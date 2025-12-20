# CliniScribe Desktop - Quick Start Guide

Get the desktop app running in **10 minutes**! 🚀

---

## Prerequisites

Before starting, install these tools:

### 1. Node.js & npm
```bash
# Check if installed
node --version  # Should be 18+
npm --version

# If not installed, download from: https://nodejs.org/
```

### 2. Rust & Cargo
```bash
# Check if installed
rustc --version  # Should be 1.70+
cargo --version

# If not installed:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### 3. Platform-Specific Dependencies

**macOS:**
```bash
xcode-select --install
```

**Windows:**
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (usually pre-installed)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

---

## Step 1: Install Dependencies

```bash
cd desktop-app
npm install
```

This installs:
- React & TypeScript
- Tauri CLI
- Tailwind CSS
- All frontend dependencies

**Expected time:** 2-3 minutes

---

## Step 2: Bundle Backend Services

This packages the Python backend and downloads Ollama:

```bash
npm run bundle:all
```

**What this does:**
1. Bundles Python FastAPI with PyInstaller (~100 MB)
2. Downloads Ollama binary for your platform (~50 MB)

**Expected time:** 3-5 minutes

**Troubleshooting:**
- If `bundle:python` fails: Make sure you're in the Cliniscribe root directory
- If `bundle:ollama` fails: Check your internet connection

---

## Step 3: Run in Development Mode

```bash
npm run tauri:dev
```

**What happens:**
1. Vite starts the React dev server (port 5173)
2. Tauri compiles the Rust backend
3. Desktop window opens
4. Hot reload is enabled (edit code and see changes instantly!)

**Expected time:** 1-2 minutes for first compilation

**You should see:**
- A desktop window with the CliniScribe UI
- Welcome screen if it's your first run
- Or Dashboard if setup was already completed

---

## Development Workflow

### Making Changes

**Frontend (React/TypeScript):**
```bash
# Edit files in src/
# Changes auto-reload in the app window
```

**Backend (Rust):**
```bash
# Edit files in src-tauri/src/
# Save and wait for recompilation (~10-30 seconds)
```

### Common Commands

```bash
# Start dev server
npm run tauri:dev

# Build for production
npm run tauri:build

# Lint TypeScript
npm run lint

# Re-bundle Python backend (after code changes)
npm run bundle:python

# Re-download Ollama (if corrupted)
npm run bundle:ollama
```

---

## Testing the Full Workflow

### 1. First Run Setup

When you open the app for the first time:

1. **Welcome Screen** appears
   - Click "Get Started"

2. **Model Downloads** start
   - Whisper: ~150 MB
   - Llama: ~4.7 GB
   - This takes 5-15 minutes depending on internet speed
   - You can minimize and let it run in background

3. **Completion Screen**
   - Click "Launch CliniScribe"

4. **Dashboard** appears
   - You're ready to upload audio!

### 2. Process an Audio File

1. Click the upload area
2. Select an audio file (MP3, WAV, etc.)
3. Choose subject (optional)
4. Adjust summary length slider
5. Click "Generate Study Notes"
6. Wait 2-10 minutes depending on file length
7. View results!

---

## Project Structure Overview

```
desktop-app/
├── src/                          # React frontend
│   ├── components/
│   │   ├── SetupWizard/         # First-run flow
│   │   ├── Dashboard/           # Main UI
│   │   └── Settings/            # Preferences
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # Entry point
│   └── styles/                  # CSS
│
├── src-tauri/                    # Rust backend
│   ├── src/
│   │   ├── main.rs              # Tauri commands
│   │   ├── process_manager.rs   # Python/Ollama lifecycle
│   │   ├── config.rs            # Settings
│   │   └── model_downloader.rs  # Model downloads
│   │
│   └── resources/               # Bundled files
│       ├── python-backend/      # PyInstaller bundle
│       └── ollama/              # Ollama binary
│
├── build-scripts/               # Build automation
├── package.json                 # Node dependencies
├── vite.config.ts               # Vite configuration
└── tauri.conf.json              # Tauri configuration
```

---

## Troubleshooting

### "Failed to start services"

**Check backend bundles exist:**
```bash
ls src-tauri/resources/python-backend/cliniscribe-api
ls src-tauri/resources/ollama/ollama
```

**If missing:**
```bash
npm run bundle:all
```

### "Rust compilation failed"

**Update Rust:**
```bash
rustup update
```

**Clean and retry:**
```bash
cd src-tauri
cargo clean
cd ..
npm run tauri:dev
```

### "React errors" or "TypeScript errors"

**Check syntax:**
```bash
npm run lint
```

**Reinstall dependencies:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Backend won't start

**Test Python backend separately:**
```bash
cd src-tauri/resources/python-backend
./cliniscribe-api

