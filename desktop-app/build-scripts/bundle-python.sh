#!/usr/bin/env bash
set -euo pipefail

echo "🐍 Bundling Python backend with PyInstaller..."

# Navigate to parent directory (Cliniscribe root)
cd "$(dirname "$0")/../.."

# Check if Python backend exists
if [ ! -d "src/api" ]; then
    echo "❌ Error: Python backend not found at src/api"
    exit 1
fi

# Install PyInstaller if not already installed
if ! python3 -m pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

# Create a spec file for better control
cat > cliniscribe-api.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/api/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
    ],
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
    name='cliniscribe-api',
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
    name='cliniscribe-api',
)
EOF

# Run PyInstaller
echo "Running PyInstaller with Python 3.13..."
python3.13 -m PyInstaller --clean cliniscribe-api.spec

# Check if build succeeded
if [ ! -f "dist/cliniscribe-api/cliniscribe-api" ]; then
    echo "❌ PyInstaller build failed"
    exit 1
fi

# Create destination directory
mkdir -p desktop-app/src-tauri/resources/python-backend

# Copy bundled application
echo "Copying bundled application to desktop-app resources..."
rm -rf desktop-app/src-tauri/resources/python-backend/*
cp -r dist/cliniscribe-api/* desktop-app/src-tauri/resources/python-backend/

# Make executable
chmod +x desktop-app/src-tauri/resources/python-backend/cliniscribe-api

echo "✅ Python backend bundled successfully"
echo "   Location: desktop-app/src-tauri/resources/python-backend/"
echo "   Size: $(du -sh desktop-app/src-tauri/resources/python-backend/ | cut -f1)"

# Cleanup
rm -f cliniscribe-api.spec
rm -rf build/

echo ""
echo "Test the bundled app:"
echo "  cd desktop-app/src-tauri/resources/python-backend"
echo "  ./cliniscribe-api"
