// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod process_manager;
mod config;
mod model_downloader;
mod obs;
mod audio;

use tokio::sync::Mutex;
use tauri::{Manager, State};
use process_manager::{ProcessManager, ServiceStatus};
use config::{AppConfig, load_config, save_config};
use model_downloader::{download_whisper_model, download_ollama_model, DownloadProgress, are_bundled_models_installed};
use obs::{OBSDetector, OBSManager, OBSInfo, OBSConnectionStatus, OBSAudioSource, OBSRecordingStatus, AudioFilterPreset};
use audio::NativeRecorderController;

// Application state
struct AppState {
    process_manager: Mutex<ProcessManager>,
    config: Mutex<AppConfig>,
    obs_manager: Mutex<OBSManager>,
    native_recorder: NativeRecorderController,
}

/// Check if this is the first run of the application
#[tauri::command]
async fn is_first_run(state: State<'_, AppState>) -> Result<bool, String> {
    let config = state.config.lock().await;
    Ok(!config.setup_completed)
}

/// Mark setup as completed
#[tauri::command]
async fn complete_setup(state: State<'_, AppState>) -> Result<(), String> {
    let mut config = state.config.lock().await;
    config.setup_completed = true;
    save_config(&config).map_err(|e| e.to_string())?;
    Ok(())
}

/// Get current application configuration
#[tauri::command]
async fn get_config(state: State<'_, AppState>) -> Result<AppConfig, String> {
    let config = state.config.lock().await;
    Ok(config.clone())
}

/// Update application configuration
#[tauri::command]
async fn update_config(
    state: State<'_, AppState>,
    new_config: AppConfig
) -> Result<(), String> {
    let mut config = state.config.lock().await;
    *config = new_config;
    save_config(&config).map_err(|e| e.to_string())?;
    Ok(())
}

/// Start backend services (Ollama + Python API)
#[tauri::command]
async fn start_services(
    state: State<'_, AppState>,
    app_handle: tauri::AppHandle
) -> Result<(), String> {
    let config = state.config.lock().await.clone();

    // Get resource directory path
    let resource_dir = app_handle
        .path_resolver()
        .resource_dir()
        .ok_or("Failed to get resource directory")?;

    // Now we can hold the lock across await with tokio::sync::Mutex
    let mut manager = state.process_manager.lock().await;
    manager.start_all(&resource_dir, &config)
        .await
        .map_err(|e| e.to_string())?;

    Ok(())
}

/// Stop backend services
#[tauri::command]
async fn stop_services(state: State<'_, AppState>) -> Result<(), String> {
    let mut manager = state.process_manager.lock().await;
    manager.stop_all().await.map_err(|e| e.to_string())?;
    Ok(())
}

/// Get status of all services
#[tauri::command]
async fn get_service_status(state: State<'_, AppState>) -> Result<ServiceStatus, String> {
    let manager = state.process_manager.lock().await;
    Ok(manager.get_status())
}

/// Download a model with progress tracking
#[tauri::command]
async fn download_model(
    model_type: String,
    app_handle: tauri::AppHandle
) -> Result<(), String> {
    let resource_dir = app_handle
        .path_resolver()
        .resource_dir()
        .ok_or("Failed to get resource directory")?;

    let progress_callback = |progress: DownloadProgress| {
        let _ = app_handle.emit_all("download-progress", progress);
    };

    match model_type.as_str() {
        "whisper" => {
            download_whisper_model(&resource_dir, progress_callback)
                .await
                .map_err(|e| e.to_string())?;
        }
        "llama" => {
            download_ollama_model(progress_callback)
                .await
                .map_err(|e| e.to_string())?;
        }
        _ => return Err(format!("Unknown model type: {}", model_type)),
    }

    Ok(())
}

/// Check backend health
#[tauri::command]
async fn check_backend_health() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();

    let response = client
        .get("http://localhost:8080/api/health")
        .send()
        .await
        .map_err(|e| format!("Health check failed: {}", e))?;

    let health = response
        .json::<serde_json::Value>()
        .await
        .map_err(|e| format!("Failed to parse health response: {}", e))?;

    Ok(health)
}

/// Check if bundled models were installed by the installer
#[tauri::command]
fn check_bundled_models() -> Result<bool, String> {
    are_bundled_models_installed().map_err(|e| e.to_string())
}

