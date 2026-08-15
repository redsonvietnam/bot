# 📦 9router Status Bot - Claude Consultation Package

## What You're Getting

Complete project package for Claude review + architecture recommendations on extending the 9router Status Bot with rich event animations.

---

## 📁 Package Contents

### Main Files to Read First
1. **`docs/PROMPT.md`** ← START HERE
   - Detailed consultation prompt for Claude
   - 7 key questions for architecture decisions
   - Expected deliverables clearly defined

2. **`docs/CONTEXT.md`** ← Read second
   - Project overview & current implementation
   - Enhancement proposal with new event types
   - Animation examples
   - Questions for Claude

3. **`README.md`** ← Quick reference
   - Project summary
   - Quick start guide
   - Current features & API contract

### Source Code
- `sidecar/app.py` — Flask endpoint (40 lines)
- `overlay/router_bot_overlay.py` — PyQt6 bot (260 lines)
- `requirements.txt` — Dependencies

### Test Suite
- `tests/test_blocked.py` — Simulates 23/23 connections locked
- `tests/test_warning.py` — Simulates 12/23 connections locked
- `tests/test_restore_idle.py` — Restores to normal state

### Sample Data
- `sample-logs/events.log` — Example 9router log events for analysis

---

## 🎯 What We Need from Claude

Send the ZIP + PROMPT.md to Claude and ask for:

1. **Architecture Recommendation** (Option A vs B)
   - Should Flask sidecar parse logs, or bot read directly?
   - Pros/cons for Windows file access

2. **State Priority Matrix**
   - Which event wins if multiple happen simultaneously?
   - Should events stack or override?

3. **Animation Implementation Details**
   - How to implement SUCCESS victory dance (trig functions)?
   - How to implement ONBOARDING sweating animation?
   - How to implement FAILED collapse animation?

4. **Log Parsing Strategy**
   - Regex patterns for event detection
   - File rotation handling
   - Buffering strategy for multi-line events

5. **State Machine Diagram**
   - Visual flow of all states + transitions

6. **Implementation Roadmap**
   - 3-5 phase breakdown
   - Which files to modify
   - Which files to create new

7. **Test Scenarios**
   - How to simulate each new event
   - What to verify after implementation

---

## 🚀 How to Send to Claude

**Recommended Approach:**

1. **Open Claude conversation**
2. **Paste this intro:**
   ```
   I'm building a desktop monitoring bot for 9router (Python + PyQt6). 
   I have a working MVP that displays connection pool status with 4 animation states.
   Now I want to extend it to show rich event states detected from 9router's runtime logs.
   
   I've prepared a consultation package with:
   - Complete source code (Flask sidecar + PyQt6 overlay)
   - Detailed context document (CONTEXT.md)
   - Consultation prompt with 7 key design questions (PROMPT.md)
   - Sample logs + test scenarios
   
   Please review the attached ZIP and provide architecture recommendations.
   ```

3. **Attach the ZIP file:** `9router-bot-project.zip`
4. **Wait for Claude's comprehensive review**

---

## 📊 Current State

**What Works:**
- ✅ Reads 9router db.json (connection pool status)
- ✅ Flask sidecar exposes `/api/status` (< 500ms)
- ✅ PyQt6 desktop bot with 4 animation states
- ✅ System tray integration + drag/drop
- ✅ Test suite with state simulation
- ✅ Polling every 4 seconds

**What's Needed:**
- ❓ Event detection from 9router logs
- ❓ 3 new animation states (SUCCESS, ONBOARDING, TOKEN_EXPIRED)
- ❓ State priority logic
- ❓ Integration testing

---

## 🎬 New Event Types to Display

| Event | Current Status | Proposed Animation |
|-------|---|---|
| **SUCCESS** | Not shown | Victory dance (jump + sparkles) |
| **ONBOARDING_RETRY** | Not shown | Sweating (head tilt + droplets) |
| **ONBOARDING_FAILED** | Not shown | Collapse/KO (slide down + X eyes) |
| **TOKEN_EXPIRED** | Not shown | Glitch effect (position jitter) |

---

## 💡 Key Decision Points

Claude needs to recommend:

### 1. Data Flow
- **Option A:** Flask sidecar parses logs (centralized)
- **Option B:** Bot reads logs directly (decentralized)

### 2. Animation Approach
- Pure trig functions (current style)
- Add Lottie JSON support
- SVG + PyQt renderer
- Hybrid (trig motion + SVG symbols)

### 3. Event Persistence
- Auto-reset after N seconds?
- Manual reset required?
- Stack multiple events?

### 4. Windows Path Handling
- Where does 9router store logs?
- How to handle file rotation?
- File locking issues on Windows?

---

## 🔗 Quick Links

- **Project root:** `d:\TEST\9routerBot\9router-bot-project\`
- **ZIP location:** `d:\TEST\9routerBot\9router-bot-project.zip`
- **Sidecar:** `sidecar/app.py` (40 lines, simple)
- **Bot:** `overlay/router_bot_overlay.py` (260 lines, PyQt6)
- **Key prompt:** `docs/PROMPT.md` (copy entire content to Claude)

---

## 🎓 Background for Claude

**User Profile:**
- Location: Vietnam (Vietnamese UI preferred)
- Tech level: Intermediate Python + PyQt6 experience
- Goal: Monitor 9router connection health with visual desktop indicator
- Constraints: Lightweight (no heavy deps), Windows-first

**Current Stack:**
- Python 3.10+
- Flask 3.1.3
- PyQt6 6.11.0
- requests 2.32.3

**Animations:**
- Pure trigonometric functions (no external animation libs)
- Math-based (sin, cos, linear interpolation)
- ~30 FPS rendering

---

## ✅ Checklist Before Sending to Claude

- [ ] ZIP file created: `9router-bot-project.zip`
- [ ] PROMPT.md reviewed (clear & detailed)
- [ ] CONTEXT.md contains all required info
- [ ] Source code is readable & well-commented
- [ ] Sample logs included for analysis
- [ ] README explains how to run/test
- [ ] requirements.txt is complete
- [ ] Questions for Claude are specific (not vague)

---

## 📝 Next Steps After Claude Review

1. **Claude provides recommendations** (architecture, animation specs, roadmap)
2. **Implement Phase 1** (likely: extend Flask sidecar with event detection)
3. **Implement Phase 2** (add SUCCESS animation)
4. **Implement Phase 3** (add ONBOARDING animations)
5. **Test & iterate** (use test suite for validation)
6. **Optimize performance** (profiling, caching)

---

**Ready to send to Claude!** 🚀

The ZIP file + PROMPT.md will give Claude everything needed to provide a comprehensive architecture review + implementation roadmap.
