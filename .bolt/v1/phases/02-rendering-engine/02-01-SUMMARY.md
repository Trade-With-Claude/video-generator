# Phase 2 Summary: Rendering Engine

## Acceptance Criteria

| AC | Description | Result |
|----|-------------|--------|
| AC1 | Time system produces seamless loop (t ∈ [0,1), θ wraps) | PASS |
| AC2 | Layered frame renders to (1080, 1920, 3) uint8 RGB array | PASS |
| AC3 | Full loop renders to valid 1080p30 MP4 with visible effects | PASS |

## Tasks

| Task | Description | Result |
|------|-------------|--------|
| 1 | Time system + noise field + layer compositor | PASS |
| 2 | Particle system + Cairo renderer | PASS |
| 3 | Integration test — render seamless loop | PASS |

## Deviations

- **opensimplex numba breakage**: `noise4array` (and all `*array` functions) are broken on Python 3.13 due to numba/floor incompatibility. Added auto-detection at import time with scalar `noise4` fallback. Performance at 270p is ~0.12s/frame (acceptable).
- **scipy dependency**: Used `scipy.ndimage.zoom` for bicubic upscale of noise field. scipy was already installed but is NOT in `pyproject.toml` — needs adding (boundary prevented modifying pyproject.toml this phase).
- **Test duration reduced**: Script defaults to 10s instead of 30s for faster verification, but accepts duration as CLI arg.
- **User feedback on visuals**: User noted the default visuals aren't what they want design-wise. Expected — Phase 3 (presets) is where the actual visual design happens.

## Files Created

- `src/video_generator/time_loop.py` — TimeLoop class (normalized t, periodic θ)
- `src/video_generator/layers.py` — Layer ABC, NoiseBackground, LayerCompositor
- `src/video_generator/particles.py` — ParticleLayer with Cairo anti-aliased rendering
- `scripts/test_render.py` — End-to-end render integration test

## Carry-Forward

- Add `scipy` to `pyproject.toml` dependencies (deferred due to boundary)

## Phase Complete: YES
