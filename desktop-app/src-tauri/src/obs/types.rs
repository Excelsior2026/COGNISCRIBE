use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Information about OBS Studio installation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OBSInfo {
    pub installed: bool,
    pub version: Option<String>,
    pub path: Option<PathBuf>,
    pub websocket_enabled: bool,
    pub websocket_port: u16,
    pub is_running: bool,
}

impl Default for OBSInfo {
    fn default() -> Self {
        Self {
            installed: false,
            version: None,
            path: None,
            websocket_enabled: false,
            websocket_port: 4455,
            is_running: false,
        }
    }
}

/// OBS connection status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OBSConnectionStatus {
    pub connected: bool,
    pub obs_version: Option<String>,
    pub websocket_version: Option<String>,
    pub available_features: Vec<String>,
}

/// Audio source information from OBS
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OBSAudioSource {
    pub name: String,
    pub uuid: Option<String>,
    pub input_kind: String,
    pub volume_db: f32,
    pub muted: bool,
    pub monitoring_type: String,
}

/// OBS recording status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OBSRecordingStatus {
    pub recording: bool,
    pub paused: bool,
    pub output_path: Option<PathBuf>,
    pub duration_seconds: u64,
    pub bytes: u64,
}

/// Filter preset for audio enhancement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioFilterPreset {
    pub name: String,
    pub description: String,
    pub filters: Vec<FilterConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FilterConfig {
    pub filter_type: String,
    pub enabled: bool,
    pub settings: serde_json::Value,
}

/// Predefined filter presets for different scenarios
impl AudioFilterPreset {
    pub fn lecture_hall() -> Self {
        Self {
            name: "Lecture Hall".to_string(),
            description: "Optimized for recording in large classroom settings".to_string(),
            filters: vec![
                FilterConfig {
                    filter_type: "noise_gate".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "open_threshold": -35.0,
                        "close_threshold": -45.0,
                        "attack_time": 25,
                        "hold_time": 200,
                        "release_time": 150
                    }),
                },
                FilterConfig {
                    filter_type: "noise_suppression".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "method": "rnnoise",
                        "intensity": 0.8
                    }),
                },
                FilterConfig {
                    filter_type: "compressor".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "ratio": 4.0,
                        "threshold": -18.0,
                        "attack_time": 6,
                        "release_time": 60,
                        "output_gain": 2.0
                    }),
                },
            ],
        }
    }

    pub fn clinical_skills() -> Self {
        Self {
            name: "Clinical Skills".to_string(),
            description: "For recording practice sessions with multiple speakers".to_string(),
            filters: vec![
                FilterConfig {
                    filter_type: "noise_gate".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "open_threshold": -40.0,
                        "close_threshold": -50.0,
                        "attack_time": 15,
                        "hold_time": 150,
                        "release_time": 100
                    }),
                },
                FilterConfig {
                    filter_type: "noise_suppression".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "method": "rnnoise",
                        "intensity": 0.6
                    }),
                },
                FilterConfig {
                    filter_type: "compressor".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "ratio": 3.0,
                        "threshold": -20.0,
                        "attack_time": 10,
                        "release_time": 80,
                        "output_gain": 1.0
                    }),
                },
            ],
        }
    }

    pub fn online_lecture() -> Self {
        Self {
            name: "Online Lecture".to_string(),
            description: "For capturing Zoom/Teams lectures with system audio".to_string(),
            filters: vec![
                FilterConfig {
                    filter_type: "noise_gate".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "open_threshold": -45.0,
                        "close_threshold": -55.0,
                        "attack_time": 20,
                        "hold_time": 100,
                        "release_time": 120
                    }),
                },
                FilterConfig {
                    filter_type: "noise_suppression".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "method": "speex",
                        "intensity": 0.5
                    }),
                },
                FilterConfig {
                    filter_type: "compressor".to_string(),
                    enabled: true,
                    settings: serde_json::json!({
                        "ratio": 2.5,
                        "threshold": -22.0,
                        "attack_time": 8,
                        "release_time": 100,
                        "output_gain": 0.5
                    }),
                },
            ],
        }
    }
}