/// Save recorded audio data to a file
#[tauri::command]
async fn save_recorded_audio(path: String, audio_data: Vec<u8>) -> Result<(), String> {
    use std::fs;

    fs::write(&path, audio_data)
        .map_err(|e| format!("Failed to save recording: {}", e))?;

    Ok(())
}

// ==================== In-App Recording Commands ====================

/// Start native in-app recording (studio pipeline).
#[tauri::command]
fn native_start_recording(state: State<'_, AppState>) -> Result<String, String> {
    state
        .native_recorder
        .start()
        .map(|path| path.to_string_lossy().to_string())
        .map_err(|e| e.to_string())
}

/// Stop native in-app recording and return the output file path.
#[tauri::command]
fn native_stop_recording(state: State<'_, AppState>) -> Result<String, String> {
    state
        .native_recorder
        .stop()
        .map(|path| path.to_string_lossy().to_string())
        .map_err(|e| e.to_string())
}

/// Pause native recording without stopping the stream.
#[tauri::command]
fn native_pause_recording(state: State<'_, AppState>) -> Result<(), String> {
    state
        .native_recorder
        .pause()
        .map_err(|e| e.to_string())
}

/// Resume native recording.
#[tauri::command]
fn native_resume_recording(state: State<'_, AppState>) -> Result<(), String> {
    state
        .native_recorder
        .resume()
        .map_err(|e| e.to_string())
}

/// Check if native recording is active.
#[tauri::command]
fn native_is_recording(state: State<'_, AppState>) -> Result<bool, String> {
    state
        .native_recorder
        .is_recording()
        .map_err(|e| e.to_string())
}

// ==================== OBS Integration Commands ====================

/// Detect OBS installation and status
#[tauri::command]
async fn obs_detect() -> Result<OBSInfo, String> {
    OBSDetector::detect().map_err(|e| e.to_string())
}

/// Connect to OBS WebSocket
#[tauri::command]
async fn obs_connect(
    state: State<'_, AppState>,
    host: String,
    port: u16,
    password: Option<String>,
) -> Result<OBSConnectionStatus, String> {
    let mut obs = state.obs_manager.lock().await;
    obs.connect(&host, port, password)
        .await
        .map_err(|e| e.to_string())
}

/// Disconnect from OBS
#[tauri::command]
async fn obs_disconnect(state: State<'_, AppState>) -> Result<(), String> {
    let mut obs = state.obs_manager.lock().await;
    obs.disconnect().await.map_err(|e| e.to_string())
}

/// Check if connected to OBS
#[tauri::command]
async fn obs_is_connected(state: State<'_, AppState>) -> Result<bool, String> {
    let obs = state.obs_manager.lock().await;
    Ok(obs.is_connected())
}

/// Get list of audio sources from OBS
#[tauri::command]
async fn obs_get_audio_sources(state: State<'_, AppState>) -> Result<Vec<OBSAudioSource>, String> {
    let obs = state.obs_manager.lock().await;
    obs.get_audio_sources().await.map_err(|e| e.to_string())
}

/// Start OBS recording
#[tauri::command]
async fn obs_start_recording(state: State<'_, AppState>) -> Result<(), String> {
    let mut obs = state.obs_manager.lock().await;
    obs.start_recording().await.map_err(|e| e.to_string())
}

