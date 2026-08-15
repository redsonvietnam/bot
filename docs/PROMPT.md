# Claude Consultation Prompt: 9router Status Bot Enhancement

## Your Task

Review and provide architecture + implementation recommendations for extending the **9router Status Bot** to display rich event states (SUCCESS, ONBOARDING, TOKEN_EXPIRED) detected from 9router's runtime logs.

**Context Files to Review:**
- `CONTEXT.md` (overall project summary)
- `sidecar/app.py` (current Flask endpoint logic)
- `overlay/router_bot_overlay.py` (current PyQt6 bot)
- `requirements.txt` (dependencies)

---

## Background

### What Exists Today

We have a lightweight desktop overlay bot written in Python that:

1. **Monitors 9router connection status** by reading `db.json` (connection locks, token expiry, test status)
2. **Exposes REST endpoint** `/api/status` via Flask sidecar
3. **Displays animated indicator** using PyQt6 with 4 states:
   - **idle** (blue, gentle bob) — ready, no recent usage
   - **active** (green, bounce) — currently being used
   - **warning** (yellow, flash) — ≥50% connections locked
   - **blocked** (red, shake) — all connections locked

4. **Features:**
   - Drag-and-drop repositioning with saved preferences
   - System tray integration (Show/Hide, Quit)
   - Left-click opens dashboard, double-click hides
   - Real-time polling every 4 seconds
   - Tooltip + on-widget detail text

**Tech Stack:**
- Backend: Flask + Python 3.10+
- Frontend: PyQt6, trigonometric animations (no anime/GSAP)
- Data source: 9router's `db.json`

---

## The Enhancement Request

### New Event Types to Display

From analyzing **9router runtime logs**, Gemini identified 3 new rich event categories:

#### 1. SUCCESS Events
**When:** Google token refresh succeeds for providers (antigravity, gemini-cli)
```
Log: "Successfully refreshed Google token for antigravity. expiresIn: 3599, success: true"
```
**Proposed Animation:** Victory dance
- Bot jumps upward with elastic bounce
- Body scales up/down rhythmically
- Sparkle effects (stars ⭐) around bot

**Proposed Colors:** Bright green (#3CBF6A) with glow

**Duration:** 1.5 seconds, then fade back to normal state

#### 2. ONBOARDING Events (Retry Loop)
**When:** Bot attempts to onboard user to standard-tier project
```
Log: "onboardUser attempt 1/5: Finding project_id..."
     "onboardUser attempt 2/5: Retrying..."
     "onboardUser attempt 5/5: FAILED - no project_id in response"
```
**Proposed Animation:**
- **Attempts 1-4:** Sweating animation (head tilts, water droplets 💧)
- **Failed attempt 5:** Collapse/KO animation (slide down, X eyes ❌, smoke ☁️)

**Proposed Colors:**
- Active retry: Warm orange (#E6AF28) with sweat droplets
- Final fail: Dark red (#991111) or gray (#404040)

**Duration:** Persist until next successful state or manual reset

#### 3. TOKEN_EXPIRED Events
**When:** Auth failure for providers (codex, cline, xai, qoder)
```
Log: "Re-auth required for codex: validation failed"
     "Config missing for cline: token expired"
```
**Proposed Animation:** Glitch effect
- Position jitter/flicker (small random dx/dy every frame)
- Color desaturation
- Warning symbol ⚠️ in face area

**Proposed Colors:** Orange-red (#D85C3C)

**Duration:** Until token refreshed

---

## Design Questions We Need Your Input On

### 1. Data Flow Architecture

**Option A: Extend Flask Sidecar (Reads Logs Directly)**
```
9router runtime
    ↓
[db.json] + [9router.log]
    ↓
[Flask app.py]
├─ Detects SUCCESS (timestamp match on token refresh)
├─ Detects ONBOARDING_RETRY (parse log for "attempt N/5")
├─ Detects TOKEN_EXPIRED (error patterns)
├─ Computes connection status (existing logic)
└─ Returns unified JSON: {"state": "...", "detail": "...", "event_type": "..."}
    ↓
[Bot polls /api/status every 4s]
    ↓
[PyQt6 renders animation based on state]
```

**Option B: Bot Reads Logs Directly**
```
9router runtime
    ↓
[9router.log]
    ↓
[Bot reads + parses log in parallel]
    ↓
[Maps events to local state]
    ↓
[Renders animation]
```

**Recommendation needed:**
- Which approach is cleaner for Windows file access?
- Should we add log tailing library (e.g., `pytailf` or simple polling)?
- What's the 9router log path on Windows? (`%APPDATA%/9router/logs/`?)

---

### 2. State Priority & Conflicts

If multiple events happen in the same 4s polling window:
- SUCCESS + ONBOARDING_RETRY → Show which?
- TOKEN_EXPIRED + blocked → Show which?
- SUCCESS + TOKEN_EXPIRED → Show which?

**Recommend a priority matrix:**
```
BLOCKED > ONBOARDING_FAILED > WARNING > TOKEN_EXPIRED > SUCCESS > ACTIVE > IDLE
```

Or should we show **stacked notifications** (bot cycles through them)?

---

### 3. Event Persistence & State Reset

**Question:** When should bot auto-reset event states?

Examples:
- SUCCESS → show for 1.5s, auto-return to underlying state (idle/active)
- ONBOARDING_FAILED → persist until manual "retry" button or next successful state?
- TOKEN_EXPIRED → persist until token refresh detected in log

**Recommend:** Add configurable TTL (time-to-live) per event type?

---

### 4. Animation Implementation

**Current approach:** Pure trigonometric animations (no sprite sheets, no external animation libs)

For new states, should we:
- **A)** Stick with trig functions (`sin`, `cos`, polynomial easing)
- **B)** Add Lottie JSON file support (lightweight)
- **C)** Use SVG + PyQt SVG renderer
- **D)** Hybrid: trig for motion, SVG for static symbols (stars, droplets)

