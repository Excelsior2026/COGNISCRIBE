// OBS Studio Integration Module
// Provides professional audio recording capabilities via OBS WebSocket

pub mod detector;
pub mod manager;
pub mod types;
pub mod installer;
pub mod config_writer;

pub use detector::OBSDetector;
pub use manager::OBSManager;
pub use installer::{OBSInstaller, OBSInstallProgress};
pub use config_writer::OBSConfigWriter;
pub use types::*;
