# Quick Reference - 9router Bot Enhancement Project

## 📦 What You Have

**File:** `9router-bot-project.zip` (18.5 KB)

**Contains:**
```
sidecar/
  └─ app.py                 (Flask /api/status endpoint)
overlay/
  └─ router_bot_overlay.py  (PyQt6 desktop bot)
tests/
  ├─ test_blocked.py
  ├─ test_warning.py
  └─ test_restore_idle.py
docs/
  ├─ CONTEXT.md            (Project overview + enhancement proposal)
  ├─ PROMPT.md             (7 design questions for Claude)
  └─ sample-logs/events.log
README.md
requirements.txt
```

---

## 🎯 What to Send Claude

**Step 1:** Extract ZIP
```bash
unzip 9router-bot-project.zip
cd 9router-bot-project
```

**Step 2:** Send to Claude with this intro:

```
I've developed a lightweight desktop monitoring bot for 9router (Python + PyQt6).

**Current state:**
- Reads 9router connection pool status from db.json
- Flask sidecar exposes /api/status endpoint (< 500ms)
- PyQt6 desktop widget with 4 animation states (idle/active/warning/blocked)
- System tray integration, drag-and-drop repositioning
- Real-time polling every 4 seconds

**New requirement:**
- Extend bot to display rich event states from 9router runtime logs:
  - SUCCESS: Token refresh succeeded
  - ONBOARDING_RETRY: User onboarding loop (attempt 1-5)
  - ONBOARDING_FAILED: Failed after 5 retries
  - TOKEN_EXPIRED: Auth failure

**What I need from you:**
Please review the attached project and provide:
1. Architecture recommendation (Flask parses logs vs bot parses logs?)
2. State priority matrix (which event wins if multiple occur?)
3. Animation implementation details (new motion equations)
4. Log parsing strategy (regex patterns, file handling)
5. Implementation roadmap (phase breakdown)
6. Test scenarios (how to simulate each event)

Here's the full consultation prompt:
[PASTE ENTIRE docs/PROMPT.md HERE]
```

**Step 3:** Attach the ZIP file

---

## 🎨 New Animation States (What Claude Will Design)

| Event | Color | Animation | Icon |
|-------|-------|-----------|------|
| SUCCESS | Bright Green | Jump + scale pulse | ⭐ Stars sparkle |
| ONBOARDING_RETRY | Warm Orange | Head tilt + sweat | 💧 Droplets |
| ONBOARDING_FAILED | Dark Red | Collapse/slide down | ❌ Eyes X X |
| TOKEN_EXPIRED | Orange-Red | Position glitch | ⚠️ Warning |

---

## 💬 Claude's Key Decision Points

### 1. Where Should Event Detection Happen?

**Option A: Flask Sidecar**
```
9router → db.json + logs
    ↓
app.py (reads logs, detects events)
    ↓
/api/status returns: {"state": "...", "event": "..."}
    ↓
Bot displays animation
```

**Option B: Bot Reads Logs**
```
9router → logs
    ↓
Bot reads + parses logs
    ↓
Bot maps to local state
    ↓
Bot renders animation
```

*Claude needs to recommend which for Windows file access robustness*

### 2. Animation Implementation

Use existing trig functions or add new library?

**Current approach:**
```python
# Idle: gentle bob
dy = math.sin(self._t * 1.5) * 3

# Active: bounce + pulse
dy = math.sin(self._t * 5) * 4
scale = 1.0 + 0.03 * math.sin(self._t * 5)
```

*Claude needs to provide similar math for SUCCESS/ONBOARDING/TOKEN_EXPIRED*

### 3. State Conflicts

If multiple events in same poll window:
- BLOCKED > ONBOARDING_FAILED > WARNING > TOKEN_EXPIRED > SUCCESS > ACTIVE > IDLE?
- Or show multiple stacked?

*Claude needs to provide priority matrix*

---

## 🔧 Project Structure After Claude Review

**Expected additions:**

