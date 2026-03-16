"""FFmpeg subprocess wrapper for piping raw frames to video."""

import shutil
import subprocess
from pathlib import Path

import numpy as np

from video_generator.config import Settings


class FFmpegError(RuntimeError):
    """Raised when FFmpeg is missing or fails."""


def check_ffmpeg() -> str:
    """Check that FFmpeg is available on PATH. Returns the path to the binary."""
    path = shutil.which("ffmpeg")
    if path is None:
        raise FFmpegError(
            "FFmpeg not found on PATH. Install it with: brew install ffmpeg"
        )
    return path


class FFmpegPipe:
    """Pipe raw RGB frames to FFmpeg and produce an MP4."""

    def __init__(self, output_path: Path, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._process: subprocess.Popen | None = None

    def open(self) -> "FFmpegPipe":
        """Start the FFmpeg subprocess."""
        s = self.settings
        cmd = [
            check_ffmpeg(),
            "-y",
            # Input: raw RGB frames from stdin
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{s.width}x{s.height}",
            "-framerate", str(s.fps),
            "-i", "pipe:0",
            # Output: YouTube-optimized H.264
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            "-movflags", "+faststart",
            str(self.output_path),
        ]
        self._process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        return self

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a single RGB frame (H x W x 3, uint8)."""
        if self._process is None or self._process.stdin is None:
            raise FFmpegError("FFmpeg pipe is not open. Call .open() first.")
        self._process.stdin.write(frame.tobytes())

    def close(self) -> None:
        """Close stdin and wait for FFmpeg to finish."""
        if self._process is None:
            return
        if self._process.stdin:
            self._process.stdin.close()
        self._process.wait()
        if self._process.returncode != 0:
            stderr = self._process.stderr.read().decode() if self._process.stderr else ""
            raise FFmpegError(f"FFmpeg exited with code {self._process.returncode}: {stderr}")

    def __enter__(self) -> "FFmpegPipe":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()
