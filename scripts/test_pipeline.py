"""Test script: pipe solid-color frames through FFmpeg to produce a 10-second MP4."""

import numpy as np

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegPipe

settings = Settings()
output_path = settings.output_dir / "test.mp4"
total_frames = settings.fps * 10  # 10 seconds

# Deep teal solid color
frame = np.full((settings.height, settings.width, 3), [10, 80, 90], dtype=np.uint8)

print(f"Rendering {total_frames} frames at {settings.width}x{settings.height} @ {settings.fps}fps...")

with FFmpegPipe(output_path, settings) as pipe:
    for i in range(total_frames):
        pipe.write_frame(frame)
        if (i + 1) % settings.fps == 0:
            print(f"  {i + 1}/{total_frames} frames")

size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"Done! Output: {output_path} ({size_mb:.1f} MB)")
