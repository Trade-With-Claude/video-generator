"""Build configured layers from a preset."""

from __future__ import annotations

from video_generator.layers import Layer, NoiseBackground
from video_generator.particles import ParticleLayer
from video_generator.presets import Preset


def build_layers(preset: Preset, width: int = 1920, height: int = 1080) -> list[Layer]:
    """Create a list of render layers configured from a preset."""
    bg = NoiseBackground(
        width,
        height,
        scale=preset.bg_noise_scale,
        speed=preset.bg_noise_speed,
        color_low=preset.bg_color_low,
        color_high=preset.bg_color_high,
        seed=preset.seed,
    )

    particles = ParticleLayer(
        width,
        height,
        count=preset.particle_count,
        seed=preset.seed,
        color_base=preset.particle_color_base,
        color_variance=preset.particle_color_variance,
        size_range=preset.particle_size_range,
        drift_range=preset.particle_drift_range,
        alpha_range=preset.particle_alpha_range,
    )

    return [bg, particles]
