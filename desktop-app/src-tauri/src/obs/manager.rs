use anyhow::{anyhow, Context, Result};
use obws::Client;
use std::path::PathBuf;
use std::time::Duration;
use tokio::sync::Mutex;

use super::types::*;

/// Manages OBS WebSocket connection and operations
pub struct OBSManager {
    client: Option<Client>,
    connected: bool,
    recording: bool,
}

impl OBSManager {
    pub fn new() -> Self {
        Self {
            client: None,
            connected: false,
            recording: false,
        }
    }

    /// Connect to OBS WebSocket server
    pub async fn connect(&mut self, host: &str, port: u16, password: Option<String>) -> Result<OBSConnectionStatus> {
        println!("Connecting to OBS WebSocket at {}:{}...", host, port);

        // Build connection URL
        let url = format!("{}:{}", host, port);

        // Connect to OBS
        let client = if let Some(pwd) = password {
            Client::connect_with_password(&url, &pwd).await
                .context("Failed to connect to OBS WebSocket with password")?
        } else {
            Client::connect(&url, None).await
                .context("Failed to connect to OBS WebSocket")?
        };

        // Get version info
        let version = client.general().version().await?;

        let status = OBSConnectionStatus {
            connected: true,
            obs_version: Some(version.obs_version.to_string()),
            websocket_version: Some(version.obs_web_socket_version.to_string()),
            available_features: vec![
                "recording".to_string(),
                "audio_sources".to_string(),
                "filters".to_string(),
                "scenes".to_string(),
            ],
        };

        self.client = Some(client);
        self.connected = true;

        println!("Successfully connected to OBS {} (WebSocket {})",
                 status.obs_version.as_ref().unwrap(),
                 status.websocket_version.as_ref().unwrap());

        Ok(status)
    }

    /// Disconnect from OBS
    pub async fn disconnect(&mut self) -> Result<()> {
        if let Some(client) = self.client.take() {
            drop(client);
        }
        self.connected = false;
        self.recording = false;
        println!("Disconnected from OBS");
        Ok(())
    }

    /// Check if connected to OBS
    pub fn is_connected(&self) -> bool {
        self.connected
    }

    /// Get list of audio input sources
    pub async fn get_audio_sources(&self) -> Result<Vec<OBSAudioSource>> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        let inputs = client.inputs().list(None).await?;

        let mut audio_sources = Vec::new();

        for input in inputs {
            // Check if this is an audio input
            if input.input_kind.contains("audio") ||
               input.input_kind.contains("capture") ||
               input.input_kind == "coreaudio_input_capture" ||
               input.input_kind == "wasapi_input_capture" {

                // Get volume and mute status
                let volume = client.inputs().volume(&input.input_name).await
                    .unwrap_or(obws::responses::inputs::Volume {
                        input_volume_db: 0.0,
                        input_volume_mul: 1.0,
                    });

                let muted = client.inputs().muted(&input.input_name).await
                    .unwrap_or(false);

                audio_sources.push(OBSAudioSource {
                    name: input.input_name.clone(),
                    uuid: None,
                    input_kind: input.input_kind.clone(),
                    volume_db: volume.input_volume_db,
                    muted,
                    monitoring_type: "None".to_string(),
                });
            }
        }

        Ok(audio_sources)
    }

    /// Start recording in OBS
    pub async fn start_recording(&mut self) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        client.recording().start().await?;
        self.recording = true;

        println!("OBS recording started");
        Ok(())
    }

    /// Stop recording in OBS and return the output file path
    pub async fn stop_recording(&mut self) -> Result<PathBuf> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        let output_path = client.recording().stop().await?;
        self.recording = false;

        println!("OBS recording stopped: {:?}", output_path);
        Ok(PathBuf::from(output_path.output_path))
    }

    /// Pause recording
    pub async fn pause_recording(&mut self) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        client.recording().pause().await?;
        println!("OBS recording paused");
        Ok(())
    }

    /// Resume recording
    pub async fn resume_recording(&mut self) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        client.recording().resume().await?;
        println!("OBS recording resumed");
        Ok(())
    }

    /// Get current recording status
    pub async fn get_recording_status(&self) -> Result<OBSRecordingStatus> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        let status = client.recording().status().await?;

        Ok(OBSRecordingStatus {
            recording: status.output_active,
            paused: status.output_paused,
            output_path: status.output_path.map(PathBuf::from),
            duration_seconds: status.output_duration.as_secs(),
            bytes: status.output_bytes,
        })
    }

    /// Apply a filter preset to an audio source
    pub async fn apply_filter_preset(&self, source_name: &str, preset: &AudioFilterPreset) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        println!("Applying '{}' preset to '{}'", preset.name, source_name);

        // Remove existing filters first
        // Note: In a production version, we might want to be more selective

        // Apply each filter in the preset
        for (index, filter_config) in preset.filters.iter().enumerate() {
            let filter_name = format!("{}_{}", filter_config.filter_type, index);

            // Create filter
            client.filters().create(obws::requests::filters::Create {
                source_name,
                filter_name: &filter_name,
                filter_kind: &filter_config.filter_type,
                filter_settings: Some(filter_config.settings.clone()),
            }).await.ok(); // Ignore errors if filter already exists

            // Enable/disable filter
            client.filters().set_enabled(source_name, &filter_name, filter_config.enabled).await?;
        }

        println!("Successfully applied '{}' preset", preset.name);
        Ok(())
    }

    /// Get available filter presets
    pub fn get_filter_presets() -> Vec<AudioFilterPreset> {
        vec![
            AudioFilterPreset::lecture_hall(),
            AudioFilterPreset::clinical_skills(),
            AudioFilterPreset::online_lecture(),
        ]
    }

    /// Set audio source volume
    pub async fn set_source_volume(&self, source_name: &str, volume_db: f32) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        client.inputs().set_volume(source_name, obws::requests::inputs::Volume::Db(volume_db)).await?;
        Ok(())
    }

    /// Mute/unmute audio source
    pub async fn set_source_muted(&self, source_name: &str, muted: bool) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Not connected to OBS"))?;

        client.inputs().set_muted(source_name, muted).await?;
        Ok(())
    }
}

impl Default for OBSManager {
    fn default() -> Self {
        Self::new()
    }
}
