"""Time-loop system for seamless animation."""

import math
from typing import Iterator


class TimeLoop:
    """Generate frame timing for a seamless loop.

    Yields (frame_index, t, theta) where:
    - t ∈ [0, 1) — normalized time
    - theta = t * 2π — angle for periodic functions
    """

    def __init__(self, fps: int, duration: float) -> None:
        self.fps = fps
        self.duration = duration
        self.total_frames = int(fps * duration)

    def __iter__(self) -> Iterator[tuple[int, float, float]]:
        for i in range(self.total_frames):
            t = i / self.total_frames
            theta = t * 2.0 * math.pi
            yield i, t, theta

    def __len__(self) -> int:
        return self.total_frames
