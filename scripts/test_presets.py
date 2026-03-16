"""Render 5 seconds of each preset to verify visual distinctness."""

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegPipe
from video_generator.layers import LayerCompositor
from video_generator.presets import AVAILABLE_MOODS, get_preset
from video_generator.render import build_layers
from video_generator.time_loop import TimeLoop

settings = Settings()
duration = 5.0

for mood in AVAILABLE_MOODS:
    preset = get_preset(mood, seed=42)
    layers = build_layers(preset, settings.width, settings.height)
    compositor = LayerCompositor(layers, settings.width, settings.height)
    loop = TimeLoop(settings.fps, duration)

    output_path = settings.output_dir / f"preset_{mood}.mp4"
    print(f"\nRendering '{mood}' preset ({preset.particle_count} particles)...")

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
