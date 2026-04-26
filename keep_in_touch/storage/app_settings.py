"""Small app-level settings stored outside the user data folder.

This file stores only application preferences, such as the last selected data
folder. It does not store people, interactions, notes, or personal relationship
data.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_SETTINGS_FILENAME = "settings.json"


def app_settings_path() -> Path:
    """Return the app-level settings file path.

    The path follows common platform conventions:

    - Linux: ~/.config/keep-in-touch/settings.json
    - macOS: ~/Library/Application Support/keep-in-touch/settings.json
    - Windows: %APPDATA%/keep-in-touch/settings.json

    Example:
        path = app_settings_path()
        assert path.name == "settings.json"
    """

    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return base / "keep-in-touch" / APP_SETTINGS_FILENAME


def load_remembered_data_dir() -> Path | None:
    """Load the remembered data folder, if one exists and is still valid.

    Returns:
        The remembered data folder, or None.

    Example:
        remembered = load_remembered_data_dir()
        if remembered is not None:
            print(remembered)
    """

    settings_path = app_settings_path()
    if not settings_path.exists():
        return None

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    raw_path = data.get("data_dir")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None

    data_dir = Path(raw_path).expanduser()
    if not data_dir.exists() or not data_dir.is_dir():
        return None

    return data_dir


def save_remembered_data_dir(data_dir: Path) -> None:
    """Remember the user's selected data folder for future launches.

    Args:
        data_dir: Folder selected by the user.

    Example:
        save_remembered_data_dir(Path("/tmp/keep-in-touch-data"))
    """

    settings_path = app_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "data_dir": str(data_dir.expanduser().resolve()),
    }
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def clear_remembered_data_dir() -> None:
    """Forget the remembered data folder.

    This does not delete the user's data folder. It only removes the app setting.
    """

    settings_path = app_settings_path()
    if settings_path.exists():
        settings_path.unlink()