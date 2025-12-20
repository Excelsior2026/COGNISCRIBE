# Cliniscribe Desktop App Architecture

## Overview

A cross-platform desktop application that bundles all Cliniscribe dependencies into a single installer, eliminating the need for manual Python, Ollama, or FFmpeg installation.

## Technology Stack

### Frontend
- **Framework**: React 18 + Vite (reusing existing web UI)
- **Styling**: Tailwind CSS
- **State Management**: React hooks

### Desktop Wrapper
- **Framework**: Tauri 1.5+ (Rust-based)
- **Size**: ~600KB overhead (vs Electron's 100MB+)
- **Security**: Sandboxed webview with IPC communication
- **Auto-updater**: Built-in update mechanism

### Bundled Backend
- **Python Runtime**: Embedded Python 3.11 (via PyInstaller)
- **API Server**: FastAPI bundled as standalone executable
- **Audio Processing**: librosa, noisereduce, pydub (all bundled)
- **Transcription**: faster-whisper (bundled)

### Bundled AI Services
- **Ollama**: Platform-specific binary (auto-managed)
- **Models**: Auto-downloaded on first run with progress tracking
  - Whisper: base model (~150MB)
  - Llama: llama3.1:8b (~4.7GB)

## Application Structure

```
cliniscribe-desktop/
├── src/                          # React frontend
│   ├── components/
│   │   ├── SetupWizard/         # First-run setup
│   │   ├── Dashboard/           # Main app UI
│   │   ├── Settings/            # Configuration
│   │   └── StatusBar/           # Service health indicators
│   ├── hooks/
│   │   ├── useBackendHealth.ts  # Monitor backend status
│   │   └── useModelDownload.ts  # Track model downloads
│   └── App.tsx
│
├── src-tauri/                    # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs              # App entry point
│   │   ├── process_manager.rs   # Manage Python/Ollama processes
│   │   ├── model_downloader.rs  # Download AI models
│   │   ├── config.rs            # Settings persistence
│   │   └── updater.rs           # Auto-update logic
│   │
│   ├── resources/               # Bundled at build time
│   │   ├── python-backend/      # PyInstaller-built backend
│   │   │   ├── cliniscribe-api  # Executable (platform-specific)
│   │   │   └── _internal/       # Dependencies
│   │   └── ollama/              # Platform-specific Ollama binary
│   │
│   ├── icons/                   # App icons
│   └── tauri.conf.json          # Tauri configuration
│
├── build-scripts/               # Build automation
│   ├── bundle-python.sh         # PyInstaller packaging
│   ├── download-ollama.sh       # Fetch Ollama binaries
│   └── build-installer.sh       # Platform-specific installers
│
└── installers/                  # Output directory
    ├── CliniScribe-1.0.0.dmg   # macOS
    ├── CliniScribe-1.0.0.msi   # Windows
    └── CliniScribe-1.0.0.AppImage # Linux
```

## Startup Sequence

### 1. Application Launch
```
User double-clicks app
    ↓
Tauri initializes
    ↓
Check if first run
    ├─ YES → Show Setup Wizard
    │         ├─ Select data directory
    │         ├─ Download Whisper model (with progress)
    │         ├─ Download Llama model (with progress)
    │         └─ Save preferences
    │
    └─ NO  → Load saved preferences
```

### 2. Service Startup
```
Start Ollama process
    ↓
Wait for Ollama health check (5s timeout)
    ↓
Start Python FastAPI process
    ↓
Wait for API health check (10s timeout)
    ↓
Show main window
    ↓
Display service status in UI
```

### 3. Processing Flow
```
User uploads audio
    ↓
Frontend → IPC → Tauri
    ↓
Tauri → HTTP → Python API (localhost:8080)
    ↓
Python API → Ollama (localhost:11436)
    ↓
Results → Frontend
    ↓
Display study notes
```

### 4. Shutdown
```
User closes app
    ↓
Tauri intercepts close event
    ↓
Gracefully stop Python API
    ↓
Gracefully stop Ollama
    ↓
Save application state
    ↓
Exit
```

## Inter-Process Communication (IPC)

Tauri provides secure IPC between frontend and Rust backend:

### Frontend → Rust Commands
```typescript
// Check backend health
await invoke('check_backend_health');

// Download model with progress
await invoke('download_model', {
  modelName: 'whisper-base',
  onProgress: (progress) => console.log(progress)
});

// Get app settings
const settings = await invoke('get_settings');

// Update settings
await invoke('update_settings', { settings: {...} });
```

### Rust → Frontend Events
```rust
// Send progress updates
app.emit_all("download-progress", {
    model: "llama3.1:8b",
    percent: 45,
    downloaded: "2.1GB",
    total: "4.7GB"
});

// Send service status
app.emit_all("service-status", {
    ollama: "running",
    api: "running",
    whisper_loaded: true
});
```

## Process Management

### Python Backend Management
```rust
// src-tauri/src/process_manager.rs

pub struct BackendProcess {
    child: Child,
    port: u16,
}

impl BackendProcess {
    pub fn start(app_dir: &Path) -> Result<Self> {
        let exe_path = app_dir.join("resources/python-backend/cliniscribe-api");

        let child = Command::new(exe_path)
            .env("PORT", "8080")
            .env("OLLAMA_HOST", "localhost")
            .env("OLLAMA_PORT", "11436")
            .spawn()?;

        // Wait for health check
        wait_for_health("http://localhost:8080/api/health")?;

        Ok(Self { child, port: 8080 })
    }

    pub fn stop(&mut self) -> Result<()> {
        self.child.kill()?;
        Ok(())
    }
}
```

### Ollama Management
```rust
pub struct OllamaProcess {
    child: Child,
    port: u16,
}

impl OllamaProcess {
    pub fn start(app_dir: &Path) -> Result<Self> {
        let exe_path = app_dir.join("resources/ollama/ollama");

        let child = Command::new(exe_path)
            .arg("serve")
            .spawn()?;

        wait_for_health("http://localhost:11436/api/tags")?;

        Ok(Self { child, port: 11436 })
    }
}
```

## Model Management

### First-Run Model Download
```rust
pub async fn download_model(
    model_name: &str,
    progress_callback: impl Fn(DownloadProgress)
) -> Result<()> {
    match model_name {
        "whisper-base" => download_whisper_model(progress_callback).await,
        "llama3.1:8b" => download_ollama_model(progress_callback).await,
        _ => Err("Unknown model")
    }
}

async fn download_ollama_model(progress_callback: impl Fn(DownloadProgress)) -> Result<()> {
    // Use Ollama API to pull model
    let client = reqwest::Client::new();
    let mut stream = client
        .post("http://localhost:11436/api/pull")
        .json(&json!({ "name": "llama3.1:8b" }))
        .send()
        .await?
        .bytes_stream();

    // Parse JSON stream for progress
    while let Some(chunk) = stream.next().await {
        let progress: DownloadProgress = serde_json::from_slice(&chunk?)?;
        progress_callback(progress);
    }

    Ok(())
}
```

## Configuration Storage

Settings stored in platform-specific locations:
- **macOS**: `~/Library/Application Support/com.cliniscribe.app/`
- **Windows**: `%APPDATA%\CliniScribe\`
- **Linux**: `~/.config/cliniscribe/`

```rust
#[derive(Serialize, Deserialize)]
pub struct AppConfig {
    // Model settings
    pub whisper_model: String,      // "base", "small", "medium"
    pub ollama_model: String,        // "llama3.1:8b"

    // Processing settings
    pub default_ratio: f32,          // 0.15
    pub default_subject: String,     // ""

    // Storage
    pub data_directory: PathBuf,     // Where to store audio files
    pub auto_delete_days: u32,       // 7

    // UI preferences
    pub theme: String,               // "light" | "dark"
    pub auto_updates: bool,          // true
}
```

## Build Process

### 1. Bundle Python Backend
```bash
# build-scripts/bundle-python.sh

cd ../
python -m PyInstaller \
    --onefile \
    --name cliniscribe-api \
    --add-data "src:src" \
    --hidden-import librosa \
    --hidden-import noisereduce \
    --clean \
    src/api/main.py

# Output: dist/cliniscribe-api
mv dist/cliniscribe-api desktop-app/src-tauri/resources/python-backend/
```

### 2. Download Ollama
```bash
# build-scripts/download-ollama.sh

PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

if [ "$PLATFORM" = "darwin" ]; then
    curl -L https://ollama.ai/download/ollama-darwin -o ollama
elif [ "$PLATFORM" = "linux" ]; then
    curl -L https://ollama.ai/download/ollama-linux-${ARCH} -o ollama
fi

chmod +x ollama
mv ollama desktop-app/src-tauri/resources/ollama/
```

### 3. Build Tauri App
```bash
cd desktop-app
npm run tauri build

# Outputs:
# - macOS: src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_x64.dmg
# - Windows: src-tauri/target/release/bundle/msi/CliniScribe_1.0.0_x64.msi
# - Linux: src-tauri/target/release/bundle/appimage/CliniScribe_1.0.0_amd64.AppImage
```

## Security Considerations

### Sandboxing
- Tauri runs with limited permissions by default
- Python backend only accessible via localhost
- No external network access except for model downloads
- File system access restricted to app data directory

### Content Security Policy
```json
{
  "csp": "default-src 'self'; connect-src 'self' http://localhost:8080 http://localhost:11436"
}
```

### Auto-Update Security
- Code-signed installers (macOS/Windows)
- HTTPS-only update server
- Signature verification before installing updates

## Size Estimates

### Installer Sizes
- **macOS**: ~600MB (Python: 100MB, Ollama: 50MB, Tauri: 600KB, Models: 450MB)
- **Windows**: ~650MB (similar breakdown)
- **Linux**: ~600MB (similar breakdown)

### Runtime Memory
- **Idle**: ~200MB (Tauri + React UI)
- **Processing**: ~4GB (Whisper model + Ollama model loaded)

### Disk Space
- **Application**: ~600MB
- **Models**: ~5GB (Whisper base + Llama 8B)
- **Audio Storage**: User-configurable (auto-cleanup after 7 days)

## Future Enhancements

### Phase 2 Features
- [ ] Cloud sync for study notes
- [ ] Collaboration features (share notes with classmates)
- [ ] Browser extension for capturing web lectures
- [ ] Mobile companion app
- [ ] Plugin system for custom export formats
- [ ] Integration with Anki for flashcard generation
- [ ] Multi-language support
- [ ] Offline speech-to-text fallback

### Performance Optimizations
- [ ] Lazy-load models (only load when needed)
- [ ] Model quantization (smaller file sizes)
- [ ] Incremental model downloads (resume support)
- [ ] Background processing queue
- [ ] GPU acceleration detection and auto-config

## Development Workflow

### Local Development
```bash
# Terminal 1: Run Python backend
cd ../
uvicorn src.api.main:app --reload --port 8080

# Terminal 2: Run Ollama
ollama serve

# Terminal 3: Run Tauri dev
cd desktop-app
npm run tauri dev
```

### Testing
```bash
# Unit tests
npm test

# Integration tests
npm run test:e2e

# Build test
npm run tauri build --debug
```

## Deployment

### Release Process
1. Update version in `tauri.conf.json` and `package.json`
2. Run build scripts for all platforms (CI/CD)
3. Code-sign binaries (macOS/Windows)
4. Upload to update server
5. Publish release on GitHub
6. Notify users via in-app update mechanism

### Auto-Update Flow
```
App checks for updates (daily)
    ↓
New version available?
    ├─ YES → Show update notification
    │         ├─ User clicks "Update"
    │         ├─ Download installer in background
    │         ├─ Verify signature
    │         ├─ Prompt to restart
    │         └─ Install and relaunch
    │
    └─ NO  → Continue normally
```

## Support & Maintenance

### Error Reporting
- Sentry integration for crash reports
- Anonymous usage analytics (opt-in)
- Logs stored locally for debugging

### User Support
- In-app help documentation
- Video tutorials
- Community Discord server
- GitHub issues for bug reports

---

**Target User**: Medical student with zero technical knowledge
**Setup Time**: < 5 minutes (download + install + first run)
**User Actions**: 1. Download installer, 2. Double-click, 3. Wait for models, 4. Start using
