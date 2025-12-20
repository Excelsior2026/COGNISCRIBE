use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::process::{Child, Command};
use std::time::Duration;
use tokio::time::sleep;

use crate::config::AppConfig;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub ollama_running: bool,
    pub api_running: bool,
    pub whisper_loaded: bool,
}

pub struct ProcessManager {
    ollama_process: Option<Child>,
    api_process: Option<Child>,
}

impl ProcessManager {
    pub fn new() -> Self {
        Self {
            ollama_process: None,
            api_process: None,
        }
    }

    /// Start all backend services
    pub async fn start_all(&mut self, resource_dir: &Path, config: &AppConfig) -> Result<()> {
        println!("Starting backend services...");

        // Start Ollama first
        self.start_ollama(resource_dir).await?;

        // Wait a bit for Ollama to initialize
        sleep(Duration::from_secs(2)).await;

        // Start Python API
        self.start_api(resource_dir, config).await?;

        // Wait for API to be healthy
        self.wait_for_api_health().await?;

        println!("All services started successfully");
        Ok(())
    }

    /// Start Ollama service
    async fn start_ollama(&mut self, resource_dir: &Path) -> Result<()> {
        println!("Starting Ollama...");

        let ollama_path = resource_dir.join("ollama").join("ollama");

        if !ollama_path.exists() {
            anyhow::bail!("Ollama binary not found at {:?}", ollama_path);
        }

        let child = Command::new(&ollama_path)
            .arg("serve")
            .env("OLLAMA_HOST", "127.0.0.1:11436")
            .spawn()
            .context("Failed to start Ollama")?;

        self.ollama_process = Some(child);

        // Wait for Ollama to be ready
        self.wait_for_ollama_health().await?;

        println!("Ollama started successfully");
        Ok(())
    }

    /// Start Python FastAPI service
    async fn start_api(&mut self, resource_dir: &Path, config: &AppConfig) -> Result<()> {
        println!("Starting Python API...");

        #[cfg(target_os = "windows")]
        let exe_name = "cliniscribe-api.exe";

        #[cfg(not(target_os = "windows"))]
        let exe_name = "cliniscribe-api";

        let api_path = resource_dir
            .join("python-backend")
            .join(exe_name);

        if !api_path.exists() {
            anyhow::bail!("Python API binary not found at {:?}", api_path);
        }

        let child = Command::new(&api_path)
            .env("PORT", "8080")
            .env("OLLAMA_HOST", "localhost")
            .env("OLLAMA_PORT", "11436")
            .env("WHISPER_MODEL", &config.whisper_model)
            .env("USE_GPU", config.use_gpu.to_string())
            .env("OLLAMA_MODEL", &config.ollama_model)
            .env("LOG_LEVEL", "INFO")
            .spawn()
            .context("Failed to start Python API")?;

        self.api_process = Some(child);

        println!("Python API started");
        Ok(())
    }

    /// Wait for Ollama to be healthy
    async fn wait_for_ollama_health(&self) -> Result<()> {
        let client = reqwest::Client::new();
        let max_attempts = 30; // 30 seconds total

        for attempt in 1..=max_attempts {
            match client
                .get("http://localhost:11436/api/tags")
                .timeout(Duration::from_secs(2))
                .send()
                .await
            {
                Ok(response) if response.status().is_success() => {
                    println!("Ollama is healthy (attempt {})", attempt);
                    return Ok(());
                }
                _ => {
                    if attempt < max_attempts {
                        sleep(Duration::from_secs(1)).await;
                    }
                }
            }
        }

        anyhow::bail!("Ollama failed to become healthy after {} seconds", max_attempts)
    }

    /// Wait for Python API to be healthy
    async fn wait_for_api_health(&self) -> Result<()> {
        let client = reqwest::Client::new();
        let max_attempts = 60; // 60 seconds total (Whisper model loading can be slow)

        for attempt in 1..=max_attempts {
            match client
                .get("http://localhost:8080/api/health")
                .timeout(Duration::from_secs(3))
                .send()
                .await
            {
                Ok(response) if response.status().is_success() => {
                    println!("Python API is healthy (attempt {})", attempt);
                    return Ok(());
                }
                _ => {
                    if attempt < max_attempts {
                        sleep(Duration::from_secs(1)).await;
                    }
                }
            }
        }

        anyhow::bail!("Python API failed to become healthy after {} seconds", max_attempts)
    }

    /// Stop all services gracefully
    pub async fn stop_all(&mut self) -> Result<()> {
        println!("Stopping backend services...");

        // Stop API first
        if let Some(mut child) = self.api_process.take() {
            let _ = child.kill();
            let _ = child.wait();
            println!("Python API stopped");
        }

        // Stop Ollama
        if let Some(mut child) = self.ollama_process.take() {
            let _ = child.kill();
            let _ = child.wait();
            println!("Ollama stopped");
        }

        println!("All services stopped");
        Ok(())
    }

    /// Get current service status
    pub fn get_status(&self) -> ServiceStatus {
        ServiceStatus {
            ollama_running: self.ollama_process.is_some(),
            api_running: self.api_process.is_some(),
            whisper_loaded: self.api_process.is_some(), // Simplified check
        }
    }
}

impl Drop for ProcessManager {
    fn drop(&mut self) {
        // Ensure processes are killed when manager is dropped
        if let Some(mut child) = self.api_process.take() {
            let _ = child.kill();
        }
        if let Some(mut child) = self.ollama_process.take() {
            let _ = child.kill();
        }
    }
}
