# 9router Status Bot - Project Context & Enhancement Proposal

## 📋 Current Status

### What We Have Built
A lightweight desktop overlay bot for 9router that monitors connection status in real-time.

**Architecture:**
- **Flask Sidecar** (`app.py`): Reads 9router's `db.json`, exposes `/api/status` endpoint (< 500ms response)
- **PyQt6 Desktop Bot** (`router_bot_overlay.py`): Polls sidecar every 4s, displays animated status indicator with tray integration

**Current States:**
| State | Color | Animation | Use Case |
|-------|-------|-----------|----------|
| `idle` | Blue | Gentle bob | Ready, no recent usage |
| `active` | Green | Bounce + pulse | Recently used connections |
| `warning` | Yellow | Flashing opacity | ≥50% connections locked/partial |
| `blocked` | Red | Shake/tremor | 0 free connections (rate-limited) |
| `offline` | Gray | Slight move | Cannot reach sidecar |

**Features:**
- ✅ Drag & drop repositioning (position saved)
- ✅ System tray icon (Show/Hide, Quit)
- ✅ Left-click opens dashboard
- ✅ Double-click to hide
- ✅ Real-time status polling
- ✅ Tooltip + on-widget detail display

---

## 🎯 Enhancement Proposal (Based on Gemini Analysis)

### New Event Types from 9router Logs

**Problem:** Current bot only reflects connection lock/availability. But 9router logs show rich event lifecycle:
1. **SUCCESS** — Token refresh successful (antigravity, gemini-cli)
2. **ONBOARDING_RETRY** — Attempting to onboard user to standard-tier (attempt 1-5)
3. **ONBOARDING_FAILED** — Failed after 5 retries, project_id not found
4. **TOKEN_EXPIRED** — Auth failures (codex, cline, xai, qoder)

### Proposed New States

| Event | State Name | Animation | Color | Effect | Intent |
|-------|-----------|-----------|-------|--------|--------|
| Token refresh success | `SUCCESS` | Victory dance (jump + scale pop) | Bright Green | Stars ⭐ sparkle around bot | Celebrate successful token refresh |
| Onboard attempt 1-4 | `ONBOARDING_RETRY` | Sweating (head tilt + droplets) | Warm Orange | Question marks `?` linger | Bot is trying, show effort |
| Onboard fail after 5 | `ONBOARDING_FAILED` | Collapse (slide down) | Dark Red/Gray | Eyes `X X`, smoke puff ☁️ | Bot "knocked out", needs help |
| Token invalid | `TOKEN_EXPIRED` | Glitch flicker (position jitter) | Orange-Red | Warning symbol ⚠️ | Auth issue, needs manual intervention |

---

## 🔄 Implementation Strategy

### Option A: Extend Flask Sidecar (Recommended)
**Pros:**
- Centralized logic parsing
- One source of truth for state
- Bot remains simple (just displays what API sends)
- No file permission issues on Windows

**Approach:**
```
app.py reads db.json + 9router log file
├─ Detects SUCCESS events (token refresh timestamps)
├─ Detects ONBOARDING_RETRY loops (onboardUser attempt counter)
├─ Detects ONBOARDING_FAILED (after 5 failures)
├─ Detects TOKEN_EXPIRED (auth error patterns)
└─ Returns enriched JSON: {"state": "...", "detail": "...", "event": "..."}

router_bot_overlay.py polls /api/status
├─ Maps state → animation + color
├─ Renders new animations based on state
└─ Shows event detail in tooltip/widget
```

### Option B: Bot Reads Log Directly
**Pros:**
- Lighter sidecar
- Immediate feedback to bot

**Cons:**
- More complex in bot code
- File access conflicts on Windows
- Harder to track multi-event sequences

---

## 📁 File Structure for Handoff

```
9router-bot-project/
├── CONTEXT.md                    (this file - for Claude context)
├── PROMPT.md                     (detailed prompt for Claude)
├── requirements.txt              (dependencies)
├── sidecar/
│   └── app.py                    (Flask /api/status endpoint)
├── overlay/
│   └── router_bot_overlay.py     (PyQt6 desktop bot)
├── tests/
│   ├── test_blocked.py
│   ├── test_warning.py
│   └── test_restore_idle.py
└── docs/
    ├── animation_spec.md         (animation equations)
    └── state_machine.md          (state transition diagram)
```

---

## ❓ Questions for Claude

1. **Log Parsing Strategy:** Should Flask sidecar parse 9router logs directly, or should we add a separate log-monitoring module?

2. **Event Persistence:** When bot shows "ONBOARDING_FAILED" state, how long should it persist? Auto-reset after 60s or wait for user manual reset?

3. **Multi-Event Handling:** If SUCCESS + ONBOARDING_RETRY happen within same 4s poll window, which state wins priority?

4. **Animation Details:**
   - Should "victory dance" include emoji particles (stars ⭐) or just motion?
   - Should "sweating" show actual water droplets (🌧️) or just visual jitter?
   - Should "knocked out" animate a "Help!" sign or just color + position?

5. **Backward Compatibility:** Keep existing 4 states (idle/active/warning/blocked) fully functional, or introduce breaking changes?

6. **Log File Path:** Assume 9router logs to `%APPDATA%/9router/logs/` or configurable path?

7. **MVP vs Full:** Start with just ONBOARDING states + SUCCESS (3 new states), or include TOKEN_EXPIRED too (4 new)?

---

## 🚀 Next Steps (After Claude Review)

1. Claude analyzes context + proposes refined approach
2. Implement chosen strategy (likely Option A: extend Flask sidecar)
3. Add animation frames for new states
4. Update bot state machine
5. Test with simulated logs
6. Update documentation

---

## 📊 Current Metrics

- **Sidecar latency:** < 50ms (read db.json + compute)
- **Bot polling interval:** 4000ms (configurable)
- **Memory footprint:** ~80MB (PyQt6 overhead)
- **CPU:** <1% idle
- **Python version:** 3.10+

---

## 🎨 Animation Math Examples

Current animations use simple trigonometric functions (no external animation libs):

```python
# Idle: gentle bob
dy = math.sin(self._t * 1.5) * 3  # 3px amplitude, 1.5 rad/s frequency

# Active: bounce + scale pulse
dy = math.sin(self._t * 5) * 4
scale = 1.0 + 0.03 * math.sin(self._t * 5)

# Warning: flashing opacity
opacity = 0.6 + 0.4 * abs(math.sin(self._t * 4))

# Blocked: shake
dx = math.sin(self._t * 25) * 2.5  # 2.5px amplitude, high frequency
```

New states can follow same pattern for smooth, lightweight animations.

---

## 💬 Contact & Questions

Ask Claude to review this context and provide:
- Architecture recommendations (Option A vs B)
- Animation implementation details
- State machine diagram
- Log parsing strategy
- Test scenarios for new states
