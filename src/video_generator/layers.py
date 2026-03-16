"""Layer system: noise background and compositor."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

import numpy as np
import opensimplex
from scipy.ndimage import zoom


class Layer(ABC):
    """Base class for renderable layers."""

    @abstractmethod
    def render(self, t: float, theta: float) -> np.ndarray:
        """Render this layer and return an (H, W, 3) uint8 RGB array."""


class NoiseBackground(Layer):
    """Loopable noise field rendered at low res and upscaled."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        *,
        scale: float = 3.0,
        speed: float = 1.0,
        color_low: tuple[int, int, int] = (5, 20, 60),
        color_high: tuple[int, int, int] = (20, 100, 140),
        seed: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.scale = scale
        self.speed = speed
        self.color_low = np.array(color_low, dtype=np.float64)
        self.color_high = np.array(color_high, dtype=np.float64)

        # Low-res grid (270p equivalent)
        self.lr_h = height // 4
        self.lr_w = width // 4
        self.scale_y = height / self.lr_h
        self.scale_x = width / self.lr_w

        # Pre-compute spatial coordinates
        y_coords = np.linspace(0, self.scale, self.lr_h)
        x_coords = np.linspace(0, self.scale, self.lr_w)
        self.xs, self.ys = np.meshgrid(x_coords, y_coords)

        opensimplex.seed(seed)

    def render(self, t: float, theta: float) -> np.ndarray:
        # Circular path through noise z/w for seamless loop
        z = math.cos(theta) * self.speed
        w = math.sin(theta) * self.speed

        z_arr = np.full_like(self.xs, z)
        w_arr = np.full_like(self.xs, w)

        # Generate noise at low res — returns values in [-1, 1]
        noise = opensimplex.noise4array(self.xs, self.ys, z_arr, w_arr)

        # Normalize to [0, 1]
        noise_norm = (noise + 1.0) * 0.5

        # Upscale to full resolution with bicubic interpolation
        noise_full = zoom(noise_norm, (self.scale_y, self.scale_x), order=3)

        # Clip to exact dimensions (zoom can be off by 1 pixel)
        noise_full = noise_full[: self.height, : self.width]

        # Map to color gradient
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for c in range(3):
            channel = self.color_low[c] + noise_full * (self.color_high[c] - self.color_low[c])
            frame[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)

        return frame


class LayerCompositor:
    """Stack multiple layers into a final frame using alpha blending."""

    def __init__(self, layers: list[Layer], width: int = 1920, height: int = 1080) -> None:
        self.layers = layers
        self.width = width
        self.height = height

    def render_frame(self, t: float, theta: float) -> np.ndarray:
        """Render all layers and composite them."""
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        for layer in self.layers:
            layer_frame = layer.render(t, theta)
            if layer_frame.shape[2] == 4:
                # RGBA — alpha blend
                alpha = layer_frame[:, :, 3:4].astype(np.float32) / 255.0
                rgb = layer_frame[:, :, :3]
                canvas = (
                    canvas.astype(np.float32) * (1.0 - alpha) + rgb.astype(np.float32) * alpha
                ).astype(np.uint8)
            else:
                # RGB — first layer replaces, subsequent layers overwrite non-black pixels
                if np.any(canvas):
                    mask = np.any(layer_frame > 0, axis=2, keepdims=True)
                    canvas = np.where(mask, layer_frame, canvas)
                else:
                    canvas = layer_frame

        return canvas