```
sidecar/
  ├─ app.py                    (MODIFY: add event detection)
  ├─ log_parser.py             (NEW: event detection logic)
  └─ event_patterns.py         (NEW: regex patterns)

overlay/
  ├─ router_bot_overlay.py     (MODIFY: add animations)
  ├─ animations.py             (NEW: animation specs)
  └─ state_machine.py          (NEW: state transitions)

tests/
  ├─ test_success_event.py      (NEW)
  ├─ test_onboarding_retry.py   (NEW)
  ├─ test_token_expired.py      (NEW)
  └─ [existing tests]

docs/
  ├─ IMPLEMENTATION_PLAN.md     (NEW: from Claude)
  ├─ STATE_MACHINE.md           (NEW: from Claude)
  ├─ ANIMATION_SPEC.md          (NEW: from Claude)
  └─ [existing docs]
```

---

## 🚀 Implementation Phases (Predicted)

**Phase 1:** Event Detection
- Add log file monitoring to Flask sidecar
- Parse SUCCESS events (token refresh)
- Test with sample logs

**Phase 2:** SUCCESS Animation
- Add animation math for victory dance
- Update paintEvent() to render new motion
- Test state transitions

**Phase 3:** ONBOARDING Animations
- Parse onboardUser attempt logs
- Implement sweating animation (retry)
- Implement collapse animation (fail)
- Add event persistence logic

**Phase 4:** TOKEN_EXPIRED & Polish
- Add glitch animation
- Priority conflict resolution
- UI polish (symbols, colors)
- Performance tuning

**Phase 5:** Testing & Release
- Integration tests
- Edge case handling
- Documentation update

---

## 📊 Current Metrics

| Metric | Value |
|--------|-------|
| Sidecar latency | < 50ms |
| Polling interval | 4000ms |
| Memory (idle) | ~80MB |
| CPU (idle) | < 1% |
| Python version | 3.10+ |
| Frameworks | Flask 3.1.3, PyQt6 6.11.0 |

---

## 🎓 Gemini's Original Observation

> From 9router logs, 3 new event categories emerged:
> 1. **SUCCESS** — Token refresh succeeded (antigravity, gemini-cli)
> 2. **ONBOARDING** — Retry loop for standard-tier project (1-5 attempts)
> 3. **FAILED** — Failed after 5 attempts, needs manual intervention
> 4. **TOKEN_EXPIRED** — Auth failures for multiple providers

This drives the entire enhancement request.

---

## ✅ Validation Checklist

**Before sending ZIP to Claude, verify:**
- [ ] `docs/PROMPT.md` has 7 clear questions
- [ ] `docs/CONTEXT.md` has background info
- [ ] `sample-logs/events.log` shows all event types
- [ ] Source code is formatted + commented
- [ ] `requirements.txt` is complete
- [ ] Test files run successfully
- [ ] README explains setup + usage
- [ ] ZIP extracts to clean structure

---

## 🎬 After Claude Responds

1. **Save Claude's response** with:
   - Architecture recommendation
   - Animation specifications
   - Implementation roadmap
   - Test scenarios

2. **Create new files based on Claude's guidance:**
   - `log_parser.py` with event detection
   - `animations.py` with new animation math
   - `state_machine.py` with state transitions

3. **Modify existing files:**
   - `sidecar/app.py` — call event detection
   - `overlay/router_bot_overlay.py` — render new animations

4. **Run test suite** to validate each phase

5. **Performance profile** to ensure < 2% CPU idle

---

## 📞 Questions Claude Will Likely Ask

- What's the exact log file path on Windows?
- How should event TTL (time-to-live) be handled?
- Should events persist across bot restarts?
- What's the user's preference for animation complexity?
- Do we need event logging/debugging mode?
- Should animations be configurable?
- Any accessibility requirements?

*Be ready with these answers after Claude asks*

---

## 🏁 Success Criteria (After Implementation)

- ✅ SUCCESS event triggers victory dance animation
- ✅ ONBOARDING_RETRY persists until success or fail
- ✅ ONBOARDING_FAILED shows collapse animation
- ✅ TOKEN_EXPIRED shows glitch effect
- ✅ State priorities respected (no conflicts)
- ✅ Response time still < 500ms
- ✅ CPU usage < 2% idle
- ✅ All test scenarios pass
- ✅ Documentation updated
- ✅ User reports smooth, responsive animations

---

**Ready to send to Claude!** 🚀

All files prepared in `9router-bot-project.zip`.

Just extract + paste PROMPT.md content to Claude + attach ZIP.
