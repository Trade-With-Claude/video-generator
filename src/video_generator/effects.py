"""Advanced visual effect layers."""

from __future__ import annotations

import math

import cairo
import numpy as np
import opensimplex
from scipy.ndimage import gaussian_filter

from video_generator.layers import Layer


class GlowParticleLayer(Layer):
    """Sharp particles with radial gradient glow halos via Cairo."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        count: int = 200,
        seed: int = 0,
        colors: list[tuple[int, int, int]] | None = None,
        size_range: tuple[float, float] = (2.0, 6.0),
        drift_range: tuple[float, float] = (40.0, 180.0),
        glow_radius: float = 3.0,
        alpha_range: tuple[float, float] = (0.4, 0.9),
    ) -> None:
        self.width = width
        self.height = height
        self.count = count
        self.glow_mult = glow_radius  # multiplier: halo radius = size * glow_mult

        rng = np.random.default_rng(seed)

        if colors is None:
            colors = [(100, 200, 255), (150, 220, 255), (80, 160, 240)]

        self.base_x = rng.uniform(0, width, count)
        self.base_y = rng.uniform(0, height, count)
        self.phases = rng.uniform(0, 2 * math.pi, count)
        self.drift_x = rng.uniform(drift_range[0], drift_range[1], count)
        self.drift_y = rng.uniform(drift_range[0], drift_range[1], count)
        self.sizes = rng.uniform(size_range[0], size_range[1], count)
        self.alphas = rng.uniform(alpha_range[0], alpha_range[1], count)

        self.colors = np.array([colors[i % len(colors)] for i in range(count)], dtype=np.float64)
        self.colors += rng.uniform(-20, 20, self.colors.shape)
        self.colors = np.clip(self.colors, 0, 255)

    def render(self, t: float, theta: float) -> np.ndarray:
        x = self.base_x + self.drift_x * np.sin(theta + self.phases)
        y = self.base_y + self.drift_y * np.cos(theta * 0.8 + self.phases)
        x = x % self.width
        y = y % self.height

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)

        for i in range(self.count):
            r, g, b = self.colors[i] / 255.0
            a = self.alphas[i]
            px, py = float(x[i]), float(y[i])
            sz = float(self.sizes[i])
            halo_r = sz * self.glow_mult

            # Draw glow halo (radial gradient: bright center → transparent edge)
            pat = cairo.RadialGradient(px, py, sz * 0.5, px, py, halo_r)
            pat.add_color_stop_rgba(0.0, r, g, b, a * 0.5)
            pat.add_color_stop_rgba(0.5, r, g, b, a * 0.15)
            pat.add_color_stop_rgba(1.0, r, g, b, 0.0)
            ctx.set_source(pat)
            ctx.arc(px, py, halo_r, 0, 2 * math.pi)
            ctx.fill()

            # Draw sharp core
            ctx.set_source_rgba(r, g, b, a)
            ctx.arc(px, py, sz, 0, 2 * math.pi)
            ctx.fill()

        buf = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape(
            self.height, self.width, 4
        ).copy()

        # BGRA → RGBA
        rgba = np.empty_like(buf)
        rgba[:, :, 0] = buf[:, :, 2]
        rgba[:, :, 1] = buf[:, :, 1]
        rgba[:, :, 2] = buf[:, :, 0]
        rgba[:, :, 3] = buf[:, :, 3]

        return rgba


class AuroraLayer(Layer):
    """Flowing aurora ribbons — sinusoidal color bands that drift."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        num_ribbons: int = 5,
        seed: int = 0,
        colors: list[tuple[int, int, int]] | None = None,
        speed: float = 1.0,
        wave_scale: float = 1.0,
        alpha: float = 0.4,
    ) -> None:
        self.width = width
        self.height = height
        self.num_ribbons = num_ribbons
        self.speed = speed
        self.wave_scale = wave_scale
        self.alpha_val = alpha

        rng = np.random.default_rng(seed)

        if colors is None:
            colors = [(40, 200, 180), (80, 120, 220), (120, 60, 200)]

        self.ribbon_colors = [colors[i % len(colors)] for i in range(num_ribbons)]
        self.ribbon_y_base = rng.uniform(0.15, 0.85, num_ribbons)  # Normalized y positions
        self.ribbon_phases = rng.uniform(0, 2 * math.pi, num_ribbons)
        self.ribbon_freqs = rng.uniform(1.5, 4.0, num_ribbons)
        self.ribbon_widths = rng.uniform(60, 150, num_ribbons)
        self.ribbon_amplitudes = rng.uniform(30, 100, num_ribbons)

        # Pre-compute x coordinates
        self.x_coords = np.linspace(0, 2 * math.pi * wave_scale, width)

    def render(self, t: float, theta: float) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        y_pixels = np.arange(self.height)

        for i in range(self.num_ribbons):
            r, g, b = self.ribbon_colors[i]
            phase = self.ribbon_phases[i]
            freq = self.ribbon_freqs[i]
            width_px = self.ribbon_widths[i]
            amp = self.ribbon_amplitudes[i]
            y_center_norm = self.ribbon_y_base[i]

            # Ribbon center oscillates with theta for seamless loop
            y_offset = amp * math.sin(theta * self.speed + phase)
            y_center = y_center_norm * self.height + y_offset

            # Sinusoidal wave shape along x
            wave = np.sin(self.x_coords * freq + theta * self.speed * 0.7 + phase) * amp * 0.4
            ribbon_y_per_x = y_center + wave  # (W,)

            # Distance from each pixel row to the ribbon center at each x
            # Shape: (H, W)
            dist = np.abs(y_pixels[:, np.newaxis] - ribbon_y_per_x[np.newaxis, :])

            # Gaussian falloff
            intensity = np.exp(-0.5 * (dist / (width_px * 0.4)) ** 2)

            alpha = (intensity * self.alpha_val * 255).astype(np.uint8)

            # Blend ribbon onto frame
            mask = alpha > 0
            blend = alpha[mask].astype(np.float32) / 255.0
            for c_idx, c_val in enumerate([r, g, b]):
                existing = frame[:, :, c_idx][mask].astype(np.float32)
                frame[:, :, c_idx][mask] = (existing * (1 - blend) + c_val * blend).astype(np.uint8)
            frame[:, :, 3] = np.maximum(frame[:, :, 3], alpha)

        return frame


