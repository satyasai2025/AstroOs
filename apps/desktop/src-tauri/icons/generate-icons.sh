#!/usr/bin/env bash
# Generate Tauri app icons from the source SVG.
# Requires Inkscape or ImageMagick to be installed.
# Usage: bash generate-icons.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="${SCRIPT_DIR}/icon.svg"

if [ ! -f "$SOURCE" ]; then
    echo "Source icon not found: $SOURCE"
    exit 1
fi

echo "Generating icons from ${SOURCE}..."

# Determine which tool is available
if command -v inkscape &>/dev/null; then
    CONVERT="inkscape"
elif command -v magick &>/dev/null; then
    CONVERT="magick"
elif command -v convert &>/dev/null; then
    CONVERT="convert"
else
    echo "Error: Neither Inkscape nor ImageMagick found."
    echo "Install one of them:"
    echo "  macOS: brew install inkscape"
    echo "  Linux: sudo apt install inkscape"
    echo "  Windows: Install Inkscape from https://inkscape.org/"
    exit 1
fi

generate_png() {
    local size="$1"
    local output="$2"
    echo "  -> ${output} (${size}x${size})"

    case "$CONVERT" in
        inkscape)
            inkscape "$SOURCE" --export-type=png \
                --export-width="$size" --export-height="$size" \
                --export-filename="$output" 2>/dev/null
            ;;
        magick)
            magick convert "$SOURCE" -resize "${size}x${size}" "$output"
            ;;
        convert)
            convert "$SOURCE" -resize "${size}x${size}" "$output"
            ;;
    esac
}

# Generate platform-specific icons
generate_png 32 "32x32.png"
generate_png 128 "128x128.png"
generate_png 256 "128x128@2x.png"

# Generate ICO (multi-size Windows icon) — needs ImageMagick
if command -v magick &>/dev/null || command -v convert &>/dev/null; then
    echo "  -> icon.ico (Windows ICO)"
    if command -v magick &>/dev/null; then
        magick convert "$SOURCE" -define icon:auto-resize=256,128,64,48,32,16 "icon.ico"
    else
        convert "$SOURCE" -define icon:auto-resize=256,128,64,48,32,16 "icon.ico"
    fi
else
    echo "  [SKIP] icon.ico — ImageMagick not available. Run: magick convert icon.svg icon.ico"
fi

# Generate ICNS (macOS) — needs iconutil (macOS only)
if command -v iconutil &>/dev/null; then
    echo "  -> icon.icns (macOS ICNS)"
    # Create iconset directory
    ICONSET="AstroOS.iconset"
    mkdir -p "$ICONSET"
    generate_png 16 "$ICONSET/icon_16x16.png"
    generate_png 32 "$ICONSET/icon_16x16@2x.png"
    generate_png 32 "$ICONSET/icon_32x32.png"
    generate_png 64 "$ICONSET/icon_32x32@2x.png"
    generate_png 128 "$ICONSET/icon_128x128.png"
    generate_png 256 "$ICONSET/icon_128x128@2x.png"
    generate_png 256 "$ICONSET/icon_256x256.png"
    generate_png 512 "$ICONSET/icon_256x256@2x.png"
    generate_png 512 "$ICONSET/icon_512x512.png"
    iconutil -c icns "$ICONSET"
    mv "$ICONSET/icon.icns" "icon.icns"
    rm -rf "$ICONSET"
else
    echo "  [SKIP] icon.icns — iconutil not available (macOS only). Generate on macOS."
fi

echo ""
echo "Done! Icons generated in: $SCRIPT_DIR"
ls -lh "$SCRIPT_DIR"/*.png "$SCRIPT_DIR"/*.ico "$SCRIPT_DIR"/*.icns 2>/dev/null
