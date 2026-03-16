"""Visual preset system — mood-based configurations for the renderer."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Preset:
    """Complete visual configuration for a render."""

    name: str
    seed: int

    # Background noise
    bg_color_low: tuple[int, int, int]
    bg_color_high: tuple[int, int, int]
    bg_noise_scale: float
    bg_noise_speed: float

    # Particles
    particle_count: int
    particle_color_base: tuple[int, int, int]
    particle_color_variance: float
    particle_size_range: tuple[float, float]
    particle_drift_range: tuple[float, float]
    particle_alpha_range: tuple[float, float]


# --- Preset definitions ---
# Each returns base values; get_preset applies seed-based randomization.

def _ambient_base() -> dict:
    return dict(
        name="ambient",
        bg_color_low=(3, 12, 45),
        bg_color_high=(15, 70, 110),
        bg_noise_scale=2.5,
        bg_noise_speed=0.6,
        particle_count=1000,
        particle_color_base=(80, 180, 210),
        particle_color_variance=25.0,
        particle_size_range=(1.0, 3.5),
        particle_drift_range=(30.0, 120.0),
        particle_alpha_range=(0.15, 0.5),
    )


def _focus_base() -> dict:
    return dict(
        name="focus",
        bg_color_low=(10, 5, 2),
        bg_color_high=(45, 30, 12),
        bg_noise_scale=3.5,
        bg_noise_speed=0.8,
        particle_count=800,
        particle_color_base=(220, 170, 60),
        particle_color_variance=20.0,
        particle_size_range=(1.5, 4.0),
        particle_drift_range=(40.0, 150.0),
        particle_alpha_range=(0.2, 0.55),
    )


def _trippy_base() -> dict:
    return dict(
        name="trippy",
        bg_color_low=(20, 5, 40),
        bg_color_high=(60, 15, 100),
        bg_noise_scale=4.0,
        bg_noise_speed=1.8,
        particle_count=3000,
        particle_color_base=(200, 80, 220),
        particle_color_variance=60.0,
        particle_size_range=(1.0, 5.0),
        particle_drift_range=(80.0, 280.0),
        particle_alpha_range=(0.25, 0.75),
    )


_PRESETS = {
    "ambient": _ambient_base,
    "focus": _focus_base,
    "trippy": _trippy_base,
}

AVAILABLE_MOODS = list(_PRESETS.keys())


def get_preset(name: str, seed: int = 0) -> Preset:
    """Get a preset by name with seed-based randomization within palette bounds."""
    if name not in _PRESETS:
        raise ValueError(f"Unknown preset '{name}'. Available: {AVAILABLE_MOODS}")

    base = _PRESETS[name]()
    rng = np.random.default_rng(seed)

    # Apply subtle randomization to colors (keep within mood family)
    def jitter_color(color: tuple[int, int, int], amount: int = 15) -> tuple[int, int, int]:
        return tuple(
            int(np.clip(c + rng.integers(-amount, amount + 1), 0, 255))
            for c in color
        )

    base["bg_color_low"] = jitter_color(base["bg_color_low"], 8)
    base["bg_color_high"] = jitter_color(base["bg_color_high"], 12)
    base["particle_color_base"] = jitter_color(base["particle_color_base"], 15)

    # Slight speed/scale variation
    base["bg_noise_speed"] *= 1.0 + rng.uniform(-0.15, 0.15)
    base["bg_noise_scale"] *= 1.0 + rng.uniform(-0.1, 0.1)

    return Preset(seed=seed, **base)
