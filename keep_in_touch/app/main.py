"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from keep_in_touch.app.app_config import AppConfig
from keep_in_touch.storage.app_settings import load_remembered_data_dir
from keep_in_touch.ui.app_icon import app_icon
from keep_in_touch.ui.main_window import MainWindow


def main() -> int:
    """Start the Qt application.

    The app always opens, even when no data folder is configured. If a previous
    data folder was remembered, it is loaded automatically. Otherwise, the main
    window opens in a no-data-folder state and lets the user choose one.

    Returns:
        Process exit code.

    Example:
        # From a terminal:
        # keep-in-touch
    """

    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())

    remembered_data_dir = load_remembered_data_dir()
    config = AppConfig(data_dir=remembered_data_dir)

    window = MainWindow(config=config)
    window.resize(window.preferred_initial_size())
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
