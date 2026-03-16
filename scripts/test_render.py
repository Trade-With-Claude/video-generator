"""Integration test: render a seamless loop with noise + particles."""

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegPipe
from video_generator.layers import LayerCompositor, NoiseBackground
from video_generator.particles import ParticleLayer
from video_generator.time_loop import TimeLoop

settings = Settings()
output_path = settings.output_dir / "test_render.mp4"
import sys
duration = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

# Build layers
bg = NoiseBackground(
    settings.width,
    settings.height,
    scale=3.0,
    speed=1.0,
    color_low=(5, 20, 60),
    color_high=(20, 100, 140),
    seed=42,
)
particles = ParticleLayer(
    settings.width,
    settings.height,
    count=1500,
    seed=42,
    color_base=(100, 200, 220),
    alpha_range=(0.3, 0.7),
)

compositor = LayerCompositor([bg, particles], settings.width, settings.height)
loop = TimeLoop(settings.fps, duration)

print(f"Rendering {len(loop)} frames at {settings.width}x{settings.height} @ {settings.fps}fps...")

with FFmpegPipe(output_path, settings) as pipe:
    for i, t, theta in loop:
        frame = compositor.render_frame(t, theta)
        pipe.write_frame(frame)
        if (i + 1) % settings.fps == 0:
            sec = (i + 1) // settings.fps
            print(f"  {sec}/{int(duration)}s ({i + 1}/{len(loop)} frames)")

size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"Done! Output: {output_path} ({size_mb:.1f} MB)")
