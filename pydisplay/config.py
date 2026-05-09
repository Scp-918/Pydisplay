"""Static project configuration."""

from __future__ import annotations

from pathlib import Path


APP_NAME = "Pydisplay"
WINDOW_TITLE = "Pydisplay 上位机"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "pydisplay.log"
