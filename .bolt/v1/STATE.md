# V1 State

## Phase
5

## Status
v1_complete

## Progress
- [x] Project created
- [x] Idea defined (`/bolt:discover`)
- [x] Technical research (`/bolt:research`)
- [x] Roadmap planned (`/bolt:roadmap`)
- [x] Phase 1: Project Foundation ✅ (4/4 AC passed)
- [x] Phase 2: Rendering Engine ✅ (3/3 AC passed)
- [x] Phase 3: Visual Presets ✅ (3/3 AC passed)
- [x] Phase 4: Loop Extension ✅ (3/3 AC passed)
- [x] Phase 5: TUI & Polish ✅ (3/3 AC passed)

## Key Decisions
- Hybrid rendering: Cairo (shapes) + NumPy (pixel effects)
- Seamless loops via time-wrapping with periodic functions + circular noise
- NumPy vectorized particle system (5,000+ particles)
- 3 presets for v1: ambient, focus, trippy
- Visuals independent of audio (no audio-reactive in v1)
- questionary for TUI, FFmpeg via subprocess pipe
- opensimplex for 4D noise (circular loopable motion)
- Noise at lower res (270p) + bicubic upscale for performance
- opensimplex noise4array broken on Python 3.13 — scalar fallback
- Loop extension via FFmpeg -stream_loop (stream copy, no re-encode)

## Planned Next
- Visual quality pass: metaballs, glow/bloom, flow fields, color cycling, aurora ribbons, vignette
- Make each preset visually unique with different effect types
- Future v2: GLSL shaders via moderngl for 3D-like visuals

## Notes
V1 complete! All 5 phases passed. Next: visual quality improvements.
