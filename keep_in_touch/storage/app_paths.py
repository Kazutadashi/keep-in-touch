"""Path helpers for local app data."""

from pathlib import Path


def default_data_dir() -> Path:
    """Return the default data directory.

    Example:
        path = default_data_dir()
        assert path.name == "data"
    """

    return Path.home() / "Documents" / "KeepInTouch" / "data"


def ensure_data_layout(data_dir: Path) -> None:
    """Create the data directory and empty files if needed.

    Args:
        data_dir: Directory that contains the app's data files.

    Example:
        ensure_data_layout(Path("/tmp/keep-in-touch-data"))
    """

    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "exports").mkdir(exist_ok=True)
    (data_dir / "backups").mkdir(exist_ok=True)

    for filename in ("people.jsonl", "interactions.jsonl"):
        path = data_dir / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")

    settings_path = data_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text("{}\n", encoding="utf-8")
