#!/usr/bin/env bash
# Desk installer for macOS and Linux. Safe to re-run.
# Usage (from a checkout):  ./install.sh [install-dir]          (default: ~/Desk)
# Usage (one line):         curl -fsSL https://raw.githubusercontent.com/TeebooTed/desk/main/install.sh | bash
#   (the one-line form needs the repo to be public; for a private repo clone it and run ./install.sh)
# Env: DESK_DIR (install dir), DESK_REPO (owner/name), DESK_REF (branch/tag), DESK_NO_OPEN=1
# Never reads, writes or prints the webhook key. Configure it in the Desk page.
# Re-running upgrades the code but never touches your status.json, live.json, layout.json or tiles/.
set -euo pipefail
REPO="${DESK_REPO:-TeebooTed/desk}"; REF="${DESK_REF:-main}"
SRC=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "$(dirname "${BASH_SOURCE[0]}")/template.html" ]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  command -v curl >/dev/null 2>&1 || { echo "curl is required." >&2; exit 1; }
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  echo "Downloading $REPO@$REF…"
  if ! curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$REF" | tar -xz -C "$TMP"; then
    echo "Download failed. If the repo is private, clone it (gh repo clone $REPO) and run ./install.sh instead." >&2; exit 1
  fi
  SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
fi
DEST="${1:-${DESK_DIR:-$HOME/Desk}}"
NO_OPEN="${DESK_NO_OPEN:-0}"
LABEL="local.desk-relay"
command -v python3 >/dev/null 2>&1 || { echo "python3 is required but was not found." >&2; exit 1; }
PY="$(command -v python3)"
mkdir -p "$DEST/relay" "$DEST/assets" "$DEST/docs" "$DEST/examples/tiles"
cp "$SRC/template.html" "$SRC/build.py" "$SRC/example-status.json" "$SRC/example-live.json" "$DEST/"
cp "$SRC/layout.default.json" "$SRC/layout_lib.py" "$DEST/"
cp "$SRC/docs/"*.md "$DEST/docs/" 2>/dev/null || true
cp "$SRC/tiles/"*.json "$DEST/examples/tiles/" 2>/dev/null || true   # copy into $DEST/tiles/ to enable
cp "$SRC/relay/desk-relay.py" "$DEST/relay/"
cp "$SRC/registry.json" "$DEST/" 2>/dev/null || true
mkdir -p "$DEST/examples/widgets" "$DEST/tools" && cp -R "$SRC/examples/widgets/." "$DEST/examples/widgets/" 2>/dev/null || true
cp "$SRC/tools/"*.py "$DEST/tools/" 2>/dev/null || true
cp -R "$SRC/assets/." "$DEST/assets/"
OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
  PL="$HOME/Library/LaunchAgents/$LABEL.plist"; mkdir -p "$(dirname "$PL")"
  cat > "$PL" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>$DEST/relay/desk-relay.py</string></array>
  <key>EnvironmentVariables</key><dict><key>DESK_DIR</key><string>$DEST</string></dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
</dict></plist>
PLIST
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PL"
  echo "Installed LaunchAgent: $PL"
elif [ "$OS" = "Linux" ]; then
  UD="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"; mkdir -p "$UD"
  cat > "$UD/desk-relay.service" <<UNIT
[Unit]
Description=Desk local relay (127.0.0.1:8765)

[Service]
Environment=DESK_DIR=$DEST
ExecStart=$PY $DEST/relay/desk-relay.py
Restart=on-failure

[Install]
WantedBy=default.target
UNIT
  echo "Installed systemd user unit: $UD/desk-relay.service"
  if systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable desk-relay.service >/dev/null 2>&1 || true
    systemctl --user restart desk-relay.service
  else
    echo "systemd user session not available; start the relay manually: DESK_DIR=$DEST nohup $PY $DEST/relay/desk-relay.py >/dev/null 2>&1 &"
    echo "(or add that line to your login startup applications)"
  fi
else
  echo "Unsupported OS: $OS" >&2; exit 1
fi
if [ -f "$DEST/status.json" ]; then "$PY" "$DEST/build.py" "$DEST/status.json" >/dev/null; STATUS="$DEST/status.json"; else "$PY" "$DEST/build.py" >/dev/null; STATUS="$DEST/example-status.json (demo)"; fi
echo "Built $DEST/index.html from $(basename "$STATUS")"
OK=0; for i in 1 2 3 4 5; do
  if "$PY" -c 'import urllib.request,sys;urllib.request.urlopen("http://127.0.0.1:8765/health",timeout=2)' 2>/dev/null; then OK=1; break; fi; sleep 1; done
[ "$OK" = 1 ] && echo "Relay is running on 127.0.0.1:8765" || echo "Warning: relay did not answer on 127.0.0.1:8765 yet."
if [ "$NO_OPEN" != 1 ]; then
  if [ "$OS" = "Darwin" ]; then open "$DEST/index.html"; elif command -v xdg-open >/dev/null; then xdg-open "$DEST/index.html" >/dev/null 2>&1 || true; fi
fi
cat <<NEXT

Next steps:
  1. In Desk, click the gear icon (Connect to your bot).
  2. Paste your Grok Bot webhook URL and key, then Save. The key goes only to the
     local relay (~/.config/desk-relay/config.json); the page never stores it.
  3. Click "Send test". See $DEST/docs/routines.md for the routine prompts.
  4. Tell your bot: "Set up Desk" (prompt in README / docs/bot-template.md).
  5. Or put your own data in $DEST/status.json (see docs/data-format.md) and run:
       python3 $DEST/build.py $DEST/status.json
NEXT
