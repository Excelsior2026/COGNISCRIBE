# CliniScribe Desktop Application

A cross-platform desktop app that makes CliniScribe dead-simple for medical students. No Python, no Ollama, no terminal commands - just download, install, and use.

## Features

✅ **One-Click Installation** - Single installer for Mac, Windows, and Linux
✅ **No Dependencies** - Everything bundled (Python, Ollama, models)
✅ **First-Run Wizard** - Guided setup with automatic model downloads
✅ **Auto-Updates** - Seamless updates without reinstalling
✅ **100% Offline** - Works completely offline after initial setup
✅ **Tiny Size** - Only ~600 KB overhead (vs Electron's 100+ MB)

## Technology Stack

- **Desktop Framework**: Tauri (Rust-based, lightweight)
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Backend**: Bundled Python (PyInstaller) with FastAPI
- **AI**: Bundled Ollama with automatic model management

## Prerequisites for Development

### Required
- **Node.js** 18+ and npm
- **Rust** 1.70+ (for Tauri)
- **Python** 3.9+ (for backend bundling)

### Platform-Specific
- **macOS**: Xcode Command Line Tools
- **Windows**: Microsoft C++ Build Tools
- **Linux**: webkit2gtk-4.0, libgtk-3-dev

## Quick Start (Development)

### 1. Install Dependencies

```bash
# Install Node dependencies
npm install

# Install Tauri CLI
cargo install tauri-cli
```

### 2. Bundle Backend Services

```bash
# Bundle Python backend
npm run bundle:python

# Download Ollama binary
npm run bundle:ollama

# Or bundle both at once
npm run bundle:all
```

### 3. Run Development Server

```bash
npm run tauri:dev
```

This will:
- Start the React dev server (hot reload enabled)
- Launch the Tauri window
- Mock backend services for testing

## Building for Production

### Build All Platforms

```bash
# Build for your current platform
npm run tauri:build

# Outputs to: src-tauri/target/release/bundle/
```

### Platform-Specific Builds

#### macOS (.dmg)
```bash
npm run tauri:build
# Output: src-tauri/target/release/bundle/dmg/
```

#### Windows (.msi)
```bash
npm run tauri:build
# Output: src-tauri/target/release/bundle/msi/
```

#### Linux (.AppImage)
```bash
npm run tauri:build
# Output: src-tauri/target/release/bundle/appimage/
```

## Project Structure

```
desktop-app/
├── src/                          # React frontend
│   ├── components/
│   │   ├── SetupWizard/         # First-run setup flow
│   │   │   ├── SetupWizard.tsx
│   │   │   ├── WelcomeStep.tsx
│   │   │   ├── ModelDownloadStep.tsx
│   │   │   └── CompletionStep.tsx
│   │   ├── Dashboard/           # Main application UI
│   │   └── Settings/            # User preferences
│   ├── hooks/                   # React hooks for Tauri integration
│   ├── App.tsx                  # Main app component
│   └── main.tsx                 # Entry point
│
├── src-tauri/                    # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs              # Tauri commands & lifecycle
│   │   ├── process_manager.rs   # Manage Python/Ollama processes
│   │   ├── config.rs            # App configuration
│   │   └── model_downloader.rs  # Download AI models
│   │
│   ├── resources/               # Bundled at build time
│   │   ├── python-backend/      # PyInstaller bundle
│   │   │   ├── cliniscribe-api  # Executable
│   │   │   └── _internal/       # Dependencies
│   │   └── ollama/              # Ollama binary
│   │
│   ├── Cargo.toml               # Rust dependencies
│   └── tauri.conf.json          # Tauri configuration
│
├── build-scripts/               # Build automation
│   ├── bundle-python.sh         # PyInstaller packaging
│   ├── download-ollama.sh       # Fetch Ollama binaries
│   └── build-installer.sh       # Create installers
│
├── package.json                 # Node dependencies & scripts
└── ARCHITECTURE.md              # Detailed architecture docs
```

## Tauri Commands (Rust ↔ React)

The frontend can call these Rust functions:

### Setup & Configuration
```typescript
// Check if first run
const isFirstRun = await invoke<boolean>('is_first_run');

// Mark setup as complete
await invoke('complete_setup');

// Get/update config
const config = await invoke<AppConfig>('get_config');
await invoke('update_config', { newConfig });
```

### Service Management
```typescript
// Start backend services (Ollama + Python API)
await invoke('start_services');

// Stop services
await invoke('stop_services');

// Get service status
const status = await invoke<ServiceStatus>('get_service_status');
```

### Model Downloads
```typescript
// Download model with progress tracking
await invoke('download_model', { modelType: 'whisper' });
await invoke('download_model', { modelType: 'llama' });

// Listen for progress events
await listen('download-progress', (event) => {
  console.log(event.payload); // { model_name, percent, status, ... }
});
```

### Backend Health
```typescript
// Check if API is healthy
const health = await invoke<any>('check_backend_health');
```

## Configuration

The app stores configuration in platform-specific locations:

- **macOS**: `~/Library/Application Support/com.cliniscribe.app/config.json`
- **Windows**: `%APPDATA%\CliniScribe\config.json`
- **Linux**: `~/.config/cliniscribe/config.json`

### Config Schema
```json
{
  "setup_completed": false,
  "whisper_model": "base",
  "ollama_model": "llama3.1:8b",
  "use_gpu": false,
  "default_ratio": 0.15,
  "default_subject": "",
  "data_directory": "/path/to/audio_storage",
  "auto_delete_days": 7,
  "theme": "light",
  "auto_updates": true
}
```

## Debugging

### Enable Rust Logs
```bash
RUST_LOG=debug npm run tauri:dev
```

### Enable DevTools
In `tauri.conf.json`, set:
```json
{
  "build": {
    "devPath": "http://localhost:5173",
    "withGlobalTauri": true  // Enable window.__TAURI__
  }
}
```

### Test Backend Separately
```bash
cd src-tauri/resources/python-backend
./cliniscribe-api
```

Then visit http://localhost:8080/docs

### Test Ollama Separately
```bash
cd src-tauri/resources/ollama
./ollama serve
```

Then test: http://localhost:11436/api/tags

## Code Signing (Production)

### macOS
```bash
# Generate certificate in Keychain
# Export as Developer ID Application

# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name" \
  src-tauri/target/release/bundle/macos/CliniScribe.app

# Notarize (submit to Apple)
xcrun notarytool submit \
  src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_x64.dmg \
  --apple-id "your-email@example.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID" \
  --wait

# Staple the notarization ticket
xcrun stapler staple src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_x64.dmg
```

### Windows
```bash
# Use SignTool (requires code signing certificate)
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com \
  src-tauri/target/release/bundle/msi/CliniScribe_1.0.0_x64.msi
```

## Auto-Updates

Tauri includes built-in update support. Configure the update server in `tauri.conf.json`:

```json
{
  "updater": {
    "active": true,
    "endpoints": [
      "https://updates.cliniscribe.com/{{target}}/{{current_version}}"
    ],
    "dialog": true,
    "pubkey": "YOUR_PUBLIC_KEY_HERE"
  }
}
```

### Generate Update Keys
```bash
tauri signer generate -w ~/.tauri/cliniscribe.key
```

This creates:
- Private key: `~/.tauri/cliniscribe.key` (keep secret!)
- Public key: Add to `tauri.conf.json`

### Publish Updates
1. Build new version
2. Sign with private key
3. Upload to update server with signature

## Troubleshooting

### Build Fails on "Python backend not found"
```bash
# Re-run bundling
npm run bundle:python
```

### "Ollama binary not found"
```bash
# Re-download Ollama
npm run bundle:ollama
```

### Tauri dev fails to start
```bash
# Check Rust installation
rustc --version

# Reinstall Tauri CLI
cargo install tauri-cli --force
```

### Backend services won't start
1. Check logs in console
2. Verify binaries exist in `src-tauri/resources/`
3. Ensure executables have correct permissions:
   ```bash
   chmod +x src-tauri/resources/python-backend/cliniscribe-api
   chmod +x src-tauri/resources/ollama/ollama
   ```

## Performance

### Installer Sizes
- **macOS**: ~600 MB (Python: 100MB, Ollama: 50MB, Models: 450MB on first run)
- **Windows**: ~650 MB
- **Linux**: ~600 MB

### Runtime Memory
- **Idle**: ~200 MB (Tauri + React UI)
- **Processing**: ~4 GB (models loaded in memory)

### Startup Time
- **First Run**: 5-15 minutes (model downloads)
- **Subsequent Runs**: 5-10 seconds (services startup)

## Contributing

### Adding a New Feature
1. Create React component in `src/components/`
2. Add Tauri command in `src-tauri/src/main.rs`
3. Implement Rust logic in appropriate module
4. Update TypeScript types
5. Test in dev mode
6. Build and test production bundle

### Release Process
1. Update version in `package.json` and `tauri.conf.json`
2. Update CHANGELOG.md
3. Run `npm run tauri:build` for all platforms
4. Code-sign binaries
5. Create GitHub release with binaries
6. Update auto-update server

## License

Educational use for medical and nursing students.

## Support

- **Issues**: https://github.com/yourusername/Cliniscribe/issues
- **Docs**: See ARCHITECTURE.md for detailed design
- **Discord**: Coming soon

---

**Made with ❤️ for medical students who deserve better study tools**
