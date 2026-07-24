#!/usr/bin/env bash
#
# cc-usage installer / updater
#
# Run from the repo root after cloning OR after a `git pull`:
#
#   ./install.sh            # menu bar + terminal status line
#   ./install.sh --silent   # menu bar only (no terminal status line)
#
# Idempotent: safe to re-run any time to pick up updates.
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SILENT=0
for arg in "${@:-}"; do
  case "$arg" in
    --silent) SILENT=1 ;;
    "") ;;
    *) echo "Unknown option: $arg (use --silent for menu-bar-only)" >&2; exit 1 ;;
  esac
done

say() { printf '  %s\n' "$1"; }

echo "==> Checking prerequisites"
command -v brew >/dev/null 2>&1 || { echo "Homebrew is required: https://brew.sh"; exit 1; }
command -v jq   >/dev/null 2>&1 || { say "Installing jq...";       brew install jq; }
[ -d /Applications/SwiftBar.app ] || { say "Installing SwiftBar..."; brew install --cask swiftbar; }

PYBIN="$(brew --prefix)/bin/python3"
[ -x "$PYBIN" ] || { say "Installing python..."; brew install python; PYBIN="$(brew --prefix)/bin/python3"; }
say "Python: $PYBIN"

echo "==> Installing SwiftBar plugin"
PLUGDIR="$(defaults read com.ameba.SwiftBar PluginDirectory 2>/dev/null || true)"
if [ -z "$PLUGDIR" ]; then
  PLUGDIR="$HOME/.swiftbar"
  defaults write com.ameba.SwiftBar PluginDirectory "$PLUGDIR"
fi
mkdir -p "$PLUGDIR"

# Copy plugin and rewrite the shebang to THIS machine's python (Apple Silicon / Intel).
plugin_dst="$PLUGDIR/cc-usage.5s.py"
tmp="$(mktemp)"
{ echo "#!$PYBIN"; tail -n +2 "$REPO_DIR/cc-usage.5s.py"; } > "$tmp"
mv "$tmp" "$plugin_dst"
chmod +x "$plugin_dst"
say "Plugin: $plugin_dst"

echo "==> Installing Claude Code status line hook"
mkdir -p "$HOME/.claude"
cp "$REPO_DIR/statusline-command.sh" "$HOME/.claude/statusline-command.sh"
chmod +x "$HOME/.claude/statusline-command.sh"

SETTINGS="$HOME/.claude/settings.json"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
tmp="$(mktemp)"
jq '. + {statusLine: {type: "command", command: "bash ~/.claude/statusline-command.sh"}}' \
  "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
say "Merged statusLine into $SETTINGS"

if [ "$SILENT" -eq 1 ]; then
  touch "$HOME/.claude/.cc-usage-silent"
  say "Silent mode ON — menu bar only (no terminal status line)"
else
  rm -f "$HOME/.claude/.cc-usage-silent"
  say "Terminal status line ENABLED (re-run with --silent to disable)"
fi

echo "==> Starting SwiftBar"
open -a SwiftBar 2>/dev/null || true
sleep 1
open "swiftbar://refreshallplugins" 2>/dev/null || true

echo "==> Registering SwiftBar as a login item"
# SwiftBar's internal launch-at-login preference does not survive machine
# migrations; an explicit login item does.
if osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null | grep -q "SwiftBar"; then
  say "SwiftBar already in Login Items"
elif osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/SwiftBar.app", hidden:false}' >/dev/null 2>&1; then
  say "SwiftBar added to Login Items"
else
  say "Could not register login item — add SwiftBar manually in System Settings > General > Login Items"
fi

echo
echo "Done. Look for 'CC %' in the macOS menu bar."
echo "Terminal status line appears in NEW Claude Code sessions."