/// Stop OBS recording and return file path
#[tauri::command]
async fn obs_stop_recording(state: State<'_, AppState>) -> Result<String, String> {
    let mut obs = state.obs_manager.lock().await;
    let path = obs.stop_recording().await.map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

/// Pause OBS recording
#[tauri::command]
async fn obs_pause_recording(state: State<'_, AppState>) -> Result<(), String> {
    let mut obs = state.obs_manager.lock().await;
    obs.pause_recording().await.map_err(|e| e.to_string())
}

/// Resume OBS recording
#[tauri::command]
async fn obs_resume_recording(state: State<'_, AppState>) -> Result<(), String> {
    let mut obs = state.obs_manager.lock().await;
    obs.resume_recording().await.map_err(|e| e.to_string())
}

/// Get OBS recording status
#[tauri::command]
async fn obs_get_recording_status(state: State<'_, AppState>) -> Result<OBSRecordingStatus, String> {
    let obs = state.obs_manager.lock().await;
    obs.get_recording_status().await.map_err(|e| e.to_string())
}

/// Apply filter preset to audio source
#[tauri::command]
async fn obs_apply_filter_preset(
    state: State<'_, AppState>,
    source_name: String,
    preset_name: String,
) -> Result<(), String> {
    let obs = state.obs_manager.lock().await;

    // Get the preset by name
    let preset = match preset_name.as_str() {
        "lecture_hall" => AudioFilterPreset::lecture_hall(),
        "clinical_skills" => AudioFilterPreset::clinical_skills(),
        "online_lecture" => AudioFilterPreset::online_lecture(),
        _ => return Err("Unknown preset".to_string()),
    };

    obs.apply_filter_preset(&source_name, &preset)
        .await
        .map_err(|e| e.to_string())
}

/// Get available filter presets
#[tauri::command]
async fn obs_get_filter_presets() -> Result<Vec<AudioFilterPreset>, String> {
    Ok(OBSManager::get_filter_presets())
}

/// Set audio source volume
#[tauri::command]
async fn obs_set_source_volume(
    state: State<'_, AppState>,
    source_name: String,
    volume_db: f32,
) -> Result<(), String> {
    let obs = state.obs_manager.lock().await;
    obs.set_source_volume(&source_name, volume_db)
        .await
        .map_err(|e| e.to_string())
}

/// Mute/unmute audio source
#[tauri::command]
async fn obs_set_source_muted(
    state: State<'_, AppState>,
    source_name: String,
    muted: bool,
) -> Result<(), String> {
    let obs = state.obs_manager.lock().await;
    obs.set_source_muted(&source_name, muted)
        .await
        .map_err(|e| e.to_string())
}

/// Download and install OBS Studio automatically
#[tauri::command]
async fn obs_download_and_install(
    app_handle: tauri::AppHandle
) -> Result<(), String> {
    use obs::{OBSInstaller, OBSInstallProgress};

    let downloads_dir = app_handle
        .path_resolver()
        .app_cache_dir()
        .ok_or("Failed to get cache directory")?
        .join("downloads");

    let progress_callback = move |progress: OBSInstallProgress| {
        let _ = app_handle.emit_all("obs-install-progress", progress);
    };

    OBSInstaller::install_and_configure(&downloads_dir, progress_callback)
        .await
        .map_err(|e| e.to_string())
}

/// Configure OBS Studio settings
#[tauri::command]
async fn obs_configure() -> Result<(), String> {
    use obs::OBSConfigWriter;

    OBSConfigWriter::configure_all()
        .map_err(|e| e.to_string())
}

/// Launch OBS Studio
#[tauri::command]
async fn obs_launch() -> Result<(), String> {
    use obs::OBSInstaller;

    OBSInstaller::launch_obs()
        .map_err(|e| e.to_string())
}

/// Get OBS download URL for current platform
#[tauri::command]
async fn obs_get_download_url() -> Result<String, String> {
    use obs::OBSInstaller;

    OBSInstaller::get_download_url()
        .map_err(|e| e.to_string())
}

// ==================== End OBS Commands ====================

fn main() {
    // Load or create configuration
    let config = load_config().unwrap_or_default();

    tauri::Builder::default()
        .manage(AppState {
            process_manager: Mutex::new(ProcessManager::new()),
            config: Mutex::new(config),
            obs_manager: Mutex::new(OBSManager::new()),
            native_recorder: NativeRecorderController::new(),
        })
        .invoke_handler(tauri::generate_handler![
            is_first_run,
            complete_setup,
            get_config,
            update_config,
            start_services,
            stop_services,
            get_service_status,
            download_model,
            check_backend_health,
            check_bundled_models,
            save_recorded_audio,
            native_start_recording,
            native_stop_recording,
            native_pause_recording,
            native_resume_recording,
            native_is_recording,
            // OBS commands
            obs_detect,
            obs_connect,
            obs_disconnect,
            obs_is_connected,
            obs_get_audio_sources,
            obs_start_recording,
            obs_stop_recording,
            obs_pause_recording,
            obs_resume_recording,
            obs_get_recording_status,
            obs_apply_filter_preset,
            obs_get_filter_presets,
            obs_set_source_volume,
            obs_set_source_muted,
            // OBS installation commands
            obs_download_and_install,
            obs_configure,
            obs_launch,
            obs_get_download_url,
        ])
        .setup(|app| {
            // Perform any initial setup here
            println!("CogniScribe starting...");
            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                // Graceful shutdown handled by Tauri's lifecycle
                println!("Window closing, services will be cleaned up");
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
                // Cleanup happens here
                println!("Application exiting");
            }
        });
}
