use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::SampleFormat;
use crossbeam_channel::{bounded, Receiver, RecvTimeoutError, Sender};
use hound::{SampleFormat as WavSampleFormat, WavSpec, WavWriter};

use super::AudioPipeline;

enum RecorderCommand {
    Start { resp: Sender<Result<PathBuf>> },
    Stop { resp: Sender<Result<PathBuf>> },
    Pause { resp: Sender<Result<()>> },
    Resume { resp: Sender<Result<()>> },
    IsRecording { resp: Sender<bool> },
}

#[derive(Clone)]
pub struct NativeRecorderController {
    command_tx: Sender<RecorderCommand>,
}

impl NativeRecorderController {
    pub fn new() -> Self {
        let (command_tx, command_rx) = bounded(8);
        spawn_recorder_thread(command_rx);
        Self { command_tx }
    }

    pub fn start(&self) -> Result<PathBuf> {
        let (resp_tx, resp_rx) = bounded(1);
        self.command_tx
            .send(RecorderCommand::Start { resp: resp_tx })
            .map_err(|_| anyhow!("Recorder thread unavailable"))?;
        resp_rx
            .recv()
            .map_err(|_| anyhow!("Recorder response channel closed"))?
    }

    pub fn stop(&self) -> Result<PathBuf> {
        let (resp_tx, resp_rx) = bounded(1);
        self.command_tx
            .send(RecorderCommand::Stop { resp: resp_tx })
            .map_err(|_| anyhow!("Recorder thread unavailable"))?;
        resp_rx
            .recv()
            .map_err(|_| anyhow!("Recorder response channel closed"))?
    }

    pub fn pause(&self) -> Result<()> {
        let (resp_tx, resp_rx) = bounded(1);
        self.command_tx
            .send(RecorderCommand::Pause { resp: resp_tx })
            .map_err(|_| anyhow!("Recorder thread unavailable"))?;
        resp_rx
            .recv()
            .map_err(|_| anyhow!("Recorder response channel closed"))?
    }

    pub fn resume(&self) -> Result<()> {
        let (resp_tx, resp_rx) = bounded(1);
        self.command_tx
            .send(RecorderCommand::Resume { resp: resp_tx })
            .map_err(|_| anyhow!("Recorder thread unavailable"))?;
        resp_rx
            .recv()
            .map_err(|_| anyhow!("Recorder response channel closed"))?
    }

    pub fn is_recording(&self) -> Result<bool> {
        let (resp_tx, resp_rx) = bounded(1);
        self.command_tx
            .send(RecorderCommand::IsRecording { resp: resp_tx })
            .map_err(|_| anyhow!("Recorder thread unavailable"))?;
        resp_rx
            .recv()
            .map_err(|_| anyhow!("Recorder response channel closed"))
    }
}

struct NativeRecorder {
    stream: Option<cpal::Stream>,
    writer_handle: Option<thread::JoinHandle<Result<()>>>,
    stop_flag: Arc<AtomicBool>,
    pause_flag: Arc<AtomicBool>,
    output_path: Option<PathBuf>,
    recording: bool,
}

impl NativeRecorder {
    fn new() -> Self {
        Self {
            stream: None,
            writer_handle: None,
            stop_flag: Arc::new(AtomicBool::new(false)),
            pause_flag: Arc::new(AtomicBool::new(false)),
            output_path: None,
            recording: false,
        }
    }

    fn is_recording(&self) -> bool {
        self.recording
    }

    fn start(&mut self) -> Result<PathBuf> {
        if self.recording {
            anyhow::bail!("Recording already in progress");
        }

        let output_dir = default_recordings_dir()?;
        std::fs::create_dir_all(&output_dir)
            .context("Failed to create recordings directory")?;

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .context("Failed to read system time")?
            .as_secs();
        let output_path = output_dir.join(format!("cogniscribe-recording-{}.wav", timestamp));

        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .context("No audio input device available")?;

        let default_config = device
            .default_input_config()
            .context("Failed to read default input config")?;

        let sample_format = default_config.sample_format();
        let sample_rate = default_config.sample_rate().0;
        let channels = default_config.channels() as usize;
        let config: cpal::StreamConfig = default_config.into();

        let (sender, receiver) = bounded::<i16>(sample_rate as usize);
        let stop_flag = Arc::new(AtomicBool::new(false));
        let pause_flag = Arc::new(AtomicBool::new(false));

        let writer_stop = stop_flag.clone();
        let writer_handle = spawn_writer_thread(
            receiver,
            output_path.clone(),
            sample_rate,
            writer_stop,
        );

        let pause_flag_stream = pause_flag.clone();
        let sender_stream = sender.clone();

        let err_fn = |err| eprintln!("Audio stream error: {}", err);

        let mut pipeline = AudioPipeline::new();

        let stream = match sample_format {
            SampleFormat::F32 => device.build_input_stream(
                &config,
                move |data: &[f32], _| {
                    write_input_data_f32(
                        data,
                        channels,
                        &sender_stream,
                        &pause_flag_stream,
                        &mut pipeline,
                    )
                },
                err_fn,
                None,
            )?,
            SampleFormat::I16 => device.build_input_stream(
                &config,
                move |data: &[i16], _| {
                    write_input_data_i16(
                        data,
                        channels,
                        &sender_stream,
                        &pause_flag_stream,
                        &mut pipeline,
                    )
                },
                err_fn,
                None,
            )?,
            SampleFormat::U16 => device.build_input_stream(
                &config,
                move |data: &[u16], _| {
                    write_input_data_u16(
                        data,
                        channels,
                        &sender_stream,
                        &pause_flag_stream,
                        &mut pipeline,
                    )
                },
                err_fn,
                None,
            )?,
            _ => anyhow::bail!("Unsupported audio sample format"),
        };

        stream.play().context("Failed to start audio stream")?;

        self.stream = Some(stream);
        self.writer_handle = Some(writer_handle);
        self.stop_flag = stop_flag;
        self.pause_flag = pause_flag;
        self.output_path = Some(output_path.clone());
        self.recording = true;

        Ok(output_path)
    }