**Recommend:** Lightest-weight approach that looks good?

---

### 5. Log Parsing Robustness

9router logs might:
- Rotate daily/hourly → need to track file handle
- Have variable format → need regex patterns
- Be written asynchronously → race conditions reading?

**Recommend:**
- Log file paths & naming convention?
- Retry backoff strategy if log temporarily inaccessible?
- Buffering/caching strategy for multi-line events?

---

### 6. Backward Compatibility

**Question:** Should existing 4 states (idle/active/warning/blocked) remain visually unchanged?

Or can we refactor to make room for new animations (e.g., remove "active" state if rarely used)?

---

### 7. MVP Scope

**Start with which events?**
- Option 1: SUCCESS + ONBOARDING states (2 new states, high value)
- Option 2: All 3 (SUCCESS + ONBOARDING + TOKEN_EXPIRED)
- Option 3: Just ONBOARDING_FAILED (highest pain point)

---

## Deliverables We Expect from You

1. **Architecture Decision** — Recommend Option A/B/hybrid with rationale
2. **Event Priority Matrix** — Which state wins if conflicts
3. **State Machine Diagram** — Flow chart of state transitions
4. **Animation Spec** — Pseudocode or math functions for each new animation
5. **Log Parsing Strategy** — Regex patterns + file handling approach
6. **Implementation Roadmap** — Step-by-step guide (3-5 phases)
7. **Test Scenarios** — How to simulate each new event for QA

---

## Constraints & Requirements

- **Python version:** 3.10+
- **Max dependencies:** Only add if absolutely necessary (keep it lightweight)
- **No breaking changes:** Existing 4 states must keep working
- **Windows-first:** Account for Windows paths, file access quirks
- **Performance:** Keep polling latency < 500ms, CPU < 2% idle
- **No external APIs:** Log parsing only, no new network calls

---

## File References

When you review, focus on:

1. **`sidecar/app.py`** (lines to expand):
   - `_compute_status()` — add event detection here?
   - Return JSON structure — add `"event_type"` field?

2. **`overlay/router_bot_overlay.py`** (lines to modify):
   - `STATE_COLORS` dict — add new states?
   - `_offset_for_state()` — implement new animation math?
   - `paintEvent()` — render new symbols (droplets, stars, etc.)?
   - `poll_status()` — handle new response fields?

3. **New files to create:**
   - `log_parser.py` — Event detection + regex patterns?
   - `animations.py` — Centralized animation definitions?
   - `tests/` — Unit tests for log parsing?

---

## Questions for You (Direct Feedback Loop)

After you review, please answer:

1. **Is Option A or Option B better?** Why?
2. **What's the simplest way to add SUCCESS animation without external libs?**
3. **Should ONBOARDING persist as a "sticky" state or auto-reset after N seconds?**
4. **How should we handle 9router log file paths on Windows?**
5. **Recommend a first incremental step (what to build first)?**

---

## Context for Claude: About the User

- **Location:** Vietnam (uses Vietnamese text in logs/UI)
- **Use case:** Monitor 9router connection pool health during API routing
- **Tech level:** Intermediate Python, comfortable with async/threading
- **Preferences:** Lightweight, no heavy dependencies, emphasis on smooth visuals

---

## Attached Files

The user will provide:
- `9router-bot-project.zip` containing:
  ```
  sidecar/app.py
  overlay/router_bot_overlay.py
  requirements.txt
  tests/test_*.py
  docs/CONTEXT.md (this file)
  docs/PROMPT.md (this file)
  sample-logs/ (9router log snippets for analysis)
  ```

---

**End of Prompt**

Please start by:
1. Summarizing the current system
2. Analyzing the proposed new events
3. Recommending architecture + animations
4. Providing specific implementation steps
