"""Vectorized particle system with Cairo rendering."""

from __future__ import annotations

import math

import cairo
import numpy as np

from video_generator.layers import Layer


class ParticleLayer(Layer):
    """Particle swarm rendered as anti-aliased circles via Cairo."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        count: int = 2000,
        seed: int = 0,
        color_base: tuple[int, int, int] = (100, 200, 220),
        color_variance: float = 30.0,
        size_range: tuple[float, float] = (1.5, 4.0),
        drift_range: tuple[float, float] = (50.0, 200.0),
        alpha_range: tuple[float, float] = (0.2, 0.7),
    ) -> None:
        self.width = width
        self.height = height
        self.count = count

        rng = np.random.default_rng(seed)

        # Base positions (center of orbit)
        self.base_x = rng.uniform(0, width, count)
        self.base_y = rng.uniform(0, height, count)

        # Random phase offset per particle for variety
        self.phases = rng.uniform(0, 2 * math.pi, count)

        # Drift radius — how far each particle orbits from its base
        self.drift_x = rng.uniform(drift_range[0], drift_range[1], count)
        self.drift_y = rng.uniform(drift_range[0], drift_range[1], count)

        # Sizes
        self.sizes = rng.uniform(size_range[0], size_range[1], count)

        # Colors with variance
        self.colors = np.zeros((count, 3), dtype=np.float64)
        for c in range(3):
            self.colors[:, c] = np.clip(
                color_base[c] + rng.uniform(-color_variance, color_variance, count),
                0,
                255,
            )

        # Alpha per particle
        self.alphas = rng.uniform(alpha_range[0], alpha_range[1], count)

    def render(self, t: float, theta: float) -> np.ndarray:
        """Render particles at the given time. Returns (H, W, 4) RGBA uint8 array."""
        # Compute positions using periodic functions — seamless loop
        x = self.base_x + self.drift_x * np.sin(theta + self.phases)
        y = self.base_y + self.drift_y * np.cos(theta * 0.7 + self.phases)

        # Wrap around screen edges
        x = x % self.width
        y = y % self.height

        # Create Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)

        # Draw each particle as an anti-aliased circle
        for i in range(self.count):
            r = self.colors[i, 0] / 255.0
            g = self.colors[i, 1] / 255.0
            b = self.colors[i, 2] / 255.0
            a = self.alphas[i]

            ctx.set_source_rgba(r, g, b, a)
            ctx.arc(x[i], y[i], self.sizes[i], 0, 2 * math.pi)
            ctx.fill()

        # Convert Cairo BGRA premultiplied → RGBA
        buf = surface.get_data()
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(self.height, self.width, 4).copy()

        # Cairo uses BGRA on little-endian — swap to RGBA
        rgba = np.empty_like(arr)
        rgba[:, :, 0] = arr[:, :, 2]  # R
        rgba[:, :, 1] = arr[:, :, 1]  # G
        rgba[:, :, 2] = arr[:, :, 0]  # B
        rgba[:, :, 3] = arr[:, :, 3]  # A

        return rgba
