# 9router Status Bot - Desktop Overlay Monitor

A lightweight Python desktop application that monitors 9router connection pool health with animated visual indicators.

## 📦 What's Included

### Current Implementation
- **Sidecar Service** (`sidecar/app.py`): Flask endpoint reading 9router's `db.json`
- **Desktop Bot** (`overlay/router_bot_overlay.py`): PyQt6 desktop widget with system tray integration
- **Test Suite** (`tests/`): Simulated state scenarios (blocked, warning, idle)
- **Documentation** (`docs/`): Context + enhancement proposal

### Current Features
✅ Real-time connection pool monitoring  
✅ 4-state animation (idle, active, warning, blocked)  
✅ Drag & drop repositioning with saved preferences  
✅ System tray integration (Show/Hide, Quit)  
✅ Fast polling (< 500ms response)  
✅ Lightweight (PyQt6 only, no heavy deps)  

---

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Running
Terminal 1 - Start sidecar:
```bash
python sidecar/app.py
```

Terminal 2 - Start bot:
```bash
python overlay/router_bot_overlay.py
```

### Testing
Simulate status changes:
```bash
python tests/test_blocked.py      # 23/23 connections locked → RED
python tests/test_warning.py      # 12/23 connections locked → YELLOW
python tests/test_restore_idle.py # All free → BLUE
```

---

## 📚 Documentation

- **`docs/CONTEXT.md`** — Project overview, current architecture, enhancement proposal
- **`docs/PROMPT.md`** — Detailed consultation prompt for Claude (code review + recommendations)

---

## 🎨 Current Animation States

| State | Color | Animation | Meaning |
|-------|-------|-----------|---------|
| **idle** | Blue | Gentle bobbing | Ready, no recent usage |
| **active** | Green | Bounce + pulse | Currently being used |
| **warning** | Yellow | Flashing opacity | ≥50% connections locked |
| **blocked** | Red | Shake/tremor | 0 free connections (rate-limited) |
| **offline** | Gray | Slight drift | Cannot reach sidecar |

---

## 🔧 Configuration

### Sidecar
Edit `sidecar/app.py`:
```python
DB_JSON_PATH = "..."          # Path to 9router db.json
ACTIVE_WINDOW_SEC = 30        # Recent activity window
WARNING_LOCKED_RATIO = 0.5    # Warning threshold (50%)
```

### Bot
Edit `overlay/router_bot_overlay.py`:
```python
STATUS_API_URL = "http://127.0.0.1:5000/api/status"
POLL_INTERVAL_MS = 4000       # Poll every 4 seconds
CONFIG_PATH = "~/.9router_bot/config.json"  # Position save
BOT_SIZE = 72                 # Widget size (px)
```

---

## 📡 API Contract

### GET `/api/status`
Returns connection pool status.

**Response:**
```json
{
  "state": "idle|active|warning|blocked|offline",
  "detail": "San sang - 19/23 connections kha dung"
}
```

**States:**
- `idle` — Ready, no activity in last 30s
- `active` — Recent usage detected
- `warning` — ≥50% connections locked/partial
- `blocked` — All connections locked (rate-limited)
- `offline` — Cannot read db.json or sidecar down

---

## 💡 Enhancement Proposal

The included `docs/PROMPT.md` outlines expansion to display rich event states:

- **SUCCESS** — Token refresh succeeded → Victory dance animation
- **ONBOARDING_RETRY** — User onboarding loop → Sweating animation
- **ONBOARDING_FAILED** — Failed after 5 attempts → KO/collapse animation
- **TOKEN_EXPIRED** — Auth failure → Glitch effect animation

**Status:** Awaiting Claude review & architecture recommendation

---

## 📊 Performance

- **Sidecar latency:** < 50ms (read + compute)
- **Polling interval:** 4000ms (configurable)
- **Memory:** ~80MB (PyQt6)
- **CPU:** < 1% idle
- **Python:** 3.10+

---

## 🎯 Next Steps

1. Review `docs/PROMPT.md` with Claude for architecture recommendations
2. Implement chosen event detection strategy (Option A: Flask logs parsing)
3. Add 3 new animation states (SUCCESS, ONBOARDING, TOKEN_EXPIRED)
4. Extend test suite with new event simulation
5. Performance profiling + optimization

---

## 📝 Notes

- **Windows-first:** Developed for Windows 10/11
- **9router integration:** Read-only (no modifications to 9router config/logic)
- **Log format:** Expects 9router's standard `db.json` structure
- **Animation:** Pure trigonometric functions (no external animation libs)

---

## 🔗 Related Files

- 9router docs: (external)
- PyQt6 docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Flask docs: https://flask.palletsprojects.com/

---

**Created:** August 2026  
**Maintained by:** Development team  
**Status:** Active + Enhancement phase
