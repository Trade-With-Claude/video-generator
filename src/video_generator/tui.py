"""Interactive TUI using questionary."""

from __future__ import annotations

import questionary

from video_generator.generate import generate
from video_generator.presets import AVAILABLE_MOODS


def run_tui() -> None:
    """Interactive prompt-based interface for video generation."""
    print("\n  Video Generator\n")

    mood = questionary.select(
        "Select mood:",
        choices=AVAILABLE_MOODS,
        default="ambient",
    ).ask()
    if mood is None:
        return

    duration_str = questionary.text(
        "Target duration (seconds):",
        default="300",
        validate=lambda v: v.replace(".", "", 1).isdigit() or "Enter a number",
    ).ask()
    if duration_str is None:
        return
    target_duration = float(duration_str)

    loop_str = questionary.text(
        "Loop length (seconds):",
        default="45",
        validate=lambda v: v.replace(".", "", 1).isdigit() or "Enter a number",
    ).ask()
    if loop_str is None:
        return
    loop_duration = float(loop_str)

    seed_str = questionary.text(
        "Seed (leave empty for random):",
        default="",
    ).ask()
    if seed_str is None:
        return
    seed = int(seed_str) if seed_str.strip() else None

    print()
    confirm = questionary.confirm(
        f"Generate {mood} video — {target_duration}s from {loop_duration}s loop?",
        default=True,
    ).ask()
    if not confirm:
        print("Cancelled.")
        return

    print()
    output = generate(
        mood=mood,
        target_duration=target_duration,
        loop_duration=loop_duration,
        seed=seed,
    )
    print(f"\nVideo ready: {output}")
