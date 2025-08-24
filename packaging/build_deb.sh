#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_DIR="$ROOT_DIR/packaging/debian"

echo "Building .deb package..."
cd "$PKG_DIR"

# Ensure scripts are executable
chmod +x ../scripts/shota-launch

debuild -us -uc

echo "Build completed. Check parent directory for .deb file."