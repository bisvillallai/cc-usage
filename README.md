# cc-usage — Claude Code usage in your macOS menu bar

A [SwiftBar](https://github.com/swiftbar/SwiftBar) plugin that surfaces your Claude Code session stats directly in the macOS status bar.

**Status bar:**
```
CC 68%
```

**On click:**
```
◕ 5h  68% ↺1h12m   ·   ◑ Week  41%
📋 Claude Max   ·   ◔ Ctx  30%
```

- **5h** — current 5-hour rate limit usage, with countdown to reset
- **Week** — 7-day usage across all models
- **Ctx** — context window usage for the active session
- Color: green < 70% · orange 70–89% · red ≥ 90%
- Circle indicator: ○ ◔ ◑ ◕ ● fills as usage climbs

---

## Requirements

| Tool | Install |
|------|---------|
| SwiftBar | `brew install --cask swiftbar` |
| Python 3.10+ | `brew install python` |
| jq | `brew install jq` |
| Claude Code | [claude.ai/code](https://claude.ai/code) |

> **Intel Mac:** open `cc-usage.5s.py` and change the first line to `#!/usr/local/bin/python3`

---

## Installation

### Quick install (recommended)

From the repo root:

```bash
./install.sh            # menu bar + terminal status line
./install.sh --silent   # menu bar only (no terminal status line)
```

It installs any missing dependencies (SwiftBar, Python, jq), copies the plugin
and hook into place, rewrites the Python shebang for your Mac (Apple Silicon /
Intel), merges the `statusLine` key into `~/.claude/settings.json`, and launches
SwiftBar. **Re-run it after every `git pull`** to update. Open a *new* Claude
Code session to see the terminal status line.

Toggle silent mode later without re-running:

```bash
touch ~/.claude/.cc-usage-silent   # menu bar only
rm    ~/.claude/.cc-usage-silent   # show terminal status line again
```

### Manual install (alternative)

### 1. Configure SwiftBar

Open SwiftBar, choose a plugins directory (e.g. `~/.swiftbar`).

### 2. Copy the plugin

```bash
cp cc-usage.5s.py "$(defaults read com.ameba.SwiftBar PluginDirectory)"
```

### 3. Set up the Claude Code statusline hook

Copy the hook script:

```bash
cp statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

Add this to `~/.claude/settings.json` (create the file if it doesn't exist):

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  }
}
```

> If `settings.json` already exists, merge the `statusLine` key into it — don't replace the whole file.

### 4. Refresh SwiftBar

Click the SwiftBar icon → **Refresh All Plugins**.

The plugin shows `CC —` until you start a Claude Code session. Stats appear once Claude Code writes its first status update.

---

## How it works

Claude Code calls the `statusLine` command after every interaction, piping a JSON payload with session state (model, rate limits, context window, etc.).

`statusline-command.sh` persists that payload to `~/.claude/.menubar-state.json`.

`cc-usage.5s.py` reads that file every 5 seconds and formats it for SwiftBar.

No network calls. No tokens stored. All data stays local.

---

## Files

| File | Purpose |
|------|---------|
| `install.sh` | One-command installer / updater (`--silent` for menu-bar-only) |
| `cc-usage.5s.py` | SwiftBar plugin (refreshes every 5 s) |
| `statusline-command.sh` | Claude Code hook — persists state + formats terminal status line |

> **Silent mode:** create `~/.claude/.cc-usage-silent` to feed the menu bar only
> and suppress the terminal status line (per-machine, not versioned).
