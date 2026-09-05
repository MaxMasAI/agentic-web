#!/usr/bin/env bash
# ==============================================================================
# Linux AppImage Packaging Script for Agentic Web Workstation
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

APP_DIR="dist/AgenticWeb.AppDir"
OUTPUT_DIR="dist"

echo "[*] Building PyInstaller binary first..."
bash bin/build.sh

echo "[*] Preparing AppDir structure..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/share/applications"

# Copy binary payload
cp -r dist/AgenticWeb/* "$APP_DIR/usr/bin/"

# Copy icon and desktop entry
if [ -f "visuals/app_icon.png" ]; then
    cp visuals/app_icon.png "$APP_DIR/usr/share/icons/hicolor/256x256/apps/agenticweb.png"
    cp visuals/app_icon.png "$APP_DIR/agenticweb.png"
fi

cat << 'EOF' > "$APP_DIR/agenticweb.desktop"
[Desktop Entry]
Name=Agentic Web Workstation
Exec=AgenticWeb
Icon=agenticweb
Type=Application
Categories=Development;Utility;
Terminal=false
StartupWMClass=AgenticWeb
EOF

cp "$APP_DIR/agenticweb.desktop" "$APP_DIR/usr/share/applications/"

# Create AppRun entrypoint
cat << 'EOF' > "$APP_DIR/AppRun"
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/AgenticWeb" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Check for appimagetool
if command -v appimagetool &> /dev/null; then
    echo "[*] Generating AppImage package..."
    appimagetool "$APP_DIR" "$OUTPUT_DIR/AgenticWeb-x86_64.AppImage"
    echo "[OK] AppImage generated at: $OUTPUT_DIR/AgenticWeb-x86_64.AppImage"
else
    echo "[!] appimagetool not found in PATH. AppDir prepared at: $APP_DIR"
    echo "    To generate AppImage, install appimagetool and run:"
    echo "    appimagetool $APP_DIR dist/AgenticWeb-x86_64.AppImage"
fi
