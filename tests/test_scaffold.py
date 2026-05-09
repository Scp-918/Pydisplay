from __future__ import annotations

import logging

from pydisplay.config import APP_NAME, WINDOW_TITLE
from pydisplay.logging_config import configure_logging
from pydisplay.version import __version__


def test_project_metadata() -> None:
    assert APP_NAME == "Pydisplay"
    assert "上位机" in WINDOW_TITLE
    assert __version__ == "0.1.0"


def test_configure_logging_is_idempotent() -> None:
    configure_logging(logging.DEBUG)
    before = len(logging.getLogger().handlers)
    configure_logging(logging.INFO)
    after = len(logging.getLogger().handlers)
    assert after == before
