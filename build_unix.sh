#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:-FileExplorer3D}"
VERSION="${2:-dev}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Building $APP_NAME ($VERSION) ..."

# Build a windowed app and intentionally do NOT bundle config files.
pyinstaller --noconfirm --clean --windowed \
  --name "$APP_NAME" \
  --icon fileexplorer3d_icon.png \
  --collect-submodules OpenGL \
  main.py

DIST_DIR="$PROJECT_ROOT/dist"
APP_DIR="$DIST_DIR/$APP_NAME"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCHIVE_PATH="$DIST_DIR/${APP_NAME}-${PLATFORM}-${VERSION}.tar.gz"

if [ -f "$ARCHIVE_PATH" ]; then
  rm -f "$ARCHIVE_PATH"
fi

tar -C "$DIST_DIR" -czf "$ARCHIVE_PATH" "$APP_NAME"

echo "Build complete: $APP_DIR"
echo "Release archive: $ARCHIVE_PATH"
