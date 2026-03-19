"""Build configured layers from a preset."""

from __future__ import annotations

from video_generator.effects import (
    AuroraLayer,
    ColorCycleBackground,
    FlowFieldLayer,
    GlowParticleLayer,
    VignetteLayer,
)
from video_generator.layers import Layer, NoiseBackground
from video_generator.particles import ParticleLayer
from video_generator.presets import Preset


def build_layers(preset: Preset, width: int = 1920, height: int = 1080) -> list[Layer]:
    """Create a list of render layers configured from a preset."""
    layers: list[Layer] = []

    # --- GLSL Shader mode ---
    if preset.shader:
        from video_generator.shaders import ShaderLayer, SHADER_PRESETS
        if preset.shader not in SHADER_PRESETS:
            raise ValueError(f"Unknown shader '{preset.shader}'. Available: {list(SHADER_PRESETS.keys())}")
        layers.append(ShaderLayer(
            width, height,
            fragment_shader=SHADER_PRESETS[preset.shader],
            seed=preset.seed,
        ))
        return layers

    # --- Background ---
    if preset.bg_type == "colorcycle" and preset.bg_cycle_colors:
        layers.append(ColorCycleBackground(
            width, height,
            colors=preset.bg_cycle_colors,
            speed=preset.bg_cycle_speed,
            seed=preset.seed,
        ))
    else:
        layers.append(NoiseBackground(
            width, height,
            scale=preset.bg_noise_scale,
            speed=preset.bg_noise_speed,
            color_low=preset.bg_color_low,
            color_high=preset.bg_color_high,
            seed=preset.seed,
        ))

    # --- Aurora (before particles so particles render on top) ---
    if preset.aurora_enabled and preset.aurora_count > 0:
        layers.append(AuroraLayer(
            width, height,
            num_ribbons=preset.aurora_count,
            seed=preset.seed,
            colors=preset.aurora_colors if preset.aurora_colors else None,
            speed=preset.aurora_speed,
            alpha=preset.aurora_alpha,
        ))

    # --- Particles ---
    if preset.particle_type == "glow":
        layers.append(GlowParticleLayer(
            width, height,
            count=preset.particle_count,
            seed=preset.seed,
            colors=preset.particle_glow_colors if preset.particle_glow_colors else None,
            size_range=preset.particle_size_range,
            drift_range=preset.particle_drift_range,
            glow_radius=preset.particle_glow_radius,
            alpha_range=preset.particle_alpha_range,
        ))
    elif preset.particle_type == "flow":
        layers.append(FlowFieldLayer(
            width, height,
            count=preset.particle_count,
            seed=preset.seed,
            color_base=preset.particle_color_base,
            color_variance=preset.particle_color_variance,
            size_range=preset.particle_size_range,
            alpha_range=preset.particle_alpha_range,
            flow_scale=preset.particle_flow_scale,
            trail_length=preset.particle_trail_length,
        ))
    elif preset.particle_type == "basic":
        layers.append(ParticleLayer(
            width, height,
            count=preset.particle_count,
            seed=preset.seed,
            color_base=preset.particle_color_base,
            color_variance=preset.particle_color_variance,
            size_range=preset.particle_size_range,
            drift_range=preset.particle_drift_range,
            alpha_range=preset.particle_alpha_range,
        ))

    # --- Vignette (always last) ---
    if preset.vignette_enabled:
        layers.append(VignetteLayer(
            width, height,
            strength=preset.vignette_strength,
            radius=preset.vignette_radius,
        ))

    return layers
