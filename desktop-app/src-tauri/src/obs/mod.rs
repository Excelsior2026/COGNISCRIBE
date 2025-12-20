// OBS Studio Integration Module
// Provides professional audio recording capabilities via OBS WebSocket

pub mod detector;
pub mod manager;
pub mod types;

pub use detector::OBSDetector;
pub use manager::OBSManager;
pub use types::*;
