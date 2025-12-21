use anyhow::{anyhow, Result};
use std::path::PathBuf;
use std::process::Command;

/// OBS Studio download URLs
const OBS_MACOS_ARM_URL: &str = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-30.2.2-macOS-Apple.dmg";
const OBS_MACOS_INTEL_URL: &str = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-30.2.2-macOS-Intel.dmg";
const OBS_WINDOWS_URL: &str = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-30.2.2-Windows-Installer.exe";

#[derive(Debug, serde::Serialize, serde::Deserialize, Clone)]
pub struct OBSInstallProgress {
    pub stage: String,
    pub progress: f32,
    pub message: String,
}

pub struct OBSInstaller;

impl OBSInstaller {
    /// Get the appropriate download URL for the current platform
    pub fn get_download_url() -> Result<String> {
        #[cfg(target_os = "macos")]
        {
            // Detect Apple Silicon vs Intel
            let output = Command::new("uname")
                .arg("-m")
                .output()
                .map_err(|e| anyhow!("Failed to detect architecture: {}", e))?;

            let arch = String::from_utf8_lossy(&output.stdout);

            if arch.trim() == "arm64" {
                Ok(OBS_MACOS_ARM_URL.to_string())
            } else {
                Ok(OBS_MACOS_INTEL_URL.to_string())
            }
        }

        #[cfg(target_os = "windows")]
        {
            Ok(OBS_WINDOWS_URL.to_string())
        }

        #[cfg(target_os = "linux")]
        {
            Err(anyhow!("Linux users should install OBS via package manager: sudo apt install obs-studio"))
        }
    }

    /// Download OBS installer
    pub async fn download_installer<F>(
        download_path: &PathBuf,
        progress_callback: F,
    ) -> Result<PathBuf>
    where
        F: Fn(OBSInstallProgress) + Send + Sync + 'static,
    {
        let url = Self::get_download_url()?;

        progress_callback(OBSInstallProgress {
            stage: "downloading".to_string(),
            progress: 0.0,
            message: "Starting OBS Studio download...".to_string(),
        });

        // Create downloads directory if it doesn't exist
        std::fs::create_dir_all(download_path)?;

        // Determine file extension based on platform
        #[cfg(target_os = "macos")]
        let filename = "OBS-Studio.dmg";

        #[cfg(target_os = "windows")]
        let filename = "OBS-Studio-Installer.exe";

        let file_path = download_path.join(filename);

        // Download the file
        let client = reqwest::Client::new();
        let mut response = client.get(&url).send().await?;

        let total_size = response.content_length().unwrap_or(0);
        let mut downloaded: u64 = 0;
        let mut file = std::fs::File::create(&file_path)?;

        while let Some(chunk) = response.chunk().await? {
            use std::io::Write;
            file.write_all(&chunk)?;

            downloaded += chunk.len() as u64;
            let progress = if total_size > 0 {
                (downloaded as f32 / total_size as f32) * 100.0
            } else {
                0.0
            };

            progress_callback(OBSInstallProgress {
                stage: "downloading".to_string(),
                progress,
                message: format!("Downloaded {} MB / {} MB",
                    downloaded / 1_000_000,
                    total_size / 1_000_000),
            });
        }

        progress_callback(OBSInstallProgress {
            stage: "downloaded".to_string(),
            progress: 100.0,
            message: "Download complete!".to_string(),
        });

        Ok(file_path)
    }

    /// Install OBS on macOS
    #[cfg(target_os = "macos")]
    pub async fn install_macos(dmg_path: &PathBuf) -> Result<()> {
        println!("Installing OBS from DMG: {:?}", dmg_path);

        // Mount the DMG
        let mount_output = Command::new("hdiutil")
            .args(&["attach", "-nobrowse"])
            .arg(dmg_path)
            .output()?;

        if !mount_output.status.success() {
            return Err(anyhow!("Failed to mount DMG"));
        }

        let mount_info = String::from_utf8_lossy(&mount_output.stdout);

        // Extract mount point (usually /Volumes/OBS-Studio-...)
        let mount_point = mount_info
            .lines()
            .find(|line| line.contains("/Volumes/"))
            .and_then(|line| line.split_whitespace().last())
            .ok_or_else(|| anyhow!("Could not find mount point"))?;

        println!("DMG mounted at: {}", mount_point);

        // Copy OBS.app to /Applications
        let obs_source = format!("{}/OBS.app", mount_point);
        let obs_dest = "/Applications/OBS.app";

        // Use AppleScript to copy with admin privileges
        let copy_result = Command::new("osascript")
            .arg("-e")
            .arg(format!(
                "do shell script \"cp -R '{}' '{}'\" with administrator privileges",
                obs_source, obs_dest
            ))
            .output()?;

        // Unmount the DMG
        let _ = Command::new("hdiutil")
            .args(&["detach"])
            .arg(mount_point)
            .output();

        if !copy_result.status.success() {
            return Err(anyhow!("Failed to copy OBS to Applications. Error: {}",
                String::from_utf8_lossy(&copy_result.stderr)));
        }

        // Remove quarantine attribute
        let _ = Command::new("xattr")
            .args(&["-r", "-d", "com.apple.quarantine"])
            .arg(obs_dest)
            .output();

        println!("OBS Studio installed successfully!");
        Ok(())
    }

