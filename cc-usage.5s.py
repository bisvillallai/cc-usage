#!/opt/homebrew/bin/python3
# Intel Mac: change shebang to #!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# <swiftbar.title>Claude Code Usage</swiftbar.title>
# <swiftbar.version>1.4.0</swiftbar.version>
# <swiftbar.author>bisvillallai</swiftbar.author>
# <swiftbar.desc>Muestra el uso de Claude Code (5h, weekly, context window)</swiftbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>false</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>false</swiftbar.hideSwiftBar>

import json
import os
import subprocess
import urllib.request
from datetime import datetime

STATE_FILE = os.path.expanduser("~/.claude/.menubar-state.json")
# Solo porcentajes y timestamps; el token OAuth nunca se escribe a disco.
CACHE_FILE = os.path.expanduser("~/.claude/.cc-usage-api.json")
USAGE_URL  = "https://api.anthropic.com/api/oauth/usage"
API_EVERY  = 30        # segundos entre consultas al endpoint
STALE_SECS = 300       # a partir de aquí se avisa que el dato es viejo
WEEK_SECS  = 7 * 86400

# Destello de Claude, PNG 32 px a 144 dpi (16 pt en la barra).
LOGO_PT = 14.45   # 2 × avance de Menlo 12 (7.2246 pt)
CLAUDE_LOGO = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAABYlAAAWJQFJUiTwAAABuklEQVR42t2XzY2EMAyFp4SUQAmUQAnc9koJ3PaaDiiBElJCSuC8J0pICeyO5EjWm+dk+dlB2kOkARL7i/2ceB5fnx+PE6OVcdjGGef+Z2wy/B0AUQHEfw8wSJibOwBG5Wj9hQacrBmuAtCONmXYAgjq/XQFwLPMkjK6qLQgVAewsRYV/fDM7yy7cUQD2nAHzjqiiwzWCjQtWe1kVZMSoZ3V90AAcPeT2EhGVF4AcGKe3Kow6p206reD3QcAZhp6ARiMBXk3DvQwQwR09BZiY4YypiJ0AhKJgZyWgbxfCvDUca0K8iXjQRs5LSWHGSofXJ1UwCQwrgYwg6FoRKTkPBQgQw1g++MRawDrSeN6JBKdvgbgJH9eBJdzOBulusFdMVx1GTWGCFejxtMREOvqjRVlp8L3XREpNRmY2wbmJDI/kMurCFKrABTNCKcjA+7J0axBiiKcyPGrNZHgLogk/0mt80ZEm5IGrFY7kp4gqWfrsOlJStq9PeEIBkZIWYJOaINNNApyOtKURiOEmHsL4HRX7OF2Y6LtZF7ccxjtaaF7YthsNN7xxwQB/N0A4x0A+dgOpJN+C8Dp8Q3PRhq0LhWbfwAAAABJRU5ErkJggg=="

GREEN  = "#30D158"
ORANGE = "#FF9F0A"
RED    = "#FF3B30"
GRAY   = "#8E8E93"
WHITE  = "#F2F2F7"
DIM    = "#AEAEB2"

# SwiftBar solo interpreta ANSI de 256 colores (38;5;n), no truecolor.
ANSI = {GREEN: 77, ORANGE: 214, RED: 203, GRAY: 245, DIM: 250}

def ansi(text, color):
    return f"\033[38;5;{ANSI[color]}m{text}\033[0m"

def color_for(pct):
    if pct is None: return GRAY
    if pct >= 90:   return RED
    if pct >= 70:   return ORANGE
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
    return f"{round(v)}%" if v is not None else "—%"

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

def iso_ts(v):
    try:
        return datetime.fromisoformat(v).timestamp()
    except (TypeError, ValueError):
        return None

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}

def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)

def fetch_usage():
    """Uso de toda la cuenta (CLI, Desktop, web, Design) vía el endpoint de /usage."""
    raw = subprocess.run(
        ["security", "find-generic-password", "-a", os.environ.get("USER", ""),
         "-s", "Claude Code-credentials", "-w"],
        capture_output=True, text=True, timeout=5,
    ).stdout
    oauth = json.loads(raw)["claudeAiOauth"]
    token = oauth["accessToken"]
    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
    })
    data = json.load(urllib.request.urlopen(req, timeout=5))
    return {
        "five_pct":   data["five_hour"]["utilization"],
        "five_reset": iso_ts(data["five_hour"]["resets_at"]),
        "week_pct":   data["seven_day"]["utilization"],
        "week_reset": iso_ts(data["seven_day"]["resets_at"]),
        "plan":       oauth.get("subscriptionType"),
    }

now = datetime.now().timestamp()

# ── Fuente 1: endpoint de uso (cacheado, máx. una consulta cada API_EVERY s) ─
cache = load_json(CACHE_FILE)
if now - cache.get("attempted_at", 0) >= API_EVERY:
    cache["attempted_at"] = now
    try:
        cache.update(fetch_usage(), fetched_at=now, error=None)
    except Exception as e:
        cache["error"] = type(e).__name__
    try:
        write_json(CACHE_FILE, cache)
    except Exception:
        pass

