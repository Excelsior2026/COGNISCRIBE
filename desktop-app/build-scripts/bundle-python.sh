#!/usr/bin/env bash
set -euo pipefail

echo "🐍 Bundling Python backend with PyInstaller..."

# Navigate to parent directory (CogniScribe root)
cd "$(dirname "$0")/../.."

# Check if Python backend exists
if [ ! -d "src/api" ]; then
    echo "❌ Error: Python backend not found at src/api"
    exit 1
fi

# Select Python interpreter (prefer 3.13 if available)
if command -v python3.13 > /dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 > /dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python > /dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "❌ Error: Python 3.9+ not found in PATH"
    exit 1
fi

echo "Using Python: $PYTHON_BIN"

# Ensure Python version is supported
"$PYTHON_BIN" - << 'PY'
import sys
if sys.version_info < (3, 9):
    print("❌ Error: Python 3.9+ is required for bundling.")
    raise SystemExit(1)
PY

# Install PyInstaller if not already installed
if ! "$PYTHON_BIN" -m pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    "$PYTHON_BIN" -m pip install pyinstaller
fi

# Create a spec file for better control
cat > cogniscribe-api.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

import importlib.util
from pathlib import Path

block_cipher = None

faster_whisper_spec = importlib.util.find_spec('faster_whisper')
if faster_whisper_spec and faster_whisper_spec.origin:
    faster_whisper_dir = Path(faster_whisper_spec.origin).resolve().parent
    faster_whisper_assets = faster_whisper_dir / 'assets'
else:
    faster_whisper_assets = None

datas = [
    ('src', 'src'),
]
if faster_whisper_assets and faster_whisper_assets.exists():
    datas.append((str(faster_whisper_assets), 'faster_whisper/assets'))

a = Analysis(
    ['src/api/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'librosa',
        'librosa.core',
        'librosa.feature',
        'soundfile',
        'noisereduce',
        'pydub',
        'faster_whisper',
        'requests',
        'multipart',
        'python_multipart',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cogniscribe-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console for debugging (set to False for production)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cogniscribe-api',
)
EOF

# Run PyInstaller
echo "Running PyInstaller with $PYTHON_BIN..."
"$PYTHON_BIN" -m PyInstaller --clean cogniscribe-api.spec

# Check if build succeeded
EXE_PATH="dist/cogniscribe-api/cogniscribe-api"
if [ -f "${EXE_PATH}.exe" ]; then
    EXE_PATH="${EXE_PATH}.exe"
fi

if [ ! -f "$EXE_PATH" ]; then
    echo "❌ PyInstaller build failed"
    exit 1
fi

# Create destination directory
mkdir -p desktop-app/src-tauri/resources/python-backend

# Copy bundled application
echo "Copying bundled application to desktop-app resources..."
rm -rf desktop-app/src-tauri/resources/python-backend/*
cp -r dist/cogniscribe-api/* desktop-app/src-tauri/resources/python-backend/

# Make executable (no-op on Windows)
if [ -f desktop-app/src-tauri/resources/python-backend/cogniscribe-api ]; then
    chmod +x desktop-app/src-tauri/resources/python-backend/cogniscribe-api
fi
if [ -f desktop-app/src-tauri/resources/python-backend/cogniscribe-api.exe ]; then
    chmod +x desktop-app/src-tauri/resources/python-backend/cogniscribe-api.exe
fi

echo "✅ Python backend bundled successfully"
echo "   Location: desktop-app/src-tauri/resources/python-backend/"
echo "   Size: $(du -sh desktop-app/src-tauri/resources/python-backend/ | cut -f1)"

# Cleanup
rm -f cogniscribe-api.spec
rm -rf build/

echo ""
echo "Test the bundled app:"
echo "  cd desktop-app/src-tauri/resources/python-backend"
echo "  ./cogniscribe-api"