    /// Install OBS on Windows
    #[cfg(target_os = "windows")]
    pub async fn install_windows(installer_path: &PathBuf) -> Result<()> {
        println!("Installing OBS from installer: {:?}", installer_path);

        // Run installer silently
        let output = Command::new(installer_path)
            .args(&["/S"])
            .output()?;

        if !output.status.success() {
            return Err(anyhow!("Installation failed"));
        }

        println!("OBS Studio installed successfully!");
        Ok(())
    }

    /// Launch OBS Studio
    pub fn launch_obs() -> Result<()> {
        #[cfg(target_os = "macos")]
        {
            Command::new("open")
                .args(&["-a", "OBS"])
                .spawn()?;
        }

        #[cfg(target_os = "windows")]
        {
            Command::new("C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe")
                .spawn()?;
        }

        Ok(())
    }

    /// Complete installation workflow
    pub async fn install_and_configure<F>(
        download_path: &PathBuf,
        progress_callback: F,
    ) -> Result<()>
    where
        F: Fn(OBSInstallProgress) + Send + Sync + 'static + Clone,
    {
        // Step 1: Download
        let cb = progress_callback.clone();
        let installer_path = Self::download_installer(download_path, cb).await?;

        // Step 2: Install
        progress_callback(OBSInstallProgress {
            stage: "installing".to_string(),
            progress: 0.0,
            message: "Installing OBS Studio...".to_string(),
        });

        #[cfg(target_os = "macos")]
        Self::install_macos(&installer_path).await?;

        #[cfg(target_os = "windows")]
        Self::install_windows(&installer_path).await?;

        progress_callback(OBSInstallProgress {
            stage: "installed".to_string(),
            progress: 100.0,
            message: "OBS Studio installed successfully!".to_string(),
        });

        // Step 3: Clean up installer
        let _ = std::fs::remove_file(&installer_path);

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(target_os = "macos")]
    fn test_get_download_url_macos() {
        let result = OBSInstaller::get_download_url();
        assert!(result.is_ok());

        let url = result.unwrap();
        assert!(url.contains("https://"));
        assert!(url.contains("obs-studio"));
        assert!(url.contains(".dmg"));

        // Check for Apple or Intel specific naming
        assert!(url.contains("Apple") || url.contains("Intel"));
    }

    #[test]
    #[cfg(target_os = "windows")]
    fn test_get_download_url_windows() {
        let result = OBSInstaller::get_download_url();
        assert!(result.is_ok());

        let url = result.unwrap();
        assert!(url.contains("https://"));
        assert!(url.contains("obs-studio"));
        assert!(url.contains(".exe"));
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn test_get_download_url_linux_error() {
        let result = OBSInstaller::get_download_url();
        assert!(result.is_err());
    }

    #[test]
    fn test_launch_obs_path() {
        // Just verify the function exists and returns a Result
        let result = OBSInstaller::launch_obs();

        // It will fail if OBS isn't installed, but shouldn't panic
        match result {
            Ok(_) => println!("OBS launched successfully"),
            Err(e) => println!("OBS launch failed (expected if not installed): {}", e),
        }
    }

    #[test]
    fn test_obs_install_progress_creation() {
        let progress = OBSInstallProgress {
            stage: "downloading".to_string(),
            progress: 50.0,
            message: "Downloading...".to_string(),
        };

        assert_eq!(progress.stage, "downloading");
        assert_eq!(progress.progress, 50.0);
        assert_eq!(progress.message, "Downloading...");
    }

    #[test]
    fn test_obs_install_progress_serialization() {
        let progress = OBSInstallProgress {
            stage: "installed".to_string(),
            progress: 100.0,
            message: "Complete!".to_string(),
        };

        let json = serde_json::to_string(&progress).unwrap();
        assert!(json.contains("installed"));
        assert!(json.contains("100"));

        let deserialized: OBSInstallProgress = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.stage, "installed");
        assert_eq!(deserialized.progress, 100.0);
    }

    #[test]
    #[cfg(target_os = "macos")]
    fn test_macos_architecture_detection() {
        // This tests that we can detect the architecture
        use std::process::Command;

        let output = Command::new("uname")
            .arg("-m")
            .output()
            .expect("Failed to run uname");

        let arch = String::from_utf8_lossy(&output.stdout);
        println!("Detected architecture: {}", arch.trim());

        // Should be either arm64 or x86_64
        assert!(arch.contains("arm64") || arch.contains("x86_64"));
    }
}