# Should start on http://localhost:8080
# Visit http://localhost:8080/docs to test
```

**Test Ollama separately:**
```bash
cd src-tauri/resources/ollama
./ollama serve

# Should start on http://localhost:11436
# Test: curl http://localhost:11436/api/tags
```

### Models won't download

**Check Ollama is running:**
```bash
# In terminal 1:
cd src-tauri/resources/ollama
./ollama serve

# In terminal 2:
./ollama pull llama3.1:8b
```

### Port already in use

**Kill processes:**
```bash
# Kill Vite dev server (port 5173)
lsof -ti:5173 | xargs kill

# Kill Python API (port 8080)
lsof -ti:8080 | xargs kill

# Kill Ollama (port 11436)
lsof -ti:11436 | xargs kill
```

---

## Building for Production

### Build for Current Platform

```bash
npm run tauri:build
```

**Outputs:**
- **macOS**: `src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_x64.dmg`
- **Windows**: `src-tauri/target/release/bundle/msi/CliniScribe_1.0.0_x64.msi`
- **Linux**: `src-tauri/target/release/bundle/appimage/CliniScribe_1.0.0_amd64.AppImage`

**Expected time:** 5-10 minutes

### Build Size

Total installer size: **~600 MB**
- Tauri runtime: ~600 KB
- React app: ~500 KB (minified)
- Python backend: ~100 MB
- Ollama: ~50 MB
- Models (downloaded on first run): ~5 GB

---

## Next Steps

### Add Custom Features

1. **Edit components** in `src/components/`
2. **Add Tauri commands** in `src-tauri/src/main.rs`
3. **Update styling** in `src/styles/index.css`
4. **Configure settings** in `tauri.conf.json`

### Prepare for Distribution

1. **Create app icons** (see README.md)
2. **Get code signing certificates**
   - macOS: Apple Developer Program ($99/year)
   - Windows: Code signing cert ($100-400/year)
3. **Build for all platforms**
4. **Test installers on fresh systems**
5. **Create download page**

### Learn More

- **Tauri Docs**: https://tauri.app/v1/guides/
- **React Docs**: https://react.dev/
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/

---

## Getting Help

**Issues?**
- Check the main README.md
- Review ARCHITECTURE.md for technical details
- Ask in GitHub Issues
- Join the Discord community (coming soon)

**Success?**
- Share with fellow medical students!
- Contribute improvements
- Report bugs and suggest features

---

## Summary Checklist

- [ ] Installed Node.js, Rust, platform dependencies
- [ ] Ran `npm install`
- [ ] Ran `npm run bundle:all` (Python + Ollama)
- [ ] Ran `npm run tauri:dev` (app opened successfully)
- [ ] Completed first-run setup (models downloaded)
- [ ] Tested uploading and processing an audio file
- [ ] Reviewed results and export features

**If all checked:** You're ready to develop! 🎉

**If stuck:** Check Troubleshooting section above or open an issue.

---

**Happy coding! Let's make medical education better! 🎓💙**
