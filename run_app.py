"""Run Keep in Touch from a project checkout.

This file is intentionally tiny so new contributors can press "Run" in an IDE
without needing to understand Python packaging first.

Example:
    python run_app.py
"""

from keep_in_touch.app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
