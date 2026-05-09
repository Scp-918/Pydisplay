"""Application bootstrap for Pydisplay."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from .logging_config import configure_logging


LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pydisplay GUI")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="create the Qt application and main window, print the title, then exit",
    )
    return parser.parse_args(argv)


def create_app(argv: Sequence[str] | None = None):
    """Create the QApplication and main window without entering the event loop."""

    from PySide6.QtWidgets import QApplication

    from .gui.main_window import MainWindow

    qt_argv = list(argv or [])
    app = QApplication.instance() or QApplication(qt_argv)
    window = MainWindow()
    return app, window


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    LOGGER.info("Starting Pydisplay")

    app, window = create_app(sys.argv[:1])
    if args.smoke_test:
        print(window.windowTitle())
        return 0

    window.show()
    return int(app.exec())
