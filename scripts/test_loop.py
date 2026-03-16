"""Test loop extension: render 5s loop, extend to 60s. Also test full-length mode."""

import json
import subprocess

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegPipe
from video_generator.layers import LayerCompositor
from video_generator.loop import extend_loop
from video_generator.presets import get_preset
from video_generator.render import build_layers
from video_generator.time_loop import TimeLoop


def get_duration(path):
    """Get video duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


settings = Settings()
preset = get_preset("ambient", seed=42)
layers = build_layers(preset, settings.width, settings.height)
compositor = LayerCompositor(layers, settings.width, settings.height)

# --- Test 1: Render 5s loop, extend to 60s ---
loop_duration = 5.0
loop_path = settings.output_dir / "loop_5s.mp4"
extended_path = settings.output_dir / "extended_60s.mp4"

print(f"Rendering {loop_duration}s loop...")
loop = TimeLoop(settings.fps, loop_duration)
with FFmpegPipe(loop_path, settings) as pipe:
    for i, t, theta in loop:
        pipe.write_frame(compositor.render_frame(t, theta))
        if (i + 1) % settings.fps == 0:
            print(f"  {(i+1)//settings.fps}/{int(loop_duration)}s")

print("Extending loop to 60s...")
loop_settings = Settings(loop_duration=loop_duration)
extend_loop(loop_path, extended_path, target_duration=60.0, settings=loop_settings)

dur = get_duration(extended_path)
size_mb = extended_path.stat().st_size / (1024 * 1024)
print(f"Extended: {dur:.1f}s, {size_mb:.1f} MB — {'PASS' if abs(dur - 60.0) < 0.5 else 'FAIL'}")

# --- Test 2: Full-length mode (10s, no extension) ---
full_path = settings.output_dir / "full_length_10s.mp4"
full_duration = 10.0

print(f"\nRendering {full_duration}s full-length (no extension)...")
loop2 = TimeLoop(settings.fps, full_duration)
with FFmpegPipe(full_path, settings) as pipe:
    for i, t, theta in loop2:
        pipe.write_frame(compositor.render_frame(t, theta))
        if (i + 1) % settings.fps == 0:
            print(f"  {(i+1)//settings.fps}/{int(full_duration)}s")

dur2 = get_duration(full_path)
print(f"Full-length: {dur2:.1f}s — {'PASS' if abs(dur2 - 10.0) < 0.5 else 'FAIL'}")

print("\nDone.")
