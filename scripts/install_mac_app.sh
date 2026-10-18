#!/bin/bash
# Build "Job Hunter Agent.app" and put it in /Applications (or the folder given as $1).
# Clicking it starts the dashboard in the background if it isn't running, then opens it
# in its own window (Chrome app mode when Chrome is installed, else the default browser).
#
#   bash scripts/install_mac_app.sh              # -> /Applications
#   bash scripts/install_mac_app.sh ~/Applications
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$(command -v python3)"
DEST="${1:-/Applications}"
APP="$DEST/Job Hunter Agent.app"
ICNS="$REPO/docs/brand/app-icon/AppIcon.icns"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
[ -f "$ICNS" ] && cp "$ICNS" "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Job Hunter Agent</string>
  <key>CFBundleDisplayName</key><string>Job Hunter Agent</string>
  <key>CFBundleIdentifier</key><string>local.jobhunteragent.dashboard</string>
  <key>CFBundleExecutable</key><string>launch</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
</dict></plist>
PLIST

cat > "$APP/Contents/MacOS/launch" <<LAUNCH
#!/bin/bash
REPO="$REPO"
PY="$PY"
URL="http://127.0.0.1:\${JHA_PORT:-8765}"
if ! curl -s -o /dev/null "\$URL/api/config"; then
  mkdir -p "\$REPO/data"
  cd "\$REPO" && nohup "\$PY" -m dashboard.app >> "\$REPO/data/app.log" 2>&1 &
  for i in \$(seq 1 60); do curl -s -o /dev/null "\$URL/api/config" && break; sleep 0.25; done
fi
if [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --app="\$URL"
else
  open "\$URL"
fi
LAUNCH
chmod +x "$APP/Contents/MacOS/launch"
touch "$APP"   # refresh Finder's icon cache
echo "installed: $APP"
