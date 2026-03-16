"""CLI entry point: python -m video_generator"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="video-generator",
        description="Generate ambient looping videos for YouTube",
    )
    parser.add_argument("--mood", choices=["ambient", "focus", "trippy"],
                        help="Visual preset (skip for interactive mode)")
    parser.add_argument("--duration", type=float, default=300.0,
                        help="Target video duration in seconds (default: 300)")
    parser.add_argument("--loop-duration", type=float, default=45.0,
                        help="Seamless loop length in seconds (default: 45)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path")
    parser.add_argument("--color", action="append", default=None,
                        help="Custom hex color (e.g. --color ff8800 --color 4400ff). "
                             "1 color = primary, 2 = gradient, 3+ = full palette")

    args = parser.parse_args()

    # Parse colors if provided
    colors = None
    if args.color:
        from video_generator.presets import parse_hex_color
        colors = [parse_hex_color(c) for c in args.color]

    if args.mood is None:
        from video_generator.tui import run_tui
        run_tui()
    else:
        from video_generator.generate import generate
        generate(
            mood=args.mood,
            target_duration=args.duration,
            loop_duration=args.loop_duration,
            seed=args.seed,
            output=args.output,
            colors=colors,
        )


if __name__ == "__main__":
    main()
