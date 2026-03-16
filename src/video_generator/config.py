"""Configuration via Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Video generator settings with sensible defaults."""

    model_config = {"env_prefix": "VG_"}

    width: int = 1920
    height: int = 1080
    fps: int = 30
    output_dir: Path = Path("output")
    loop_duration: float = 45.0  # seconds
    seed: int | None = None
