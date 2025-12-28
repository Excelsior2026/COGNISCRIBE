#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ICON="$SCRIPT_DIR/../../../docs/Logo.png"

if [ ! -f "$SOURCE_ICON" ]; then
    echo "Missing source logo at $SOURCE_ICON"
    exit 1
fi

cd "$SCRIPT_DIR"

echo "Using source logo: $SOURCE_ICON"
sips -z 1024 1024 "$SOURCE_ICON" --out icon.png >/dev/null
sips -z 512 512 icon.png --out icon-512.png >/dev/null
sips -z 32 32 icon.png --out 32x32.png >/dev/null
sips -z 128 128 icon.png --out 128x128.png >/dev/null
sips -z 256 256 icon.png --out 128x128@2x.png >/dev/null

# Create ICNS file for macOS
rm -rf temp.iconset
mkdir temp.iconset
sips -z 16 16 icon.png --out temp.iconset/icon_16x16.png >/dev/null
sips -z 32 32 icon.png --out temp.iconset/icon_16x16@2x.png >/dev/null
sips -z 32 32 icon.png --out temp.iconset/icon_32x32.png >/dev/null
sips -z 64 64 icon.png --out temp.iconset/icon_32x32@2x.png >/dev/null
sips -z 128 128 icon.png --out temp.iconset/icon_128x128.png >/dev/null
sips -z 256 256 icon.png --out temp.iconset/icon_128x128@2x.png >/dev/null
sips -z 256 256 icon.png --out temp.iconset/icon_256x256.png >/dev/null
sips -z 512 512 icon.png --out temp.iconset/icon_256x256@2x.png >/dev/null
sips -z 512 512 icon.png --out temp.iconset/icon_512x512.png >/dev/null
sips -z 1024 1024 icon.png --out temp.iconset/icon_512x512@2x.png >/dev/null
iconutil -c icns temp.iconset -o icon.icns
rm -rf temp.iconset

# ICO placeholder (replace with real .ico for Windows if needed)
cp icon.png icon.ico

echo "Icons created."
ls -lh icon.png icon-512.png 32x32.png 128x128.png 128x128@2x.png icon.icns icon.ico
