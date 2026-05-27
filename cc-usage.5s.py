#!/opt/homebrew/bin/python3
# Intel Mac: change shebang to #!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# <swiftbar.title>Claude Code Usage</swiftbar.title>
# <swiftbar.version>1.2.0</swiftbar.version>
# <swiftbar.author>bisvillallai</swiftbar.author>
# <swiftbar.desc>Muestra el uso de Claude Code (5h, weekly, context window)</swiftbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>false</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>false</swiftbar.hideSwiftBar>

import json
import os
from datetime import datetime

STATE_FILE = os.path.expanduser("~/.claude/.menubar-state.json")

GREEN  = "#30D158"
ORANGE = "#FF9F0A"
RED    = "#FF3B30"
GRAY   = "#8E8E93"
WHITE  = "#F2F2F7"
DIM    = "#AEAEB2"

def color_for(pct):
    if pct is None: return GRAY
    if pct >= 90:   return RED
    if pct >= 70:   return ORANGE
    return GREEN

def worst_color(*pcts):
    valid = [p for p in pcts if p is not None]
    if not valid:                       return GRAY
    if any(p >= 90 for p in valid):    return RED
    if any(p >= 70 for p in valid):    return ORANGE
    return GREEN

# ○ ◔ ◑ ◕ ●  — círculo vacío → lleno conforme sube el uso
def circle(pct):
    if pct is None: return "○"
    if pct >= 88:   return "●"
    if pct >= 63:   return "◕"
    if pct >= 38:   return "◑"
    if pct >= 13:   return "◔"
    return "○"

def pct_str(v):
    return f"{round(v):>3}%" if v is not None else "  —%"

def reset_str(ts):
    """Tiempo restante hasta ts: '1h40m' si ≥1h, '40m' si <1h, '' si ya pasó."""
    if ts is None:
        return ""
    secs = int(ts - datetime.now().timestamp())
    if secs <= 0:
        return ""
    mins = secs // 60
    if mins >= 60:
        return f"↺{mins // 60}h{mins % 60:02d}m"
    return f"↺{mins}m"

# ── Leer state file ──────────────────────────────────────────────────────────
state       = {}
last_update = None
is_active   = False

if os.path.exists(STATE_FILE):
    try:
        mtime       = os.path.getmtime(STATE_FILE)
        last_update = datetime.fromtimestamp(mtime)
        is_active   = (datetime.now() - last_update).total_seconds() < 90
        with open(STATE_FILE) as f:
            state = json.load(f)
    except Exception:
        pass

five_pct    = None
five_reset  = None   # Unix timestamp
week_pct    = None
ctx_pct     = None
plan_name   = "Claude Max"

try: five_pct   = state["rate_limits"]["five_hour"]["used_percentage"]
except (KeyError, TypeError): pass

try: five_reset = state["rate_limits"]["five_hour"]["resets_at"]
except (KeyError, TypeError): pass

try: week_pct = state["rate_limits"]["seven_day"]["used_percentage"]
except (KeyError, TypeError): pass

try: ctx_pct = state["context_window"]["used_percentage"]
except (KeyError, TypeError): pass

for path in [["plan","name"],["subscription","plan"],["rate_limits","plan"],["billing","plan_name"]]:
    try:
        v = state
        for k in path: v = v[k]
        if isinstance(v, str) and v:
            plan_name = v
            break
    except (KeyError, TypeError):
        pass

# ── Barra de menú: CC + 5h ──────────────────────────────────────────────────
if five_pct is not None:
    print(f"CC {round(five_pct)}% | color={color_for(five_pct)} font=Menlo-Bold size=12")
else:
    print(f"CC | color={GRAY} font=Menlo-Bold size=12")

print("---")

# ── Línea 1: 5h  ·  Weekly ──────────────────────────────────────────────────
c1  = circle(five_pct)
c2  = circle(week_pct)
p1  = pct_str(five_pct)
p2  = pct_str(week_pct)
r1  = reset_str(five_reset)
col1 = worst_color(five_pct, week_pct)
five_col = f" {r1}" if r1 else ""
print(f"{c1} 5h {p1}{five_col}   ·   {c2} Week {p2} | font=Menlo size=12 color={col1}")

# ── Línea 2: Plan  ·  Context ────────────────────────────────────────────────
c3 = circle(ctx_pct)
p3 = pct_str(ctx_pct)
print(f"📋 {plan_name}   ·   {c3} Ctx {p3} | font=Menlo size=11 color={DIM}")
