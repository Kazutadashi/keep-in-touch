"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from keep_in_touch.app.app_config import AppConfig
from keep_in_touch.storage.app_paths import default_data_dir, ensure_data_layout
from keep_in_touch.ui.main_window import MainWindow


def main() -> int:
    """Start the Qt application.

    Returns:
        Process exit code.

    Example:
        # From a terminal:
        # keep-in-touch
    """

    data_dir = default_data_dir()
    ensure_data_layout(data_dir)

    app = QApplication(sys.argv)
    window = MainWindow(config=AppConfig(data_dir=data_dir))
    window.resize(1200, 720)
    window.show()
    return app.exec()
