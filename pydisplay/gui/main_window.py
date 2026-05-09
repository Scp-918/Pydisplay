"""Main PySide6 window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from pydisplay.config import WINDOW_TITLE
from pydisplay.version import __version__


class MainWindow(QMainWindow):
    """Empty stage-1 shell window for later panels."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1180, 760)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(f"Pydisplay 上位机 v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("stageTitle")

        subtitle = QLabel("阶段 1：基础窗口已启动，串口和协议模块将在后续阶段接入。")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(1)
        self.setCentralWidget(central)