class FlowFieldLayer(Layer):
    """Particles following noise-based curved flow paths."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        count: int = 1500,
        seed: int = 0,
        color_base: tuple[int, int, int] = (200, 180, 100),
        color_variance: float = 30.0,
        size_range: tuple[float, float] = (1.0, 2.5),
        alpha_range: tuple[float, float] = (0.3, 0.7),
        flow_scale: float = 3.0,
        trail_length: int = 6,
    ) -> None:
        self.width = width
        self.height = height
        self.count = count
        self.flow_scale = flow_scale
        self.trail_length = trail_length

        rng = np.random.default_rng(seed)
        opensimplex.seed(seed + 1000)

        self.base_x = rng.uniform(0, width, count)
        self.base_y = rng.uniform(0, height, count)
        self.phases = rng.uniform(0, 2 * math.pi, count)
        self.sizes = rng.uniform(size_range[0], size_range[1], count)
        self.alphas = rng.uniform(alpha_range[0], alpha_range[1], count)

        self.colors = np.zeros((count, 3), dtype=np.float64)
        for c in range(3):
            self.colors[:, c] = np.clip(
                color_base[c] + rng.uniform(-color_variance, color_variance, count), 0, 255
            )

    def render(self, t: float, theta: float) -> np.ndarray:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)

        for i in range(self.count):
            # Base position with periodic motion
            bx = self.base_x[i] + 50 * math.sin(theta + self.phases[i])
            by = self.base_y[i] + 50 * math.cos(theta * 0.7 + self.phases[i])

            # Flow field offset from noise
            nx = (bx / self.width) * self.flow_scale
            ny = (by / self.height) * self.flow_scale
            angle = opensimplex.noise4(
                nx, ny, math.cos(theta) * 0.8, math.sin(theta) * 0.8
            ) * math.pi * 2

            flow_dist = 40 + 30 * math.sin(theta * 0.5 + self.phases[i])
            fx = bx + math.cos(angle) * flow_dist
            fy = by + math.sin(angle) * flow_dist

            fx = fx % self.width
            fy = fy % self.height

            r, g, b = self.colors[i] / 255.0
            a = self.alphas[i]

            # Draw small trail
            for step in range(self.trail_length):
                trail_t = step / self.trail_length
                trail_alpha = a * (1.0 - trail_t * 0.7)
                trail_size = self.sizes[i] * (1.0 - trail_t * 0.5)
                # Trail position interpolated back toward base
                tx = fx * (1 - trail_t) + bx * trail_t
                ty = fy * (1 - trail_t) + by * trail_t
                tx = tx % self.width
                ty = ty % self.height

                ctx.set_source_rgba(r, g, b, trail_alpha)
                ctx.arc(tx, ty, trail_size, 0, 2 * math.pi)
                ctx.fill()

        buf = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape(
            self.height, self.width, 4
        ).copy()

        rgba = np.empty_like(buf)
        rgba[:, :, 0] = buf[:, :, 2]
        rgba[:, :, 1] = buf[:, :, 1]
        rgba[:, :, 2] = buf[:, :, 0]
        rgba[:, :, 3] = buf[:, :, 3]

        return rgba


class VignetteLayer(Layer):
    """Radial darkening from edges for cinematic feel."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        strength: float = 0.7,
        radius: float = 0.8,
    ) -> None:
        self.width = width
        self.height = height

        # Pre-compute vignette mask
        y = np.linspace(-1, 1, height)
        x = np.linspace(-1, 1, width)
        xv, yv = np.meshgrid(x, y)
        dist = np.sqrt(xv ** 2 + yv ** 2)

        # Smooth falloff
        self.mask = np.clip(1.0 - ((dist - radius) / (1.5 - radius)) * strength, 0, 1)
        self.mask = self.mask.astype(np.float32)

    def render(self, t: float, theta: float) -> np.ndarray:
        # Return as RGB — compositor will multiply
        # We use a trick: return a dark frame with the vignette as brightness
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Actually, we need to darken the existing canvas. Return RGBA where
        # alpha represents how much to keep of the underlying image.
        # Black pixels with alpha = vignette strength → darkens edges.
        frame_rgba = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        # Invert: where mask is 0 (edges), we want darkening
        darken = ((1.0 - self.mask) * 255).astype(np.uint8)
        frame_rgba[:, :, 3] = darken
        return frame_rgba


