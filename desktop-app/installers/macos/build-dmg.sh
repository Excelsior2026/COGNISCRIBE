#!/usr/bin/env bash
set -euo pipefail

echo "🍎 Building macOS DMG for CogniScribe..."

# Configuration
APP_NAME="CogniScribe"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_APP_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$DESKTOP_APP_DIR/src-tauri/target/release/bundle/macos"
OUTPUT_DIR="$DESKTOP_APP_DIR/installers/output/macos"
DMG_NAME="$APP_NAME-$VERSION"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Build Tauri app
echo -e "${BLUE}Step 1: Building Tauri application...${NC}"
cd "$DESKTOP_APP_DIR"
npm run tauri:build
echo -e "${GREEN}✓ Build complete${NC}"

# Step 2: Verify .app exists
if [ ! -d "$BUILD_DIR/$APP_NAME.app" ]; then
    echo "❌ Error: $APP_NAME.app not found"
    exit 1
fi

# Step 2.5: Ensure microphone usage description exists
INFO_PLIST="$BUILD_DIR/$APP_NAME.app/Contents/Info.plist"
MIC_DESC="CogniScribe needs access to your microphone to record lectures."
if [ -f "$INFO_PLIST" ]; then
    /usr/libexec/PlistBuddy -c "Print :NSMicrophoneUsageDescription" "$INFO_PLIST" >/dev/null 2>&1 \
        && /usr/libexec/PlistBuddy -c "Set :NSMicrophoneUsageDescription \"$MIC_DESC\"" "$INFO_PLIST" \
        || /usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string \"$MIC_DESC\"" "$INFO_PLIST"
    echo -e "${GREEN}✓ Updated Info.plist microphone usage description${NC}"
else
    echo "⚠️  Warning: Info.plist not found to set microphone usage description"
fi

# Step 3: Create DMG
echo -e "${BLUE}Step 2: Creating DMG...${NC}"
mkdir -p "$OUTPUT_DIR"

# Use create-dmg if available, otherwise use hdiutil
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "$BUILD_DIR/$APP_NAME.app/Contents/Resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 200 190 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 600 185 \
        "$OUTPUT_DIR/$DMG_NAME.dmg" \
        "$BUILD_DIR/$APP_NAME.app"
else
    # Fallback: simple DMG creation
    echo "create-dmg not found, using hdiutil..."

    TMP_DMG="$OUTPUT_DIR/tmp-$DMG_NAME.dmg"
    rm -f "$OUTPUT_DIR/$DMG_NAME.dmg"
    rm -f "$TMP_DMG"

    hdiutil create -size 800m -fs HFS+ -volname "$APP_NAME" "$TMP_DMG"

    hdiutil attach "$TMP_DMG" -mountpoint /Volumes/$APP_NAME

    cp -R "$BUILD_DIR/$APP_NAME.app" "/Volumes/$APP_NAME/"
    ln -s /Applications "/Volumes/$APP_NAME/Applications"

    hdiutil detach "/Volumes/$APP_NAME"

    hdiutil convert "$TMP_DMG" -format UDZO -o "$OUTPUT_DIR/$DMG_NAME.dmg" -ov
    rm "$TMP_DMG"
fi

echo -e "${GREEN}✓ DMG created${NC}"

# Get size
DMG_SIZE=$(du -h "$OUTPUT_DIR/$DMG_NAME.dmg" | cut -f1)

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DMG created successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "  📦 Location: $OUTPUT_DIR/$DMG_NAME.dmg"
echo "  📊 Size: $DMG_SIZE"
echo ""
echo "To test:"
echo "  open \"$OUTPUT_DIR/$DMG_NAME.dmg\""
echo ""
