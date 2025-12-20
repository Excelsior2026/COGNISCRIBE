use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadProgress {
    pub model_name: String,
    pub status: String, // "downloading" | "complete" | "error"
    pub percent: f32,
    pub downloaded_bytes: u64,
    pub total_bytes: u64,
    pub message: String,
}

/// Download Whisper model
pub async fn download_whisper_model<F>(
    _resource_dir: &Path,
    progress_callback: F,
) -> Result<()>
where
    F: Fn(DownloadProgress),
{
    println!("Downloading Whisper model...");

    // Whisper models are auto-downloaded by faster-whisper on first use
    // We just need to ensure the Python backend can access the internet
    // and has proper permissions

    progress_callback(DownloadProgress {
        model_name: "whisper-base".to_string(),
        status: "downloading".to_string(),
        percent: 0.0,
        downloaded_bytes: 0,
        total_bytes: 150_000_000, // ~150MB for base model
        message: "Whisper model will auto-download on first use".to_string(),
    });

    // Simulate progress for UX (actual download happens in Python)
    progress_callback(DownloadProgress {
        model_name: "whisper-base".to_string(),
        status: "complete".to_string(),
        percent: 100.0,
        downloaded_bytes: 150_000_000,
        total_bytes: 150_000_000,
        message: "Whisper model ready".to_string(),
    });

    println!("Whisper model download prepared");
    Ok(())
}

/// Download Ollama model using Ollama API
pub async fn download_ollama_model<F>(progress_callback: F) -> Result<()>
where
    F: Fn(DownloadProgress),
{
    println!("Downloading Ollama model: llama3.1:8b");

    let client = reqwest::Client::new();

    progress_callback(DownloadProgress {
        model_name: "llama3.1:8b".to_string(),
        status: "downloading".to_string(),
        percent: 0.0,
        downloaded_bytes: 0,
        total_bytes: 4_700_000_000, // ~4.7GB
        message: "Starting download...".to_string(),
    });

    // Use Ollama's pull API
    let request_body = serde_json::json!({
        "name": "llama3.1:8b",
        "stream": true
    });

    let mut response = client
        .post("http://localhost:11436/api/pull")
        .json(&request_body)
        .send()
        .await
        .context("Failed to start Ollama model download")?;

    let mut total_downloaded: u64 = 0;
    let total_size: u64 = 4_700_000_000; // Approximate

    while let Some(chunk) = response.chunk().await.context("Download interrupted")? {
        // Parse progress from Ollama's response
        if let Ok(text) = std::str::from_utf8(&chunk) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(text) {
                if let Some(completed) = json.get("completed").and_then(|v| v.as_u64()) {
                    total_downloaded = completed;
                }

                if let Some(total) = json.get("total").and_then(|v| v.as_u64()) {
                    let percent = (total_downloaded as f64 / total as f64 * 100.0) as f32;

                    progress_callback(DownloadProgress {
                        model_name: "llama3.1:8b".to_string(),
                        status: "downloading".to_string(),
                        percent,
                        downloaded_bytes: total_downloaded,
                        total_bytes: total,
                        message: format!(
                            "Downloading: {:.1} GB / {:.1} GB",
                            total_downloaded as f64 / 1_000_000_000.0,
                            total as f64 / 1_000_000_000.0
                        ),
                    });
                }

                if let Some(status) = json.get("status").and_then(|v| v.as_str()) {
                    if status == "success" {
                        progress_callback(DownloadProgress {
                            model_name: "llama3.1:8b".to_string(),
                            status: "complete".to_string(),
                            percent: 100.0,
                            downloaded_bytes: total_size,
                            total_bytes: total_size,
                            message: "Download complete!".to_string(),
                        });
                        break;
                    }
                }
            }
        }
    }

    println!("Ollama model download complete");
    Ok(())
}

/// Check if a model is already downloaded
pub async fn is_model_downloaded(model_name: &str) -> Result<bool> {
    let client = reqwest::Client::new();

    let response = client
        .get("http://localhost:11436/api/tags")
        .send()
        .await
        .context("Failed to check Ollama models")?;

    let models: serde_json::Value = response
        .json()
        .await
        .context("Failed to parse Ollama models response")?;

    if let Some(models_array) = models.get("models").and_then(|v| v.as_array()) {
        for model in models_array {
            if let Some(name) = model.get("name").and_then(|v| v.as_str()) {
                if name.contains(model_name) {
                    return Ok(true);
                }
            }
        }
    }

    Ok(false)
}

/// Check if bundled models were installed by the installer
pub fn are_bundled_models_installed() -> Result<bool> {
    let app_support = dirs::data_local_dir()
        .context("Failed to get data directory")?
        .join("com.cliniscribe.app");

    let marker_file = app_support.join(".models-installed");
    Ok(marker_file.exists())
}