class ColorCycleBackground(Layer):
    """Multi-color radial gradient that rotates hue over time."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        colors: list[tuple[int, int, int]] | None = None,
        speed: float = 1.0,
        center_drift: float = 0.15,
        seed: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.speed = speed
        self.center_drift = center_drift

        rng = np.random.default_rng(seed)

        if colors is None:
            colors = [
                (10, 20, 60),
                (30, 10, 70),
                (15, 40, 80),
                (5, 15, 50),
            ]
        self.colors = [np.array(c, dtype=np.float64) for c in colors]
        self.phase_offsets = rng.uniform(0, 2 * math.pi, len(colors))

        # Pre-compute normalized coordinate grid
        y = np.linspace(-1, 1, height)
        x = np.linspace(-1, 1, width)
        self.xv, self.yv = np.meshgrid(x, y)

    def render(self, t: float, theta: float) -> np.ndarray:
        # Drifting center for organic feel
        cx = self.center_drift * math.sin(theta * self.speed)
        cy = self.center_drift * math.cos(theta * self.speed * 0.7)

        dist = np.sqrt((self.xv - cx) ** 2 + (self.yv - cy) ** 2)
        dist_norm = dist / dist.max()

        # Angle from center for color variation
        angle = np.arctan2(self.yv - cy, self.xv - cx)

        frame = np.zeros((self.height, self.width, 3), dtype=np.float64)

        for i, color in enumerate(self.colors):
            # Each color contributes based on angle + time
            phase = theta * self.speed + self.phase_offsets[i]
            weight = 0.5 + 0.5 * np.sin(angle * 2 + phase + dist_norm * 3)
            weight *= (1.0 - dist_norm * 0.5)  # Fade toward edges

            for c in range(3):
                frame[:, :, c] += color[c] * weight

        # Normalize
        frame /= max(len(self.colors) * 0.5, 1)
        frame = np.clip(frame, 0, 255).astype(np.uint8)

        return frame
