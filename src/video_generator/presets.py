"""Visual preset system — mood-based configurations for the renderer."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Preset:
    """Complete visual configuration for a render."""

    name: str
    seed: int

    # Shader (if set, uses GLSL instead of layer pipeline)
    shader: str = ""  # "tunnel", "cubes", "geometry", "terrain", or "" for layer-based

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
        particle_glow_radius=8.0,
        particle_size_range=(3.0, 8.0),
        particle_drift_range=(30.0, 100.0),
        particle_alpha_range=(0.35, 0.75),
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
        # Dense glow particles — vivid multicolor
        particle_type="glow",
        particle_count=400,
        particle_color_base=(220, 100, 240),
        particle_color_variance=50.0,
        particle_size_range=(4.0, 10.0),
        particle_drift_range=(80.0, 250.0),
        particle_alpha_range=(0.4, 0.85),
        particle_flow_scale=4.0,
        particle_trail_length=5,
        particle_glow_colors=[
            (255, 80, 200),
            (80, 200, 255),
            (200, 255, 80),
            (255, 160, 40),
        ],
        particle_glow_radius=10.0,
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


def _tunnel_base() -> dict:
    return dict(
        name="tunnel",
        shader="tunnel",
        bg_type="noise",
        bg_color_low=(2, 10, 30), bg_color_high=(10, 50, 70),
        bg_noise_scale=3.0, bg_noise_speed=1.0, bg_cycle_colors=[], bg_cycle_speed=1.0,
        particle_type="none", particle_count=0,
        particle_color_base=(0, 200, 220), particle_color_variance=0,
        particle_size_range=(1.0, 1.0), particle_drift_range=(0, 0),
        particle_alpha_range=(0, 0), particle_glow_colors=[], particle_glow_radius=0,
        particle_flow_scale=0, particle_trail_length=0,
        aurora_enabled=False, aurora_count=0, aurora_colors=[], aurora_speed=0, aurora_alpha=0,
        vignette_enabled=False, vignette_strength=0, vignette_radius=0,
    )


def _cubes_base() -> dict:
    return dict(
        name="cubes",
        shader="cubes",
        bg_type="noise",
        bg_color_low=(2, 5, 15), bg_color_high=(10, 30, 50),
        bg_noise_scale=3.0, bg_noise_speed=1.0, bg_cycle_colors=[], bg_cycle_speed=1.0,
        particle_type="none", particle_count=0,
        particle_color_base=(0, 200, 220), particle_color_variance=0,
        particle_size_range=(1.0, 1.0), particle_drift_range=(0, 0),
        particle_alpha_range=(0, 0), particle_glow_colors=[], particle_glow_radius=0,
        particle_flow_scale=0, particle_trail_length=0,
        aurora_enabled=False, aurora_count=0, aurora_colors=[], aurora_speed=0, aurora_alpha=0,
        vignette_enabled=False, vignette_strength=0, vignette_radius=0,
    )


def _geometry_base() -> dict:
    return dict(
        name="geometry",
        shader="geometry",
        bg_type="noise",
        bg_color_low=(2, 2, 10), bg_color_high=(10, 10, 40),
        bg_noise_scale=3.0, bg_noise_speed=1.0, bg_cycle_colors=[], bg_cycle_speed=1.0,
        particle_type="none", particle_count=0,
        particle_color_base=(100, 50, 200), particle_color_variance=0,
        particle_size_range=(1.0, 1.0), particle_drift_range=(0, 0),
        particle_alpha_range=(0, 0), particle_glow_colors=[], particle_glow_radius=0,
        particle_flow_scale=0, particle_trail_length=0,
        aurora_enabled=False, aurora_count=0, aurora_colors=[], aurora_speed=0, aurora_alpha=0,
        vignette_enabled=False, vignette_strength=0, vignette_radius=0,
    )


def _orb_base() -> dict:
    return dict(
        name="orb",
        shader="orb",
        bg_type="noise",
        bg_color_low=(1, 2, 10), bg_color_high=(5, 20, 40),
        bg_noise_scale=3.0, bg_noise_speed=1.0, bg_cycle_colors=[], bg_cycle_speed=1.0,
        particle_type="none", particle_count=0,
        particle_color_base=(0, 150, 180), particle_color_variance=0,
        particle_size_range=(1.0, 1.0), particle_drift_range=(0, 0),
        particle_alpha_range=(0, 0), particle_glow_colors=[], particle_glow_radius=0,
        particle_flow_scale=0, particle_trail_length=0,
        aurora_enabled=False, aurora_count=0, aurora_colors=[], aurora_speed=0, aurora_alpha=0,
        vignette_enabled=False, vignette_strength=0, vignette_radius=0,
    )


def _shader_preset(name: str) -> dict:
    """Create a minimal preset for shader-based rendering."""
    return dict(
        name=name, shader=name,
        bg_type="noise", bg_color_low=(2, 5, 15), bg_color_high=(10, 30, 50),
        bg_noise_scale=3.0, bg_noise_speed=1.0, bg_cycle_colors=[], bg_cycle_speed=1.0,
        particle_type="none", particle_count=0,
        particle_color_base=(0, 200, 220), particle_color_variance=0,
        particle_size_range=(1.0, 1.0), particle_drift_range=(0, 0),
        particle_alpha_range=(0, 0), particle_glow_colors=[], particle_glow_radius=0,
        particle_flow_scale=0, particle_trail_length=0,
        aurora_enabled=False, aurora_count=0, aurora_colors=[], aurora_speed=0, aurora_alpha=0,
        vignette_enabled=False, vignette_strength=0, vignette_radius=0,
    )


_PRESETS = {
    "ambient": _ambient_base,
    "focus": _focus_base,
    "trippy": _trippy_base,
    "tunnel": _tunnel_base,
    "cubes": _cubes_base,
    "geometry": _geometry_base,
    "orb": _orb_base,
    "torus": lambda: _shader_preset("torus"),
    "octahedron": lambda: _shader_preset("octahedron"),
    "warp": lambda: _shader_preset("warp"),
    "dna": lambda: _shader_preset("dna"),
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


def parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    """Parse a hex color like '#ff8800' or 'ff8800' to (r, g, b)."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color: '{hex_str}' — expected 6 hex digits")
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def apply_custom_colors(preset: Preset, colors: list[tuple[int, int, int]]) -> Preset:
    """Override a preset's colors with custom ones.

    Colors are applied as:
    - 1 color: used as primary everywhere
    - 2 colors: bg gradient low/high
    - 3+ colors: bg cycle, particle colors, aurora colors
    """
    if not colors:
        return preset

    if len(colors) == 1:
        c = colors[0]
        # Darken for background, use as-is for particles/aurora
        dark = tuple(max(0, v // 4) for v in c)
        mid = tuple(max(0, v // 2) for v in c)
        preset.bg_color_low = dark
        preset.bg_color_high = mid
        preset.bg_cycle_colors = [dark, mid, dark]
        preset.particle_color_base = c
        if preset.particle_glow_colors:
            preset.particle_glow_colors = [c]
        if preset.aurora_colors:
            preset.aurora_colors = [c, mid]
    elif len(colors) == 2:
        preset.bg_color_low = colors[0]
        preset.bg_color_high = colors[1]
        preset.bg_cycle_colors = [colors[0], colors[1], colors[0]]
        preset.particle_color_base = colors[1]
        if preset.particle_glow_colors:
            preset.particle_glow_colors = list(colors)
        if preset.aurora_colors:
            preset.aurora_colors = list(colors)
    else:
        # 3+ colors: full palette
        preset.bg_cycle_colors = [
            tuple(max(0, v // 3) for v in c) for c in colors[:4]
        ]
        preset.bg_color_low = tuple(max(0, v // 4) for v in colors[0])
        preset.bg_color_high = tuple(max(0, v // 2) for v in colors[1])
        preset.particle_color_base = colors[0]
        if preset.particle_glow_colors:
            preset.particle_glow_colors = list(colors)
        if preset.aurora_colors:
            preset.aurora_colors = list(colors)

    return preset
