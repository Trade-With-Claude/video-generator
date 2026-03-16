# Video Generator

## The Idea
A generative visual video tool for ambient/meditation/ADHD-focus YouTube content. Creates seamlessly looping visuals — particle systems, organic motion, flowing patterns — that pair with binaural beats and focus music tracks. Standalone CLI with a simple TUI for v1, designed to plug into a larger automation pipeline later.

## The Problem
Creating visuals for music videos is time-consuming and repetitive. For a channel that needs consistent uploads of ambient/focus content, manually creating or sourcing visuals for every track is a bottleneck. This tool automates visual generation with mood-matched presets so you can go from audio track to upload-ready video fast.

## Key Features
- **Mood-based preset system** — pass a tag like `ambient`, `focus`, `trippy` and get matching visuals
- **Seamless looping** — short loops (30-60 sec) extended to any duration, no visible cut point
- **Pure Python generative engine** — particle systems, flowing gradients, organic motion via Cairo/Pillow
- **FFmpeg integration** — frame assembly, video encoding, future audio merge
- **Simple TUI** — interactive terminal menu to pick mood, set duration, configure, and generate
- **Pipeline-ready architecture** — callable interface for future youtube-autopilot integration

## Stack / Tech Preferences
- Python (main language)
- Cairo / Pillow (frame generation)
- FFmpeg (video assembly)
- 1080p 30fps output
- No Node.js, no browser dependencies

## Notes
- Part of the broader youtube-autopilot project
- GLSL shaders planned for v2 (skipped in v1 due to macOS headless complexity)
- Keep rendering fast — short loop + extend is the default strategy
- Visual quality matters — these are public YouTube videos, not placeholders
