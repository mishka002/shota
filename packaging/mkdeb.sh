#!/usr/bin/env bash
set -euo pipefail

APP_NAME="shota"
VERSION="0.1.1"
ARCH="all"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT_DIR/packaging/stage"
DIST="$ROOT_DIR/dist"

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/256x256/apps" "$STAGE/opt/$APP_NAME" "$DIST"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: mishka002 <mishka002@users.noreply.github.com>
Depends: python3, python3-tk, git
Section: utils
Priority: optional
Description: Shota launcher and calculator
 Simple GUI launcher that updates a GitHub repo and runs a calculator.
EOF

# App payload
cp "$ROOT_DIR/lancher.py" "$STAGE/opt/$APP_NAME/"
cp "$ROOT_DIR/home.py" "$STAGE/opt/$APP_NAME/"
cp "$ROOT_DIR/updater.py" "$STAGE/opt/$APP_NAME/"
cp "$ROOT_DIR/githubSettings.md" "$STAGE/opt/$APP_NAME/"
cp "$ROOT_DIR/requirements.txt" "$STAGE/opt/$APP_NAME/"

# Launcher wrapper
install -m 0755 "$ROOT_DIR/packaging/scripts/shota-launch" "$STAGE/usr/bin/shota"

# Desktop entry (icon optional)
install -m 0644 "$ROOT_DIR/packaging/desktop/shota.desktop" "$STAGE/usr/share/applications/shota.desktop"
if [ -f "$ROOT_DIR/packaging/desktop/shota.png" ]; then
  install -m 0644 "$ROOT_DIR/packaging/desktop/shota.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/shota.png"
fi

dpkg-deb --build "$STAGE" "$DIST/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo "Built: $DIST/${APP_NAME}_${VERSION}_${ARCH}.deb"