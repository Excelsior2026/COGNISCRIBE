use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::fs;
use std::net::{SocketAddr, TcpStream};
use std::process::{Child, Command};
use std::time::Duration;
use tokio::time::sleep;

use crate::config::AppConfig;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub ollama_running: bool,
    pub api_running: bool,
    pub whisper_loaded: bool,
    pub deepfilter_available: bool,
    pub deepfilter_binary: Option<String>,
    pub deepfilter_model: Option<String>,
}

pub struct ProcessManager {
    ollama_process: Option<Child>,
    api_process: Option<Child>,
    ollama_port: u16,
    use_port_checks: bool,
    deepfilter_available: bool,
    deepfilter_binary: Option<String>,
    deepfilter_model: Option<String>,
}

fn is_child_running(child: &mut Option<Child>) -> bool {
    if let Some(process) = child {
        match process.try_wait() {
            Ok(Some(_)) => {
                *child = None;
                false
            }
            Ok(None) => true,
            Err(_) => {
                *child = None;
                false
            }
        }
    } else {
        false
    }
}

fn is_tcp_port_listening(port: u16) -> bool {
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    TcpStream::connect_timeout(&addr, Duration::from_millis(200)).is_ok()
}

fn ollama_binary_name() -> &'static str {
    if cfg!(target_os = "windows") {
        "ollama.exe"
    } else {
        "ollama"
    }
}

fn resolve_resource_base(resource_dir: &Path) -> PathBuf {
    if resource_dir.join("resources").exists() {
        resource_dir.join("resources")
    } else {
        resource_dir.to_path_buf()
    }
}

fn resolve_ollama_binary(resource_dir: &Path) -> Result<PathBuf> {
    let resource_path = resolve_resource_base(resource_dir)
        .join("ollama")
        .join(ollama_binary_name());
    if resource_path.exists() {
        return Ok(resource_path);
    }

    let app_support = dirs::data_local_dir()
        .context("Failed to get data directory")?
        .join("com.bageltech.cogniscribe")
        .join("ollama");
    let app_path = app_support.join(ollama_binary_name());
    if app_path.exists() {
        return Ok(app_path);
    }

    anyhow::bail!(
        "Ollama binary not found at {:?} or {:?}",
        resource_path,
        app_path
    );
}

impl ProcessManager {
    pub fn new() -> Self {
        Self {
            ollama_process: None,
            api_process: None,
            ollama_port: 11436,
            use_port_checks: false,
            deepfilter_available: false,
            deepfilter_binary: None,
            deepfilter_model: None,
        }
    }

