use anyhow::Result;
use std::path::PathBuf;
use sysinfo::System;

use super::types::OBSInfo;

/// Detects OBS Studio installation and configuration
pub struct OBSDetector;

impl OBSDetector {
    /// Detect OBS installation and gather information
    pub fn detect() -> Result<OBSInfo> {
        let mut info = OBSInfo::default();

        // Find OBS installation path
        if let Some(path) = Self::find_obs_path() {
            info.installed = true;
            info.path = Some(path.clone());

            // Try to get OBS version
            info.version = Self::get_obs_version(&path);
        }

        // Check if OBS is currently running
        info.is_running = Self::is_obs_running();

        // If OBS is running, try to detect WebSocket
        if info.is_running {
            if let Ok(ws_info) = Self::detect_websocket() {
                info.websocket_enabled = ws_info.enabled;
                info.websocket_port = ws_info.port;
            }
        }

        Ok(info)
    }

    /// Find OBS installation path based on platform
    fn find_obs_path() -> Option<PathBuf> {
        #[cfg(target_os = "macos")]
        {
            let paths = vec![
                PathBuf::from("/Applications/OBS.app"),
                PathBuf::from("/Applications/OBS Studio.app"),
                PathBuf::from(format!("{}/Applications/OBS.app", std::env::var("HOME").unwrap_or_default())),
            ];

            paths.into_iter().find(|p| p.exists())
        }

        #[cfg(target_os = "windows")]
        {
            let paths = vec![
                PathBuf::from("C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe"),
                PathBuf::from("C:\\Program Files (x86)\\obs-studio\\bin\\64bit\\obs64.exe"),
            ];

            paths.into_iter().find(|p| p.exists())
        }

        #[cfg(target_os = "linux")]
        {
            // Check common Linux installation paths
            let paths = vec![
                PathBuf::from("/usr/bin/obs"),
                PathBuf::from("/usr/local/bin/obs"),
                PathBuf::from(format!("{}/.local/bin/obs", std::env::var("HOME").unwrap_or_default())),
            ];

            paths.into_iter().find(|p| p.exists())
        }
    }

    /// Get OBS version from the executable
    fn get_obs_version(obs_path: &PathBuf) -> Option<String> {
        #[cfg(target_os = "macos")]
        {
            // On macOS, read version from Info.plist
            let plist_path = obs_path.join("Contents/Info.plist");
            if plist_path.exists() {
                // Simple plist parsing - look for CFBundleShortVersionString
                if let Ok(contents) = std::fs::read_to_string(plist_path) {
                    if let Some(start) = contents.find("<key>CFBundleShortVersionString</key>") {
                        if let Some(version_start) = contents[start..].find("<string>") {
                            if let Some(version_end) = contents[start + version_start..].find("</string>") {
                                let version_str = &contents[start + version_start + 8..start + version_start + version_end];
                                return Some(version_str.to_string());
                            }
                        }
                    }
                }
            }
        }

        #[cfg(target_os = "windows")]
        {
            // On Windows, try to run obs64.exe --version
            if let Ok(output) = Command::new(obs_path).arg("--version").output() {
                if let Ok(version) = String::from_utf8(output.stdout) {
                    return Some(version.trim().to_string());
                }
            }
        }

        #[cfg(target_os = "linux")]
        {
            // On Linux, try to run obs --version
            if let Ok(output) = Command::new(obs_path).arg("--version").output() {
                if let Ok(version) = String::from_utf8(output.stdout) {
                    return Some(version.trim().to_string());
                }
            }
        }

        None
    }

    /// Check if OBS is currently running
    fn is_obs_running() -> bool {
        let mut system = System::new_all();
        system.refresh_all();

        #[cfg(target_os = "macos")]
        let process_names = vec!["obs", "OBS"];

        #[cfg(target_os = "windows")]
        let process_names = vec!["obs64.exe", "obs32.exe"];

        #[cfg(target_os = "linux")]
        let process_names = vec!["obs"];

        system.processes().iter().any(|(_, process)| {
            let proc_name = process.name().to_lowercase();
            process_names.iter().any(|name| proc_name.contains(&name.to_lowercase()))
        })
    }

    /// Attempt to detect WebSocket server
    fn detect_websocket() -> Result<WebSocketInfo> {
        // Try to connect to common WebSocket ports
        let ports = vec![4455, 4444]; // OBS WebSocket v5 default is 4455, v4 was 4444

        for port in ports {
            // Simple TCP connection test
            if let Ok(_) = std::net::TcpStream::connect(format!("127.0.0.1:{}", port)) {
                return Ok(WebSocketInfo {
                    enabled: true,
                    port,
                });
            }
        }

        Ok(WebSocketInfo {
            enabled: false,
            port: 4455,
        })
    }

    /// Open OBS WebSocket settings for user configuration
    pub fn open_websocket_settings() -> Result<()> {
        println!("Opening OBS WebSocket settings...");

        // Note: This would require OBS to be running and we'd need to
        // use AppleScript/AutoHotkey to navigate to Tools > WebSocket Server Settings
        // For now, we'll just provide instructions

        Ok(())
    }
}

#[derive(Debug)]
struct WebSocketInfo {
    enabled: bool,
    port: u16,
}
