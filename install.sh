#!/bin/bash
# Job Hunter Agent: one-time setup on macOS or Linux.
#
#   ./install.sh
#
# It installs the Python packages and the browser the agent fills forms in, creates your private folders (profile/
# and .env, never published), and puts Job Hunter Agent in Applications with its icon (on a Mac), or a menu entry
# (on Linux). Then it opens the app, whose Setup page walks you through the rest.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
say() { printf '  %s\n' "$1"; }
printf '\nJob Hunter Agent · setup\n\n'

# 1 · Python 3.10 or newer
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then PY="$(command -v "$c")"; break; fi
done
if [ -z "$PY" ]; then
  say "Python 3.10 or newer is needed. On a Mac: brew install python, or https://www.python.org/downloads/ . Then run this again."
  exit 1
fi
say "Python: $PY"

# 2 · a private Python environment for the agent, its packages, and the browser it fills forms in
[ -x .venv/bin/python ] || { say "Creating .venv…"; "$PY" -m venv .venv; }
VPY="$ROOT/.venv/bin/python"
say "Installing packages (a few minutes the first time)…"
"$VPY" -m pip install --quiet --upgrade pip
"$VPY" -m pip install --quiet -r requirements.txt
say "Installing the browser the agent fills forms in…"
"$VPY" -m playwright install chromium

# 3 · your private folders: profile/ (your storybook, empty) and .env (settings); nothing here is ever published
"$VPY" -m agent.run init

# 4 · the app
if [ "$(uname)" = "Darwin" ]; then
  if ! xcrun --find swiftc >/dev/null 2>&1; then
    say "Building the Mac app needs Apple's command line tools. A window will ask to install them; run ./install.sh again after."
    xcode-select --install || true
    exit 1
  fi
  JHA_PYTHON="$VPY" mac/build.sh --install
  printf '\nDone. Opening Job Hunter Agent: its Setup page shows what is left (a model, your standing answers, your storybook).\n\n'
  open -a "Job Hunter Agent"
else
  mkdir -p "$HOME/.local/share/applications"
  cat > "$HOME/.local/share/applications/job-hunter-agent.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Job Hunter Agent
Exec="$VPY" -m dashboard.launcher %u
Path=$ROOT
Icon=$ROOT/docs/brand/app-icon/icon-1024.png
MimeType=x-scheme-handler/jobhunter;
Categories=Office;
DESKTOP
  command -v xdg-mime >/dev/null && xdg-mime default job-hunter-agent.desktop x-scheme-handler/jobhunter || true
  printf '\nDone. Job Hunter Agent is in your applications menu; opening it now.\n\n'
  (cd "$ROOT" && nohup "$VPY" -m dashboard.launcher >/dev/null 2>&1 &)
fi