    /// Start all backend services
    pub async fn start_all(&mut self, resource_dir: &Path, config: &AppConfig) -> Result<()> {
        println!("Starting backend services...");
        self.use_port_checks = true;

        // Start Ollama first
        self.start_ollama(resource_dir, config).await?;

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
    async fn start_ollama(&mut self, resource_dir: &Path, config: &AppConfig) -> Result<()> {
        println!("Starting Ollama...");

        let ollama_path = resolve_ollama_binary(resource_dir)?;

        let client = reqwest::Client::new();
        let preferred_ports: Vec<u16> = {
            let mut ports = vec![11436u16, 11434u16];
            ports.extend(11437u16..=11446u16);
            ports
        };

        for port in preferred_ports {
            if is_tcp_port_listening(port) {
                // Something is already listening: reuse it only if it behaves like a working Ollama server.
                let tags_url = format!("http://127.0.0.1:{}/api/tags", port);
                let tags_ok = match client
                    .get(&tags_url)
                    .timeout(Duration::from_secs(2))
                    .send()
                    .await
                {
                    Ok(resp) => resp.status().is_success(),
                    Err(_) => false,
                };

                if !tags_ok {
                    continue;
                }

                let generate_url = format!("http://127.0.0.1:{}/api/generate", port);
                let generate_body = serde_json::json!({
                    "model": config.ollama_model.as_str(),
                    "prompt": "healthcheck",
                    "stream": false,
                    "options": { "num_predict": 1, "temperature": 0.0 }
                });

                match client
                    .post(&generate_url)
                    .json(&generate_body)
                    .timeout(Duration::from_secs(3))
                    .send()
                    .await
                {
                    Ok(resp) if resp.status().is_success() => {
                        self.ollama_port = port;
                        self.ollama_process = None;
                        println!("Using existing Ollama on port {}", port);
                        return Ok(());
                    }
                    Ok(resp) => {
                        println!(
                            "Existing Ollama on port {} failed generate check ({}); trying another port",
                            port,
                            resp.status()
                        );
                        continue;
                    }
                    Err(err) if err.is_timeout() => {
                        // If the model is still warming up, treat the server as usable and let the UI preflight
                        // health check decide when to unblock processing.
                        self.ollama_port = port;
                        self.ollama_process = None;
                        println!(
                            "Found Ollama on port {} but generate check timed out; assuming it is starting",
                            port
                        );
                        return Ok(());
                    }
                    Err(_) => continue,
                }
            }

            // Port is free; start a bundled Ollama instance on it.
            self.ollama_port = port;

            let mut command = Command::new(&ollama_path);
            command.arg("serve").env("OLLAMA_HOST", format!("127.0.0.1:{}", port));
            if let Some(parent) = ollama_path.parent() {
                command.current_dir(parent);
            }

            let child = command.spawn().context("Failed to start Ollama")?;

            self.ollama_process = Some(child);

            // Wait for Ollama to be ready
            if let Err(err) = self.wait_for_ollama_health().await {
                // Kill the child (if we started it) and try another port.
                if let Some(mut child) = self.ollama_process.take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
                println!(
                    "Ollama failed health check on port {} ({}); trying another port",
                    port,
                    err
                );
                continue;
            }

            println!("Ollama started successfully on port {}", port);
            return Ok(());
        }

        anyhow::bail!("Failed to find an available port for Ollama")
    }

    /// Start Python FastAPI service
    async fn start_api(&mut self, resource_dir: &Path, config: &AppConfig) -> Result<()> {
        println!("Starting Python API...");

        #[cfg(target_os = "windows")]
        let exe_name = "cogniscribe-api.exe";

        #[cfg(not(target_os = "windows"))]
        let exe_name = "cogniscribe-api";

        // In production builds, resources are in a nested "resources" directory
        let api_path = if resource_dir.join("resources").exists() {
            resource_dir.join("resources").join("python-backend").join(exe_name)
        } else {
            resource_dir.join("python-backend").join(exe_name)
        };

        if !api_path.exists() {
            anyhow::bail!("Python API binary not found at {:?}", api_path);
        }

        let resource_base = if resource_dir.join("resources").exists() {
            resource_dir.join("resources")
        } else {
            resource_dir.to_path_buf()
        };

        let mut command = Command::new(&api_path);

        let audio_storage_dir = config.data_directory.clone();
        let base_data_dir = audio_storage_dir
            .parent()
            .map(PathBuf::from)
            .unwrap_or_else(|| audio_storage_dir.clone());
        let temp_audio_dir = base_data_dir.join("temp_processed");
        fs::create_dir_all(&audio_storage_dir)
            .context("Failed to create audio storage directory")?;
        fs::create_dir_all(&temp_audio_dir)
            .context("Failed to create temp audio directory")?;

        command
            .env("PORT", "8080")
            .env("OLLAMA_HOST", "localhost")
            .env("OLLAMA_PORT", self.ollama_port.to_string())
            .env("WHISPER_MODEL", &config.whisper_model)
            .env("USE_GPU", config.use_gpu.to_string())
            .env("OLLAMA_MODEL", &config.ollama_model)
            .env("AUDIO_STORAGE_DIR", &audio_storage_dir)
            .env("TEMP_AUDIO_DIR", &temp_audio_dir)
            .env(
                "CORS_ALLOW_ORIGINS",
                "http://localhost,http://127.0.0.1,http://localhost:5173,http://127.0.0.1:5173,tauri://localhost,app://localhost,http://tauri.localhost,https://tauri.localhost",
            )
            .env("LOG_LEVEL", "INFO");

        if let Some(parent) = api_path.parent() {
            command.current_dir(parent);
        }

        if let Some(df_paths) = deepfilternet_paths(&resource_base) {
            let bin_path = df_paths.bin_path.to_string_lossy().to_string();
            let model_path = df_paths.model_path.to_string_lossy().to_string();
            self.deepfilter_available = true;
            self.deepfilter_binary = df_paths
                .bin_path
                .file_name()
                .map(|name| name.to_string_lossy().to_string());
            self.deepfilter_model = df_paths
                .model_path
                .file_name()
                .map(|name| name.to_string_lossy().to_string());

            command
                .env("DEEPFILTERNET_ENABLED", "true")
                .env("DEEPFILTERNET_BIN", bin_path)
                .env("DEEPFILTERNET_MODEL", model_path)
                .env("DEEPFILTERNET_USE_POSTFILTER", "true");
        } else {
            self.deepfilter_available = false;
            self.deepfilter_binary = None;
            self.deepfilter_model = None;
        }

        let child = command
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
            let url = format!("http://127.0.0.1:{}/api/tags", self.ollama_port);
            match client
                .get(url)
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
                .get("http://127.0.0.1:8080/api/health")
                .timeout(Duration::from_secs(3))
                .send()
                .await
            {
                Ok(response)
                    if response.status() == reqwest::StatusCode::OK
                        || response.status() == reqwest::StatusCode::SERVICE_UNAVAILABLE =>
                {
                    println!("Python API is responding (attempt {})", attempt);
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
    pub fn get_status(&mut self) -> ServiceStatus {
        let ollama_running = if self.use_port_checks {
            is_child_running(&mut self.ollama_process) || is_tcp_port_listening(self.ollama_port)
        } else {
            is_child_running(&mut self.ollama_process)
        };
        let api_running = if self.use_port_checks {
            is_child_running(&mut self.api_process) || is_tcp_port_listening(8080)
        } else {
            is_child_running(&mut self.api_process)
        };
        ServiceStatus {
            ollama_running,
            api_running,
            whisper_loaded: api_running, // Simplified check
            deepfilter_available: self.deepfilter_available,
            deepfilter_binary: self.deepfilter_binary.clone(),
            deepfilter_model: self.deepfilter_model.clone(),
        }
    }
}

struct DeepFilterNetPaths {
    bin_path: std::path::PathBuf,
    model_path: std::path::PathBuf,
}

fn deepfilternet_paths(resource_base: &Path) -> Option<DeepFilterNetPaths> {
    let df_dir = resource_base.join("deepfilternet");
    if !df_dir.exists() {
        return None;
    }

    let bin_name = if cfg!(target_os = "windows") {
        "deep-filter-0.5.6-x86_64-pc-windows-msvc.exe"
    } else if cfg!(target_os = "macos") {
        if cfg!(target_arch = "aarch64") {
            "deep-filter-0.5.6-aarch64-apple-darwin"
        } else {
            "deep-filter-0.5.6-x86_64-apple-darwin"
        }
    } else {
        return None;
    };

    let bin_path = df_dir.join(bin_name);
    if !bin_path.exists() {
        return None;
    }

    let model_path = df_dir.join("DeepFilterNet3_onnx.tar.gz");
    if !model_path.exists() {
        return None;
    }

    Some(DeepFilterNetPaths { bin_path, model_path })
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_manager_creation() {
        let manager = ProcessManager::new();
        assert!(manager.ollama_process.is_none());
        assert!(manager.api_process.is_none());
    }

    #[test]
    fn test_service_status_default() {
        let mut manager = ProcessManager::new();
        let status = manager.get_status();

        assert_eq!(status.ollama_running, false);
        assert_eq!(status.api_running, false);
        assert_eq!(status.whisper_loaded, false);
        assert_eq!(status.deepfilter_available, false);
    }

    #[test]
    fn test_service_status_serialization() {
        let status = ServiceStatus {
            ollama_running: true,
            api_running: true,
            whisper_loaded: true,
            deepfilter_available: true,
            deepfilter_binary: Some("deep-filter".to_string()),
            deepfilter_model: Some("DeepFilterNet3_onnx.tar.gz".to_string()),
        };

        let json = serde_json::to_string(&status).unwrap();
        assert!(json.contains("ollama_running"));
        assert!(json.contains("true"));

        let deserialized: ServiceStatus = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.ollama_running, true);
        assert_eq!(deserialized.api_running, true);
        assert_eq!(deserialized.whisper_loaded, true);
        assert_eq!(deserialized.deepfilter_available, true);
    }
}
