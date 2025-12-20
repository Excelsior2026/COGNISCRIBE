import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface OBSAudioSource {
  name: string;
  uuid: string | null;
  input_kind: string;
  volume_db: number;
  muted: boolean;
  monitoring_type: string;
}

interface AudioFilterPreset {
  name: string;
  description: string;
  use_case: string;
}

interface OBSRecordingStatus {
  recording: boolean;
  paused: boolean;
  output_path: string | null;
  duration_seconds: number;
  bytes: number;
}

interface OBSRecordPanelProps {
  onRecordingComplete: (filePath: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

function OBSRecordPanel({ onRecordingComplete, onError, disabled }: OBSRecordPanelProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [audioSources, setAudioSources] = useState<OBSAudioSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [filterPresets, setFilterPresets] = useState<AudioFilterPreset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [recordingStatus, setRecordingStatus] = useState<OBSRecordingStatus | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  // Check OBS connection on mount
  useEffect(() => {
    checkConnection();
    loadFilterPresets();
  }, []);

  // Poll recording status while recording
  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(async () => {
        try {
          const status = await invoke<OBSRecordingStatus>('obs_get_recording_status');
          setRecordingStatus(status);
          setRecordingTime(status.duration_seconds);
          setIsPaused(status.paused);
        } catch (err) {
          console.error('Failed to get recording status:', err);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isRecording]);

  const checkConnection = async () => {
    try {
      const connected = await invoke<boolean>('obs_is_connected');
      setIsConnected(connected);

      if (connected) {
        await loadAudioSources();
      }
    } catch (err) {
      console.error('Failed to check OBS connection:', err);
      setIsConnected(false);
    }
  };

  const loadAudioSources = async () => {
    try {
      const sources = await invoke<OBSAudioSource[]>('obs_get_audio_sources');
      setAudioSources(sources);

      // Auto-select first source
      if (sources.length > 0 && !selectedSource) {
        setSelectedSource(sources[0].name);
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load audio sources');
    }
  };

  const loadFilterPresets = async () => {
    try {
      const presets = await invoke<AudioFilterPreset[]>('obs_get_filter_presets');
      setFilterPresets(presets);

      // Auto-select first preset
      if (presets.length > 0 && !selectedPreset) {
        setSelectedPreset(presets[0].name);
      }
    } catch (err) {
      console.error('Failed to load filter presets:', err);
    }
  };

  const applyFilterPreset = async () => {
    if (!selectedSource || !selectedPreset) {
      onError('Please select an audio source and filter preset');
      return;
    }

    try {
      await invoke('obs_apply_filter_preset', {
        sourceName: selectedSource,
        presetName: selectedPreset,
      });
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to apply filter preset');
    }
  };

  const handleStartRecording = async () => {
    if (!selectedSource) {
      onError('Please select an audio source first');
      return;
    }

    try {
      // Apply filter preset if selected
      if (selectedPreset) {
        await applyFilterPreset();
      }

      await invoke('obs_start_recording');
      setIsRecording(true);
      setRecordingTime(0);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to start recording');
    }
  };

  const handleStopRecording = async () => {
    try {
      const filePath = await invoke<string>('obs_stop_recording');
      setIsRecording(false);
      setIsPaused(false);
      setRecordingTime(0);
      onRecordingComplete(filePath);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to stop recording');
    }
  };

  const handlePauseRecording = async () => {
    try {
      await invoke('obs_pause_recording');
      setIsPaused(true);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to pause recording');
    }
  };

  const handleResumeRecording = async () => {
    try {
      await invoke('obs_resume_recording');
      setIsPaused(false);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to resume recording');
    }
  };

  const handleSourceVolumeChange = async (volumeDb: number) => {
    if (!selectedSource) return;

    try {
      await invoke('obs_set_source_volume', {
        sourceName: selectedSource,
        volumeDb,
      });

      // Refresh audio sources to update volume display
      await loadAudioSources();
    } catch (err) {
      console.error('Failed to set volume:', err);
    }
  };

  const handleSourceMuteToggle = async () => {
    if (!selectedSource) return;

    const source = audioSources.find((s) => s.name === selectedSource);
    if (!source) return;

    try {
      await invoke('obs_set_source_muted', {
        sourceName: selectedSource,
        muted: !source.muted,
      });

      // Refresh audio sources to update mute status
      await loadAudioSources();
    } catch (err) {
      console.error('Failed to toggle mute:', err);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatBytes = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
  };

  if (!isConnected) {
    return (
      <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-6 text-center">
        <div className="text-4xl mb-3">🔌</div>
        <h3 className="text-lg font-semibold text-purple-900 mb-2">
          OBS Not Connected
        </h3>
        <p className="text-sm text-purple-700 mb-4">
          Please complete OBS setup to use professional audio recording
        </p>
        <button
          onClick={checkConnection}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Check Connection
        </button>
      </div>
    );
  }

  const selectedSourceData = audioSources.find((s) => s.name === selectedSource);
  const selectedPresetData = filterPresets.find((p) => p.name === selectedPreset);

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="font-medium">OBS Connected - Professional Audio Ready</span>
      </div>

      {/* Audio Source Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Audio Source
        </label>
        <select
          value={selectedSource}
          onChange={(e) => setSelectedSource(e.target.value)}
          disabled={disabled || isRecording}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">Select audio source...</option>
          {audioSources.map((source) => (
            <option key={source.name} value={source.name}>
              {source.name} {source.muted ? '(Muted)' : ''}
            </option>
          ))}
        </select>
        {audioSources.length === 0 && (
          <p className="text-xs text-gray-500 mt-1">
            No audio sources found. Please configure audio in OBS.
          </p>
        )}
      </div>

      {/* Volume Control */}
      {selectedSourceData && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Volume</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {selectedSourceData.volume_db.toFixed(1)} dB
              </span>
              <button
                onClick={handleSourceMuteToggle}
                disabled={disabled || isRecording}
                className="px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {selectedSourceData.muted ? '🔇 Unmute' : '🔊 Mute'}
              </button>
            </div>
          </div>
          <input
            type="range"
            min="-40"
            max="10"
            step="1"
            value={selectedSourceData.volume_db}
            onChange={(e) => handleSourceVolumeChange(parseFloat(e.target.value))}
            disabled={disabled || isRecording}
            className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>-40 dB</span>
            <span>+10 dB</span>
          </div>
        </div>
      )}

      {/* Filter Preset Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Audio Enhancement Preset
        </label>
        <select
          value={selectedPreset}
          onChange={(e) => setSelectedPreset(e.target.value)}
          disabled={disabled || isRecording}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">No preset (manual filters)</option>
          {filterPresets.map((preset) => (
            <option key={preset.name} value={preset.name}>
              {preset.description}
            </option>
          ))}
        </select>
        {selectedPresetData && (
          <p className="text-xs text-gray-600 mt-1">
            <strong>Best for:</strong> {selectedPresetData.use_case}
          </p>
        )}
      </div>

      {/* Recording Status */}
      {isRecording && (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-semibold text-red-700">
                {isPaused ? 'PAUSED' : 'RECORDING'}
              </span>
            </div>
            <span className="text-2xl font-mono font-bold text-red-600">
              {formatTime(recordingTime)}
            </span>
          </div>
          {recordingStatus && recordingStatus.bytes > 0 && (
            <p className="text-xs text-red-600">
              File size: {formatBytes(recordingStatus.bytes)}
            </p>
          )}
        </div>
      )}

      {/* Recording Controls */}
      <div className="flex gap-3 justify-center">
        {!isRecording ? (
          <button
            onClick={handleStartRecording}
            disabled={disabled || !selectedSource}
            className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold py-3 px-6 rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            ● Start OBS Recording
          </button>
        ) : (
          <>
            {!isPaused ? (
              <button
                onClick={handlePauseRecording}
                disabled={disabled}
                className="flex-1 bg-yellow-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⏸️ Pause
              </button>
            ) : (
              <button
                onClick={handleResumeRecording}
                disabled={disabled}
                className="flex-1 bg-green-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ▶️ Resume
              </button>
            )}
            <button
              onClick={handleStopRecording}
              disabled={disabled}
              className="flex-1 bg-red-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ⏹️ Stop
            </button>
          </>
        )}
      </div>

      {/* Info */}
      {!isRecording && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-800">
            <strong>Pro Tip:</strong> Select your microphone source and an audio preset before recording.
            OBS will apply professional noise reduction, compression, and EQ filters automatically.
          </p>
        </div>
      )}
    </div>
  );
}

export default OBSRecordPanel;
