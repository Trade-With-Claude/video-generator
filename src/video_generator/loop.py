"""Loop extension — repeat a short seamless loop to fill a target duration."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegError, check_ffmpeg


def extend_loop(
    loop_path: Path,
    output_path: Path,
    target_duration: float,
    settings: Settings | None = None,
) -> Path:
    """Extend a short loop video to fill target_duration via FFmpeg stream copy.

    Uses -stream_loop for repetition and -t to trim to exact length.
    No re-encoding — just stream copy for speed.
    """
    settings = settings or Settings()
    loop_path = Path(loop_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not loop_path.exists():
        raise FFmpegError(f"Loop file not found: {loop_path}")

    # Calculate how many full repeats we need
    # -stream_loop N means play N+1 times total, so we need ceil(target/loop) - 1
    loop_dur = settings.loop_duration
    repeats = math.ceil(target_duration / loop_dur) - 1
    if repeats < 0:
        repeats = 0

    cmd = [
        check_ffmpeg(),
        "-y",
        "-stream_loop", str(repeats),
        "-i", str(loop_path),
        "-t", str(target_duration),
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        stderr = result.stderr.decode()
        raise FFmpegError(f"Loop extension failed: {stderr}")

    return output_path
