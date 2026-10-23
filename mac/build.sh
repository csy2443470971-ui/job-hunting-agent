#!/bin/bash
# Build "Job Hunter Agent.app": a native window on the local dashboard, one instance, its own Dock icon.
#
#   mac/build.sh              build into mac/build/
#   mac/build.sh --install    build, then put it in /Applications (replacing an older copy)
#
# Needs the Xcode command line tools (xcode-select --install). The app remembers this project folder and the
# Python that runs it: set JHA_PYTHON to choose another interpreter.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(dirname "$HERE")"
PY="${JHA_PYTHON:-$(command -v python3)}"
APP="$HERE/build/Job Hunter Agent.app"
rm -rf "$APP"; mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
xcrun swiftc -O -swift-version 5 -o "$APP/Contents/MacOS/JobHunterAgent" "$HERE/JobHunterAgent.swift" \
  -framework Cocoa -framework WebKit -framework Speech -framework AVFoundation
cp "$HERE/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
esc() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/[|]/\\|/g'; }
sed -e "s|@REPO@|$(esc "$REPO")|" -e "s|@PYTHON@|$(esc "$PY")|" "$HERE/Info.plist.in" > "$APP/Contents/Info.plist"
codesign --force --deep -s - "$APP"
echo "built $APP"
if [ "${1:-}" = "--install" ]; then
  rm -rf "/Applications/Job Hunter Agent.app"
  cp -R "$APP" /Applications/
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "/Applications/Job Hunter Agent.app"
  echo "installed /Applications/Job Hunter Agent.app"
fi
