## 3. Generate Visuals (two engines)

#### Engine A: GLSL Shaders
- Smooth gradient flows, fractals, morphing blobs, aurora-like patterns
- Render directly to video with FFmpeg
- Best for: dreamy, smooth, ambient vibes

#### Engine B: p5.js / Processing
- Particle systems, organic motion, generative art
- Swirling particles, galaxy-like formations, flowing dots
- Best for: trippy, alive, evolving visuals

Both engines:
- Generate a 3-5 minute seamlessly looping clip
- Multiple presets to choose from (or randomize)
- 1920x1080, 30fps minimum
- Designed for perfect loop — no visible cut point


## Tech Stack (all free)
- **Python** — main language, glue everything together
- **FFmpeg** — video rendering, looping, merging
- **GLSL** (glsl-viewer or similar) — shader-based visuals
- **p5.js / Processing** — particle/generative visuals (render to frames → FFmpeg)