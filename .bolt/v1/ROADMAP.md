# Roadmap — V1

## Phase 1: Project Foundation
**Goal:** Set up project structure, dependencies, config system, and FFmpeg pipeline

### Requirements
- **R1:** Python package structure with pyproject.toml and dependencies (pycairo, numpy, opensimplex, questionary)
- **R2:** Pydantic Settings config system (resolution, fps, output dir, defaults)
- **R3:** FFmpeg subprocess wrapper — pipe raw RGB frames to stdin, produce MP4
- **R4:** FFmpeg availability check on startup

### Success Criteria
Can pipe a solid-color test frame to FFmpeg and produce a valid 10-second MP4

---

## Phase 2: Rendering Engine
**Goal:** Build the hybrid Cairo + NumPy frame renderer with the time-loop system

### Requirements
- **R1:** Time system — normalized `t ∈ [0,1)` with periodic θ conversion
- **R2:** Cairo surface setup (1080p) with BGRA→RGB conversion for FFmpeg
- **R3:** NumPy noise field generator (opensimplex at 270p, bicubic upscale)
- **R4:** Layer compositor — stack background + midground + foreground into final frame
- **R5:** Vectorized particle system (positions, velocities, phases, colors as NumPy arrays)

### Success Criteria
Can render a 30-second seamless loop of layered particles + noise background to MP4

---

## Phase 3: Visual Presets
**Goal:** Implement the 3 mood-based preset system with distinct visual identities

### Requirements
- **R1:** Preset architecture — mood tag maps to color palette, effect layers, motion params
- **R2:** `ambient` preset — deep blues/teals, slow flowing gradients, gentle particle drift
- **R3:** `focus` preset — warm ambers/golds on dark background, structured particle flow
- **R4:** `trippy` preset — vibrant multi-color, fast organic motion, dense particle swarms
- **R5:** Randomization within preset (seed-based) for variety across runs

### Success Criteria
Three visually distinct, high-quality looping videos from `--mood ambient/focus/trippy`

---

## Phase 4: Loop Extension
**Goal:** Extend short loops to arbitrary duration and finalize video output pipeline

### Requirements
- **R1:** Loop extension — seamlessly repeat a rendered loop to fill target duration
- **R2:** Configurable mode — short loop (default) vs full-length unique render
- **R3:** YouTube-optimized H.264 encoding settings (profile, bitrate, pixel format)

### Success Criteria
Can produce a 5-minute video from a 45-second loop with no visible seam

---

## Phase 5: TUI & Polish
**Goal:** Interactive terminal interface and production-ready CLI

### Requirements
- **R1:** questionary-based TUI — select mood, set duration, choose loop mode, confirm & generate
- **R2:** Progress display during rendering (frame count, ETA)
- **R3:** Python API surface — `generate()` function callable from external code
- **R4:** Error handling, input validation, helpful error messages

### Success Criteria
Run the tool, pick options from the menu, get a polished video out — end to end