# ── Fuente 2: status line de Claude Code (fallback + contexto de la sesión) ─
state = load_json(STATE_FILE)
state_mtime = os.path.getmtime(STATE_FILE) if os.path.exists(STATE_FILE) else 0
rl = state.get("rate_limits") or {}
line_usage = {}
if rl.get("five_hour") or rl.get("seven_day"):
    line_usage = {
        "five_pct":   (rl.get("five_hour") or {}).get("used_percentage"),
        "five_reset": (rl.get("five_hour") or {}).get("resets_at"),
        "week_pct":   (rl.get("seven_day") or {}).get("used_percentage"),
        "week_reset": (rl.get("seven_day") or {}).get("resets_at"),
        "fetched_at": state_mtime,
    }

# El endpoint manda mientras responda: el status line de una sesión inactiva
# puede reescribirse con rate_limits viejos. Si el endpoint falla, gana el
# dato más reciente de los dos (ambos son uso de la cuenta completa).
if now - cache.get("fetched_at", 0) < STALE_SECS:
    usage = cache
else:
    sources = [u for u in (cache, line_usage) if u.get("fetched_at")]
    usage = max(sources, key=lambda u: u["fetched_at"]) if sources else {}

five_pct   = usage.get("five_pct")
five_reset = usage.get("five_reset")
week_pct   = usage.get("week_pct")
week_reset = usage.get("week_reset")
data_age   = now - usage["fetched_at"] if usage else None

# Si la ventana ya se reinició desde el último dato, el uso real es 0.
if five_reset and five_reset <= now: five_pct, five_reset = 0, None
if week_reset and week_reset <= now: week_pct, week_reset = 0, None

# Contexto: es por conversación, solo tiene sentido si hay una sesión activa.
ctx_pct = None
if now - state_mtime < 90:
    try: ctx_pct = state["context_window"]["used_percentage"]
    except (KeyError, TypeError): pass

# Plan de la cuenta ("pro", "max", …) según las credenciales de Claude Code.
plan_name = (cache.get("plan") or "").capitalize() or "—"

def pace_str(pct, reset):
    """▲n% si vas por encima del ritmo lineal de la semana, ▼n% si vas a favor."""
    if pct is None or reset is None:
        return ""
    elapsed = min(max((now - (reset - WEEK_SECS)) / WEEK_SECS, 0), 1)
    diff = round(pct - elapsed * 100)
    if diff > 0:  return ansi(f"▲{diff}%", ORANGE)
    if diff < 0:  return ansi(f"▼{-diff}%", GREEN)
    return ansi("=", DIM)

def age_str(secs):
    mins = int(secs // 60)
    return f"{mins // 60}h{mins % 60:02d}m" if mins >= 60 else f"{mins}m"

# ── Barra de menú: CC + 5h ──────────────────────────────────────────────────
if five_pct is not None:
    print(f"CC {round(five_pct)}% | color={color_for(five_pct)} font=Menlo-Bold size=12")
else:
    print(f"CC | color={GRAY} font=Menlo-Bold size=12")

print("---")

# ── Línea 1: 5h  ·  Weekly (cada tramo con su propio color) ─────────────────
r1        = reset_str(five_reset)
five_text = f"{circle(five_pct)} 5h {pct_str(five_pct)}" + (f" {r1}" if r1 else "")
five = ansi(five_text, color_for(five_pct))
week = ansi(f"{circle(week_pct)} W {pct_str(week_pct)}", color_for(week_pct))
pace = pace_str(week_pct, week_reset)
sep  = ansi(" · ", DIM)
print(f"{five}{sep}{week}" + (f" {pace}" if pace else "") + " | font=Menlo size=12 ansi=true")

# ── Línea 2: Plan  ·  Context ────────────────────────────────────────────────
# Sin color=: en SwiftBar 2.1.1 (macOS 26+) el hover reescribe las líneas con
# color= y se come la imagen incrustada; el gris va por ANSI, que no se toca.
# Logo a 2 celdas de Menlo 12 + los 2 espacios que SwiftBar le pone = 4 celdas;
# se rellena el plan para que el "·" caiga en la misma columna que arriba.
plan_col = plan_name.ljust(len(five_text) - 4)
plan_ctx = ansi(f"{plan_col} · {circle(ctx_pct)} Ctx {pct_str(ctx_pct)}", DIM)
print(f"{plan_ctx} | font=Menlo size=12 ansi=true image={CLAUDE_LOGO} width={LOGO_PT} height={LOGO_PT}")

# ── Aviso si el dato es viejo (p. ej. token expirado sin usar Claude Code) ──
if data_age is not None and data_age > STALE_SECS:
    hint = " · abre Claude Code para renovar sesión" if cache.get("error") else ""
    print(f"⚠ datos de hace {age_str(data_age)}{hint} | font=Menlo size=11 color={ORANGE}")
