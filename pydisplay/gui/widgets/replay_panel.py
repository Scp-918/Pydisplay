"""Replay controls."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout


class ReplayPanel(QGroupBox):
    start_replay_requested = Signal(str, str, float)
    pause_replay_requested = Signal()
    resume_replay_requested = Signal()
    stop_replay_requested = Signal()

    def __init__(self) -> None:
        super().__init__("回放")
        self.raw_path = QLineEdit()
        self.csv_path = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["raw_frames.bin", "decoded.csv"])
        self.speed_combo = QComboBox()
        for speed in ("0.25x", "0.5x", "1x", "2x", "5x"):
            self.speed_combo.addItem(speed, float(speed.rstrip("x")))

        start_button = QPushButton("开始")
        pause_button = QPushButton("暂停")
        resume_button = QPushButton("继续")
        stop_button = QPushButton("停止")
        start_button.clicked.connect(self._emit_start)
        pause_button.clicked.connect(self.pause_replay_requested)
        resume_button.clicked.connect(self.resume_replay_requested)
        stop_button.clicked.connect(self.stop_replay_requested)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("raw_frames.bin"))
        layout.addWidget(self.raw_path)
        layout.addWidget(QLabel("decoded.csv"))
        layout.addWidget(self.csv_path)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.speed_combo)
        buttons = QHBoxLayout()
        for button in (start_button, pause_button, resume_button, stop_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def _emit_start(self) -> None:
        replay_type = self.type_combo.currentText()
        path = self.raw_path.text() if replay_type == "raw_frames.bin" else self.csv_path.text()
        self.start_replay_requested.emit(replay_type, path, self.speed_combo.currentData())
