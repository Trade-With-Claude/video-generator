"""Visual preset system — mood-based configurations for the renderer."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Preset:
    """Complete visual configuration for a render."""

    name: str
    seed: int

    # Background
    bg_type: str = "noise"  # "noise" or "colorcycle"
    bg_color_low: tuple[int, int, int] = (5, 20, 60)
    bg_color_high: tuple[int, int, int] = (20, 100, 140)
    bg_noise_scale: float = 3.0
    bg_noise_speed: float = 1.0
    bg_cycle_colors: list[tuple[int, int, int]] = field(default_factory=list)
    bg_cycle_speed: float = 1.0

    # Particles
    particle_type: str = "basic"  # "basic", "glow", "flow", or "none"
    particle_count: int = 1000
    particle_color_base: tuple[int, int, int] = (100, 200, 220)
    particle_color_variance: float = 25.0
    particle_size_range: tuple[float, float] = (1.5, 4.0)
    particle_drift_range: tuple[float, float] = (50.0, 200.0)
    particle_alpha_range: tuple[float, float] = (0.2, 0.7)
    particle_glow_colors: list[tuple[int, int, int]] = field(default_factory=list)
    particle_glow_radius: float = 15.0
    particle_flow_scale: float = 3.0
    particle_trail_length: int = 6

    # Aurora
    aurora_enabled: bool = False
    aurora_count: int = 5
    aurora_colors: list[tuple[int, int, int]] = field(default_factory=list)
    aurora_speed: float = 1.0
    aurora_alpha: float = 0.4

    # Vignette
    vignette_enabled: bool = True
    vignette_strength: float = 0.7
    vignette_radius: float = 0.8


def _ambient_base() -> dict:
    return dict(
        name="ambient",
        bg_type="colorcycle",
        bg_cycle_colors=[
            (3, 15, 55),
            (8, 30, 70),
            (5, 20, 65),
            (10, 10, 50),
        ],
        bg_cycle_speed=0.5,
        # Keep noise params for fallback
        bg_color_low=(3, 12, 45),
        bg_color_high=(15, 70, 110),
        bg_noise_scale=2.5,
        bg_noise_speed=0.6,
        # Glow particles
        particle_type="glow",
        particle_count=250,
        particle_glow_colors=[
            (60, 180, 220),
            (100, 200, 255),
            (40, 140, 200),
        ],
        particle_glow_radius=18.0,
        particle_size_range=(5.0, 14.0),
        particle_drift_range=(30.0, 100.0),
        particle_alpha_range=(0.25, 0.65),
        particle_color_base=(80, 180, 210),
        particle_color_variance=25.0,
        # Aurora
        aurora_enabled=True,
        aurora_count=4,
        aurora_colors=[
            (30, 180, 160),
            (60, 100, 200),
            (80, 50, 180),
            (20, 150, 140),
        ],
        aurora_speed=0.6,
        aurora_alpha=0.35,
        # Vignette
        vignette_enabled=True,
        vignette_strength=0.8,
        vignette_radius=0.75,
    )


def _focus_base() -> dict:
    return dict(
        name="focus",
        bg_type="noise",
        bg_color_low=(8, 4, 2),
        bg_color_high=(40, 28, 10),
        bg_noise_scale=3.5,
        bg_noise_speed=0.5,
        bg_cycle_colors=[],
        bg_cycle_speed=1.0,
        # Flow field particles
        particle_type="flow",
        particle_count=1200,
        particle_color_base=(230, 180, 60),
        particle_color_variance=25.0,
        particle_size_range=(1.0, 2.5),
        particle_drift_range=(40.0, 120.0),
        particle_alpha_range=(0.3, 0.65),
        particle_flow_scale=3.5,
        particle_trail_length=8,
        particle_glow_colors=[],
        particle_glow_radius=15.0,
        # No aurora for clean look
        aurora_enabled=False,
        aurora_count=0,
        aurora_colors=[],
        aurora_speed=1.0,
        aurora_alpha=0.4,
        # Subtle vignette
        vignette_enabled=True,
        vignette_strength=0.9,
        vignette_radius=0.7,
    )


def _trippy_base() -> dict:
    return dict(
        name="trippy",
        bg_type="colorcycle",
        bg_cycle_colors=[
            (25, 5, 50),
            (50, 10, 80),
            (15, 20, 60),
            (40, 5, 70),
        ],
        bg_cycle_speed=1.5,
        bg_color_low=(20, 5, 40),
        bg_color_high=(60, 15, 100),
        bg_noise_scale=4.0,
        bg_noise_speed=1.8,
        # Flow field particles (dense, fast)
        particle_type="flow",
        particle_count=2000,
        particle_color_base=(220, 100, 240),
        particle_color_variance=50.0,
        particle_size_range=(1.0, 3.5),
        particle_drift_range=(60.0, 200.0),
        particle_alpha_range=(0.3, 0.75),
        particle_flow_scale=4.0,
        particle_trail_length=5,
        particle_glow_colors=[
            (255, 80, 200),
            (80, 200, 255),
            (200, 255, 80),
        ],
        particle_glow_radius=12.0,
        # Aurora with vivid colors
        aurora_enabled=True,
        aurora_count=6,
        aurora_colors=[
            (255, 60, 180),
            (60, 200, 255),
            (180, 255, 60),
            (255, 160, 40),
            (120, 80, 255),
            (60, 255, 180),
        ],
        aurora_speed=1.4,
        aurora_alpha=0.3,
        # Vignette
        vignette_enabled=True,
        vignette_strength=0.6,
        vignette_radius=0.85,
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

    def jitter_color(color: tuple[int, int, int], amount: int = 15) -> tuple[int, int, int]:
        return tuple(
            int(np.clip(c + rng.integers(-amount, amount + 1), 0, 255))
            for c in color
        )

    base["bg_color_low"] = jitter_color(base["bg_color_low"], 8)
    base["bg_color_high"] = jitter_color(base["bg_color_high"], 12)
    base["particle_color_base"] = jitter_color(base["particle_color_base"], 15)

    base["bg_noise_speed"] *= 1.0 + rng.uniform(-0.15, 0.15)
    base["bg_noise_scale"] *= 1.0 + rng.uniform(-0.1, 0.1)

    return Preset(seed=seed, **base)
