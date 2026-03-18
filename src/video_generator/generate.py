"""Main generation pipeline — orchestrates preset → render → extend."""

from __future__ import annotations

import time
from pathlib import Path

import json
import subprocess

from video_generator.config import Settings
from video_generator.ffmpeg import FFmpegError, FFmpegPipe, check_ffmpeg
from video_generator.layers import LayerCompositor
from video_generator.loop import extend_loop
from video_generator.presets import apply_custom_colors, get_preset
from video_generator.render import build_layers
from video_generator.time_loop import TimeLoop


def get_audio_duration(audio_path: str | Path) -> float:
    """Get duration of an audio file in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(audio_path),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise FFmpegError(f"Cannot read audio file: {audio_path}")
    return float(json.loads(result.stdout)["format"]["duration"])


def merge_audio_video(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Merge video and audio into a final MP4."""
    cmd = [
        check_ffmpeg(), "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise FFmpegError(f"Audio merge failed: {result.stderr.decode()}")
    return output_path


def generate(
    mood: str = "ambient",
    target_duration: float = 300.0,
    loop_duration: float = 45.0,
    seed: int | None = None,
    output: str | Path | None = None,
    colors: list[tuple[int, int, int]] | None = None,
    audio: str | Path | None = None,
) -> Path:
    """Generate a video end-to-end. Returns the path to the output MP4.

    Args:
        mood: Preset name (ambient, focus, trippy).
        target_duration: Final video length in seconds.
        loop_duration: Length of the rendered seamless loop in seconds.
        seed: Random seed for reproducibility. Auto-generated if None.
        output: Output file path. Auto-generated if None.
        colors: Custom color palette as list of (r,g,b) tuples. Overrides preset colors.
        audio: Path to audio file. If provided, auto-detects duration and merges.
    """
    check_ffmpeg()

    # Auto-detect duration from audio
    if audio is not None:
        audio = Path(audio)
        audio_dur = get_audio_duration(audio)
        target_duration = audio_dur
        print(f"  Audio: {audio.name} ({audio_dur:.1f}s)")

    if seed is None:
        seed = int(time.time()) % 100000

    settings = Settings(
        loop_duration=loop_duration,
        target_duration=target_duration,
        seed=seed,
    )

    if output is None:
        output = settings.output_dir / f"{mood}_{seed}.mp4"
    output = Path(output)

    preset = get_preset(mood, seed=seed)
    if colors:
        preset = apply_custom_colors(preset, colors)
    layers = build_layers(preset, settings.width, settings.height)
    compositor = LayerCompositor(layers, settings.width, settings.height)
    loop = TimeLoop(settings.fps, loop_duration)

    # Render the seamless loop
    loop_path = output.parent / f".loop_{output.stem}.mp4"
    loop_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(loop)
    t0 = time.time()

    print(f"Generating '{mood}' video (seed={seed})")
    print(f"  Loop: {loop_duration}s → Extended: {target_duration}s")
    print(f"  Rendering {total} frames at {settings.width}x{settings.height}...")

    with FFmpegPipe(loop_path, settings) as pipe:
        for i, t, theta in loop:
            pipe.write_frame(compositor.render_frame(t, theta))
            if (i + 1) % settings.fps == 0:
                elapsed = time.time() - t0
                fps_actual = (i + 1) / elapsed
                remaining = (total - i - 1) / fps_actual if fps_actual > 0 else 0
                sec = (i + 1) // settings.fps
                print(f"  {sec}/{int(loop_duration)}s  ({fps_actual:.1f} fps, ~{remaining:.0f}s remaining)")

    # Extend loop to target duration
    if target_duration > loop_duration:
        print(f"  Extending to {target_duration}s...")
        extend_loop(loop_path, output, target_duration, settings)
        loop_path.unlink(missing_ok=True)
    else:
        loop_path.rename(output)

    # Merge audio if provided
    if audio is not None:
        print(f"  Merging audio...")
        video_only = output
        if output.stem.endswith("_video"):
            final = output.with_stem(output.stem.replace("_video", ""))
        else:
            video_only = output.with_stem(output.stem + "_video")
            output.rename(video_only)
            final = output
        merge_audio_video(video_only, audio, final)
        video_only.unlink(missing_ok=True)
        output = final

    size_mb = output.stat().st_size / (1024 * 1024)
    elapsed_total = time.time() - t0
    print(f"  Done! {output} ({size_mb:.1f} MB, {elapsed_total:.0f}s total)")

    return output