    fn stop(&mut self) -> Result<PathBuf> {
        if !self.recording {
            anyhow::bail!("No recording in progress");
        }

        self.stop_flag.store(true, Ordering::SeqCst);

        // Drop the stream to stop callbacks
        self.stream.take();

        if let Some(handle) = self.writer_handle.take() {
            handle
                .join()
                .map_err(|_| anyhow::anyhow!("Failed to join writer thread"))??;
        }

        self.recording = false;
        self.pause_flag.store(false, Ordering::SeqCst);

        self.output_path
            .clone()
            .context("Missing output path for recording")
    }

    fn pause(&mut self) -> Result<()> {
        if !self.recording {
            anyhow::bail!("No recording in progress");
        }
        self.pause_flag.store(true, Ordering::SeqCst);
        Ok(())
    }

    fn resume(&mut self) -> Result<()> {
        if !self.recording {
            anyhow::bail!("No recording in progress");
        }
        self.pause_flag.store(false, Ordering::SeqCst);
        Ok(())
    }
}

fn spawn_recorder_thread(command_rx: Receiver<RecorderCommand>) {
    thread::spawn(move || {
        let mut recorder = NativeRecorder::new();
        while let Ok(command) = command_rx.recv() {
            match command {
                RecorderCommand::Start { resp } => {
                    let _ = resp.send(recorder.start());
                }
                RecorderCommand::Stop { resp } => {
                    let _ = resp.send(recorder.stop());
                }
                RecorderCommand::Pause { resp } => {
                    let _ = resp.send(recorder.pause());
                }
                RecorderCommand::Resume { resp } => {
                    let _ = resp.send(recorder.resume());
                }
                RecorderCommand::IsRecording { resp } => {
                    let _ = resp.send(recorder.is_recording());
                }
            }
        }
    });
}

fn write_input_data_f32(
    input: &[f32],
    channels: usize,
    sender: &crossbeam_channel::Sender<i16>,
    pause_flag: &AtomicBool,
    pipeline: &mut AudioPipeline,
) {
    if pause_flag.load(Ordering::SeqCst) {
        return;
    }

    for frame in input.chunks(channels) {
        let mut sum = 0.0f32;
        for sample in frame {
            sum += *sample;
        }
        let mono = sum / channels as f32;
        push_sample(mono, sender, pipeline);
    }
}

fn write_input_data_i16(
    input: &[i16],
    channels: usize,
    sender: &crossbeam_channel::Sender<i16>,
    pause_flag: &AtomicBool,
    pipeline: &mut AudioPipeline,
) {
    if pause_flag.load(Ordering::SeqCst) {
        return;
    }

    let scale = i16::MAX as f32;
    for frame in input.chunks(channels) {
        let mut sum = 0.0f32;
        for sample in frame {
            sum += *sample as f32 / scale;
        }
        let mono = sum / channels as f32;
        push_sample(mono, sender, pipeline);
    }
}

fn write_input_data_u16(
    input: &[u16],
    channels: usize,
    sender: &crossbeam_channel::Sender<i16>,
    pause_flag: &AtomicBool,
    pipeline: &mut AudioPipeline,
) {
    if pause_flag.load(Ordering::SeqCst) {
        return;
    }

    let scale = u16::MAX as f32;
    for frame in input.chunks(channels) {
        let mut sum = 0.0f32;
        for sample in frame {
            let normalized = (*sample as f32 / scale) * 2.0 - 1.0;
            sum += normalized;
        }
        let mono = sum / channels as f32;
        push_sample(mono, sender, pipeline);
    }
}

fn push_sample(
    mono: f32,
    sender: &crossbeam_channel::Sender<i16>,
    pipeline: &mut AudioPipeline,
) {
    let processed = pipeline.process_sample(mono).clamp(-1.0, 1.0);
    let scaled = (processed * i16::MAX as f32) as i16;
    let _ = sender.try_send(scaled);
}

fn spawn_writer_thread(
    receiver: crossbeam_channel::Receiver<i16>,
    output_path: PathBuf,
    sample_rate: u32,
    stop_flag: Arc<AtomicBool>,
) -> thread::JoinHandle<Result<()>> {
    thread::spawn(move || {
        let spec = WavSpec {
            channels: 1,
            sample_rate,
            bits_per_sample: 16,
            sample_format: WavSampleFormat::Int,
        };

        let mut writer = WavWriter::create(&output_path, spec)
            .context("Failed to create WAV output file")?;

        loop {
            if stop_flag.load(Ordering::SeqCst) && receiver.is_empty() {
                break;
            }

            match receiver.recv_timeout(Duration::from_millis(200)) {
                Ok(sample) => {
                    writer
                        .write_sample(sample)
                        .context("Failed to write audio sample")?;
                }
                Err(RecvTimeoutError::Timeout) => {
                    if stop_flag.load(Ordering::SeqCst) {
                        break;
                    }
                }
                Err(RecvTimeoutError::Disconnected) => break,
            }
        }

        writer.finalize().context("Failed to finalize WAV file")?;
        Ok(())
    })
}

fn default_recordings_dir() -> Result<PathBuf> {
    let base_dir = dirs::data_local_dir()
        .context("Failed to resolve data directory")?
        .join("cogniscribe");

    Ok(base_dir.join("recordings"))
}
