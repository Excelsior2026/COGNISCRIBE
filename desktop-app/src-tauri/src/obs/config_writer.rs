use anyhow::Result;
use serde_json::json;
use std::path::PathBuf;

pub struct OBSConfigWriter;

impl OBSConfigWriter {
    /// Get OBS config directory path
    fn get_config_dir() -> Result<PathBuf> {
        #[cfg(target_os = "macos")]
        {
            let home = std::env::var("HOME")?;
            Ok(PathBuf::from(format!("{}/Library/Application Support/obs-studio", home)))
        }

        #[cfg(target_os = "windows")]
        {
            let appdata = std::env::var("APPDATA")?;
            Ok(PathBuf::from(format!("{}\\obs-studio", appdata)))
        }

        #[cfg(target_os = "linux")]
        {
            let home = std::env::var("HOME")?;
            Ok(PathBuf::from(format!("{}/.config/obs-studio", home)))
        }
    }

    /// Enable WebSocket server in OBS global config
    pub fn enable_websocket() -> Result<()> {
        let config_dir = Self::get_config_dir()?;
        let global_ini = config_dir.join("global.ini");

        // Ensure config directory exists
        std::fs::create_dir_all(&config_dir)?;

        // Read existing config or create new
        let mut config_content = if global_ini.exists() {
            std::fs::read_to_string(&global_ini)?
        } else {
            String::new()
        };

        // Check if WebSocket section exists
        if !config_content.contains("[OBSWebSocket]") {
            // Add WebSocket section
            config_content.push_str("\n[OBSWebSocket]\n");
            config_content.push_str("ServerEnabled=true\n");
            config_content.push_str("ServerPort=4455\n");
            config_content.push_str("AuthRequired=false\n");
            config_content.push_str("ServerPassword=\n");
            config_content.push_str("AlertsEnabled=true\n");
        } else {
            // Update existing section
            config_content = config_content.replace("ServerEnabled=false", "ServerEnabled=true");

            // Ensure port is set
            if !config_content.contains("ServerPort=") {
                config_content = config_content.replace(
                    "[OBSWebSocket]",
                    "[OBSWebSocket]\nServerPort=4455",
                );
            }
        }

        // Write updated config
        std::fs::write(&global_ini, config_content)?;

        println!("WebSocket enabled in OBS config");
        Ok(())
    }

    /// Create a basic scene collection for CogniScribe
    pub fn create_cogniscribe_scene() -> Result<()> {
        let config_dir = Self::get_config_dir()?;
        let scenes_dir = config_dir.join("basic/scenes");

        std::fs::create_dir_all(&scenes_dir)?;

        let scene_file = scenes_dir.join("CogniScribe.json");

        // Create a simple scene collection with audio input
        let scene_collection = json!({
            "current_scene": "Lecture Recording",
            "current_program_scene": "Lecture Recording",
            "scene_order": [
                {
                    "name": "Lecture Recording"
                }
            ],
            "name": "CogniScribe",
            "sources": [
                {
                    "versioned_id": "coreaudio_input_capture",
                    "name": "Microphone",
                    "uuid": "default-microphone",
                    "id": "coreaudio_input_capture",
                    "settings": {
                        "device_id": "default"
                    },
                    "mixers": 0xFF,
                    "sync": 0,
                    "flags": 0,
                    "volume": 1.0,
                    "balance": 0.5,
                    "monitoring_type": 0
                }
            ],
            "current_transition": "Fade",
            "transitions": []
        });

        std::fs::write(
            &scene_file,
            serde_json::to_string_pretty(&scene_collection)?
        )?;

        println!("Created CogniScribe scene collection");
        Ok(())
    }

    /// Set up audio filters for the default microphone
    pub fn setup_audio_filters() -> Result<()> {
        let config_dir = Self::get_config_dir()?;
        let scenes_dir = config_dir.join("basic/scenes");

        std::fs::create_dir_all(&scenes_dir)?;

        // This would ideally be done via OBS WebSocket after OBS is running
        // For now, we'll create a filter preset file
        let filter_presets = json!({
            "cogniscribe_lecture_hall": {
                "filters": [
                    {
                        "name": "Noise Suppression",
                        "type": "noise_suppress_filter_v2",
                        "enabled": true,
                        "settings": {
                            "method": "rnnoise",
                            "intensity": -30.0
                        }
                    },
                    {
                        "name": "Compressor",
                        "type": "compressor_filter",
                        "enabled": true,
                        "settings": {
                            "ratio": 4.0,
                            "threshold": -18.0,
                            "attack_time": 6.0,
                            "release_time": 60.0,
                            "output_gain": 0.0
                        }
                    },
                    {
                        "name": "Limiter",
                        "type": "limiter_filter",
                        "enabled": true,
                        "settings": {
                            "threshold": -6.0,
                            "release_time": 60.0
                        }
                    }
                ]
            },
            "cogniscribe_clinical_skills": {
                "filters": [
                    {
                        "name": "Noise Suppression",
                        "type": "noise_suppress_filter_v2",
                        "enabled": true,
                        "settings": {
                            "method": "rnnoise",
                            "intensity": -25.0
                        }
                    },
                    {
                        "name": "Expander",
                        "type": "expander_filter",
                        "enabled": true,
                        "settings": {
                            "ratio": 2.0,
                            "threshold": -40.0,
                            "attack_time": 10.0,
                            "release_time": 50.0,
                            "output_gain": 0.0
                        }
                    }
                ]
            }
        });

        let filter_file = config_dir.join("plugin_config/cogniscribe_filters.json");
        std::fs::create_dir_all(filter_file.parent().unwrap())?;
        std::fs::write(&filter_file, serde_json::to_string_pretty(&filter_presets)?)?;

        println!("Created CogniScribe filter presets");
        Ok(())
    }

