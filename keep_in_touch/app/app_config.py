"""Application configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for the application.

    Args:
        data_dir: Directory containing app data files.

    Example:
        config = AppConfig(data_dir=Path("~/Documents/KeepInTouch/data").expanduser())
        assert config.people_path.name == "people.jsonl"
    """

    data_dir: Path

    @property
    def people_path(self) -> Path:
        """Path to the people JSONL file."""

        return self.data_dir / "people.jsonl"

    @property
    def interactions_path(self) -> Path:
        """Path to the interactions JSONL file."""

        return self.data_dir / "interactions.jsonl"

    @property
    def settings_path(self) -> Path:
        """Path to the settings JSON file."""

        return self.data_dir / "settings.json"

    @property
    def exports_dir(self) -> Path:
        """Path to exported CSV/JSONL files."""

        return self.data_dir / "exports"

    @property
    def backups_dir(self) -> Path:
        """Path to backups."""

        return self.data_dir / "backups"
