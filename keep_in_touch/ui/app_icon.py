"""Application icon helpers."""

from importlib.resources import files

from PySide6.QtGui import QIcon

APP_ICON_RESOURCE = "assets/icons/app_icon.svg"


def app_icon() -> QIcon:
    """Return the packaged Keep in Touch application icon."""

    icon_path = files("keep_in_touch").joinpath(APP_ICON_RESOURCE)
    return QIcon(str(icon_path))
