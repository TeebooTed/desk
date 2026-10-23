#!/usr/bin/env bash
# Stops and removes the Desk relay service. Safe to re-run.
# Usage: ./uninstall.sh [install-dir] [--purge]
#   --purge also deletes the install dir and ~/.config/desk-relay (your saved webhook settings).
set -euo pipefail
DEST="$HOME/Desk"; PURGE=0
for a in "$@"; do case "$a" in --purge) PURGE=1;; *) DEST="$a";; esac; done
LABEL="local.desk-relay"
if [ "$(uname -s)" = "Darwin" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
else
  systemctl --user disable --now desk-relay.service >/dev/null 2>&1 || true
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/desk-relay.service"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
fi
echo "Relay service removed."
if [ "$PURGE" = 1 ]; then rm -rf "$DEST" "$HOME/.config/desk-relay"; echo "Removed $DEST and saved relay settings."
else echo "Kept $DEST and ~/.config/desk-relay (use --purge to remove)."; fi
