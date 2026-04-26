"""Path helpers for local app data."""

from pathlib import Path


def ensure_data_layout(data_dir: Path) -> None:
    """Create the app data layout inside a user-selected folder.

    This function should only be called after the user explicitly chooses a data
    folder. It creates the files and subfolders Keep in Touch needs.

    Args:
        data_dir: User-selected directory that contains the app's data files.

    Example:
        ensure_data_layout(Path("/tmp/my-keep-in-touch-data"))
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