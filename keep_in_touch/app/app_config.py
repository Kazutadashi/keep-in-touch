"""Application configuration.

The app can start without a data folder. A data folder is only required once the
user chooses one from the UI.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """Runtime app configuration.

    Args:
        data_dir: User-selected folder containing Keep in Touch data files.

    Example:
        config = AppConfig()
        assert not config.has_data_dir

        config = AppConfig(data_dir=Path("/tmp/keep-in-touch"))
        assert config.people_path.name == "people.jsonl"
    """

    data_dir: Path | None = None

    @property
    def has_data_dir(self) -> bool:
        """Return whether a usable data folder is configured."""

        return self.data_dir is not None

    @property
    def people_path(self) -> Path:
        """Return the people JSONL path."""

        return self.require_data_dir() / "people.jsonl"

    @property
    def interactions_path(self) -> Path:
        """Return the interactions JSONL path."""

        return self.require_data_dir() / "interactions.jsonl"

    @property
    def settings_path(self) -> Path:
        """Return the data-folder-local settings path."""

        return self.require_data_dir() / "settings.json"

    @property
    def exports_dir(self) -> Path:
        """Return the exports directory path."""

        return self.require_data_dir() / "exports"

    @property
    def backups_dir(self) -> Path:
        """Return the backups directory path."""

        return self.require_data_dir() / "backups"

    def require_data_dir(self) -> Path:
        """Return the configured data folder or raise a clear error.

        Raises:
            RuntimeError: If no data folder has been selected.
        """

        if self.data_dir is None:
            raise RuntimeError("No Keep in Touch data folder has been selected.")
        return self.data_dir