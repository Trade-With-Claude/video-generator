"""Render 10 seconds of each preset to verify visual distinctness."""

import sys

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegPipe
from video_generator.layers import LayerCompositor
from video_generator.presets import AVAILABLE_MOODS, get_preset
from video_generator.render import build_layers
from video_generator.time_loop import TimeLoop

settings = Settings()
duration = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

for mood in AVAILABLE_MOODS:
    preset = get_preset(mood, seed=42)
    layers = build_layers(preset, settings.width, settings.height)
    compositor = LayerCompositor(layers, settings.width, settings.height)
    loop = TimeLoop(settings.fps, duration)

    output_path = settings.output_dir / f"preset_{mood}.mp4"
    layer_names = [type(l).__name__ for l in layers]
    print(f"\nRendering '{mood}' — layers: {layer_names}")

    with FFmpegPipe(output_path, settings) as pipe:
        for i, t, theta in loop:
            frame = compositor.render_frame(t, theta)
            pipe.write_frame(frame)
            if (i + 1) % settings.fps == 0:
                sec = (i + 1) // settings.fps
                print(f"  {sec}/{int(duration)}s")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Done: {output_path} ({size_mb:.1f} MB)")

print("\nAll presets rendered.")
