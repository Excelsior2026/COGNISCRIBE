use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    // Setup status
    pub setup_completed: bool,
    pub bundled_models_used: bool,

    // Model settings
    pub whisper_model: String,
    pub ollama_model: String,
    pub use_gpu: bool,

    // Processing defaults
    pub default_ratio: f32,
    pub default_subject: String,

    // Storage settings
    pub data_directory: PathBuf,
    pub auto_delete_days: u32,

    // UI preferences
    pub theme: String,
    pub auto_updates: bool,

    // Recording settings
    pub recording_format: String,  // "wav" or "mp3"
    pub recording_device: String,  // Device ID or empty for default
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            setup_completed: false,
            bundled_models_used: false,
            whisper_model: "base".to_string(),
            ollama_model: "llama3.1:8b".to_string(),
            use_gpu: false,
            default_ratio: 0.15,
            default_subject: String::new(),
            data_directory: get_default_data_dir(),
            auto_delete_days: 7,
            theme: "light".to_string(),
            auto_updates: true,
            recording_format: "wav".to_string(),
            recording_device: String::new(),  // Empty = default device
        }
    }
}

/// Get platform-specific config directory
pub fn get_config_dir() -> PathBuf {
    dirs::config_dir()
        .expect("Failed to get config directory")
        .join("cogniscribe")
}

/// Get default data directory for storing audio files
fn get_default_data_dir() -> PathBuf {
    dirs::data_local_dir()
        .expect("Failed to get data directory")
        .join("cogniscribe")
        .join("audio_storage")
}

/// Get config file path
fn get_config_file() -> PathBuf {
    get_config_dir().join("config.json")
}

/// Load configuration from disk
pub fn load_config() -> Result<AppConfig> {
    let config_file = get_config_file();

    if !config_file.exists() {
        // Create default config
        let config = AppConfig::default();
        save_config(&config)?;
        return Ok(config);
    }

    let contents = fs::read_to_string(&config_file)
        .context("Failed to read config file")?;

    let config: AppConfig = serde_json::from_str(&contents)
        .context("Failed to parse config file")?;

    Ok(config)
}

/// Save configuration to disk
pub fn save_config(config: &AppConfig) -> Result<()> {
    let config_dir = get_config_dir();

    // Create config directory if it doesn't exist
    fs::create_dir_all(&config_dir)
        .context("Failed to create config directory")?;

    let config_file = config_dir.join("config.json");

    let contents = serde_json::to_string_pretty(config)
        .context("Failed to serialize config")?;

    fs::write(&config_file, contents)
        .context("Failed to write config file")?;

    Ok(())
}

/// Ensure data directories exist
#[allow(dead_code)]
pub fn ensure_data_directories(config: &AppConfig) -> Result<()> {
    fs::create_dir_all(&config.data_directory)
        .context("Failed to create data directory")?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_default_config() {
        let config = AppConfig::default();

        assert_eq!(config.setup_completed, false);
        assert_eq!(config.bundled_models_used, false);
        assert_eq!(config.whisper_model, "base");
        assert_eq!(config.ollama_model, "llama3.1:8b");
        assert_eq!(config.use_gpu, false);
        assert_eq!(config.default_ratio, 0.15);
        assert_eq!(config.theme, "light");
        assert_eq!(config.auto_updates, true);
        assert_eq!(config.recording_format, "wav");
        assert_eq!(config.auto_delete_days, 7);
    }

    #[test]
    fn test_config_serialization() {
        let config = AppConfig::default();

        // Test serialization
        let json = serde_json::to_string(&config).unwrap();
        assert!(json.contains("whisper_model"));
        assert!(json.contains("base"));

        // Test deserialization
        let deserialized: AppConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.whisper_model, config.whisper_model);
        assert_eq!(deserialized.ollama_model, config.ollama_model);
    }

    #[test]
    fn test_config_save_and_load() {
        use tempfile::TempDir;

        // Create a temporary directory for testing
        let temp_dir = TempDir::new().unwrap();
        let temp_config_path = temp_dir.path().join("config.json");

        // Create a custom config
        let mut config = AppConfig::default();
        config.setup_completed = true;
        config.whisper_model = "large".to_string();
        config.default_ratio = 0.25;

        // Save to temp file
        let contents = serde_json::to_string_pretty(&config).unwrap();
        fs::write(&temp_config_path, contents).unwrap();

        // Load from temp file
        let loaded_contents = fs::read_to_string(&temp_config_path).unwrap();
        let loaded_config: AppConfig = serde_json::from_str(&loaded_contents).unwrap();

        assert_eq!(loaded_config.setup_completed, true);
        assert_eq!(loaded_config.whisper_model, "large");
        assert_eq!(loaded_config.default_ratio, 0.25);
    }

    #[test]
    fn test_config_dir_creation() {
        let config_dir = get_config_dir();
        assert!(config_dir.to_string_lossy().contains("cogniscribe"));
    }

    #[test]
    fn test_default_data_dir() {
        let data_dir = get_default_data_dir();
        assert!(data_dir.to_string_lossy().contains("cogniscribe"));
        assert!(data_dir.to_string_lossy().contains("audio_storage"));
    }
}
