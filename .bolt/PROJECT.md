# Video Generator

## Project Info
- **Name:** Video Generator
- **Created:** 2026-03-13
- **Schema:** 1

## Description
Generative visual video creator for ADHD/meditation/binaural beats YouTube content. Produces seamlessly looping ambient visuals (particle systems, organic motion, flowing patterns) that pair with audio tracks. Standalone for v1, designed for future integration into the youtube-autopilot pipeline.

## Team / Owner
Dorian — solo developer, music producer, YouTube channel operator

## Architecture Decisions

### Rendering Engine
- **Hybrid: Cairo + NumPy** — Cairo for anti-aliased shapes/particles, NumPy for pixel-level effects (noise fields, gradients)
- Frames rendered to NumPy arrays, piped directly to FFmpeg subprocess (no intermediate PNGs)
- Cairo surface format is BGRA premultiplied alpha — must convert to RGB before FFmpeg pipe
- GLSL shaders deferred to v2+ (headless rendering on macOS is complex)
- Expected render speed: ~8-15 fps at 1080p (offline batch, ~3 min for a 60s loop)

### Seamless Loop Algorithm
- **Time-wrapping with periodic functions**: all motion parameterized as `t ∈ [0,1)` → `θ = t × 2π`
- Use sin/cos exclusively for position/color/size — mathematically guaranteed seamless loop
- **Circular noise**: sample opensimplex on a circular path through 3D/4D noise space for organic loopable motion
- No crossfade blending (causes ghosting artifacts with particles)
- Noise performance: generate at lower resolution (270p), upscale with bicubic interpolation

### Particle System
- NumPy vectorized arrays: positions `(N,2)`, velocities `(N,2)`, phases `(N,)`, colors `(N,3)`
- Handles 5,000+ particles efficiently
- No OOP per-particle — all updates via vectorized operations
- Each particle's initial phase randomized, motion is periodic in θ

### Visual Effects (Layered)
- Stack 2-3 layers per preset to avoid monotony:
  - Background: gradient or noise field
  - Midground: flow field or aurora ribbons
  - Foreground: particle swarm or morphing shapes

### Visual Presets
- **3 presets for v1**: `ambient`, `focus`, `trippy`
- Each preset defines: color palette, effect layers, particle behavior, motion speed
- Mood-based color mappings:
  - `ambient` — deep blues, teals, soft purples
  - `focus` — warm ambers, soft golds, dark backgrounds
  - `trippy` — vibrant multi-color, high contrast
- Randomization within a preset for variety across videos

### Audio
- **v1: Independent** — visuals are purely generative, no audio analysis
- Audio-reactive mode deferred to v2+

### Loop Strategy
- Default: render a short seamless loop (30-60 sec), extend to match duration
- Configurable: full-length unique render available via flag
- Extension via seamless repetition (loop is mathematically perfect)

### Output
- 1920x1080, 30fps (fixed for v1)
- Output format: MP4 (H.264, YouTube-optimized encoding)
- v1 outputs visuals-only video; architecture supports audio merge + metadata for later
- Memory: 1080p RGBA frame ≈ 8MB — stream to FFmpeg pipe, never accumulate

### Interface
- Simple TUI via **questionary** (interactive prompts: select mood, set duration, configure loop mode)
- Also callable as a Python function for future pipeline integration

### Tech Stack
- **Python** — main language, orchestration
- **pycairo** — anti-aliased 2D shape rendering
- **NumPy** — vectorized particle math, pixel effects, noise field processing
- **opensimplex** — 4D simplex noise for circular loopable motion
- **questionary** — lightweight TUI prompts
- **FFmpeg** (subprocess) — frame piping, video encoding, future audio merge
- No Node.js, no browser dependencies

### Constraints
- FFmpeg must be installed on system (add startup check)
- Offline batch rendering (~3 min per 60s of video at 1080p30)
- macOS ARM (M-series) primary target

## Integration Notes
- Lives inside `youtube-autopilot/` repo (step 3 of pipeline)
- Aligns with youtube_seo_engine patterns: Pydantic Settings for config
- Future: receives audio path + config from pipeline orchestrator, outputs upload-ready video
- Design Python API surface to be importable/callable from parent pipeline
- No shared code with seo_engine yet, but follow same patterns