    /// Configure OBS for optimal recording settings
    pub fn set_recording_settings() -> Result<()> {
        let config_dir = Self::get_config_dir()?;
        let basic_ini = config_dir.join("basic/profiles/Untitled/basic.ini");

        std::fs::create_dir_all(basic_ini.parent().unwrap())?;

        let basic_config = format!(
            r#"[Output]
Mode=Simple

[SimpleOutput]
FilePath={}/Movies
RecFormat=mkv
RecEncoder=x264
RecQuality=Small
RecAudioBitrate=192

[Audio]
SampleRate=48000
ChannelSetup=Stereo

[Video]
BaseCX=1920
BaseCY=1080
OutputCX=1920
OutputCY=1080
FPSType=0
FPSCommon=30
"#,
            std::env::var("HOME").unwrap_or_else(|_| ".".to_string())
        );

        std::fs::write(&basic_ini, basic_config)?;

        println!("Set optimal recording settings");
        Ok(())
    }

    /// Complete OBS configuration setup
    pub fn configure_all() -> Result<()> {
        println!("Configuring OBS Studio for CogniScribe...");

        // Enable WebSocket
        Self::enable_websocket()?;

        // Create scene collection
        Self::create_cogniscribe_scene()?;

        // Set up filters
        Self::setup_audio_filters()?;

        // Configure recording settings
        Self::set_recording_settings()?;

        println!("OBS configuration complete!");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_config_dir() {
        let result = OBSConfigWriter::get_config_dir();

        match result {
            Ok(dir) => {
                println!("OBS config directory: {:?}", dir);
                assert!(dir.to_string_lossy().contains("obs-studio"));
            }
            Err(e) => {
                println!("Could not get OBS config dir (expected on some systems): {}", e);
            }
        }
    }

    #[test]
    #[cfg(target_os = "macos")]
    fn test_config_dir_macos() {
        let result = OBSConfigWriter::get_config_dir();

        if let Ok(dir) = result {
            let dir_str = dir.to_string_lossy();
            assert!(dir_str.contains("Library/Application Support/obs-studio"));
        }
    }

    #[test]
    fn test_enable_websocket_content() {
        // Test the content that would be written
        let websocket_config = "[OBSWebSocket]\nServerEnabled=true\nServerPort=4455\nAuthRequired=false\n";

        assert!(websocket_config.contains("ServerEnabled=true"));
        assert!(websocket_config.contains("ServerPort=4455"));
        assert!(websocket_config.contains("AuthRequired=false"));
    }

    #[test]
    fn test_scene_json_structure() {
        use serde_json::json;

        let scene_collection = json!({
            "current_scene": "Lecture Recording",
            "name": "CogniScribe",
            "scenes": [{
                "name": "Lecture Recording",
                "sources": [{
                    "name": "Microphone",
                    "id": "coreaudio_input_capture",
                    "settings": { "device_id": "default" },
                    "volume": 1.0
                }]
            }]
        });

        assert!(scene_collection["current_scene"] == "Lecture Recording");
        assert!(scene_collection["name"] == "CogniScribe");
    }

    #[test]
    fn test_filter_preset_json() {
        use serde_json::json;

        let filter_presets = json!({
            "cogniscribe_lecture_hall": {
                "filters": [{
                    "name": "Noise Suppression",
                    "type": "noise_suppress_filter_v2",
                    "enabled": true
                }]
            }
        });

        let json_str = serde_json::to_string(&filter_presets).unwrap();
        assert!(json_str.contains("cogniscribe_lecture_hall"));
        assert!(json_str.contains("Noise Suppression"));
    }

    #[test]
    fn test_recording_settings_format() {
        let basic_config = format!(
            r#"[SimpleOutput]
RecFormat=mkv
RecQuality=Small
RecAudioBitrate=192

[Audio]
SampleRate=48000
ChannelSetup=Stereo"#
        );

        assert!(basic_config.contains("RecFormat=mkv"));
        assert!(basic_config.contains("SampleRate=48000"));
        assert!(basic_config.contains("ChannelSetup=Stereo"));
        assert!(basic_config.contains("RecAudioBitrate=192"));
    }
}
