"""回放控制面板。

用户选择 raw_frames.bin 或 decoded.csv，选择速度，然后发出开始/暂停/继续/停止信号。
实际文件读取和节奏控制由 replay 模块完成。
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QVBoxLayout


class ReplayPanel(QGroupBox):
    start_replay_requested = Signal(str, str, float)
    pause_replay_requested = Signal()
    resume_replay_requested = Signal()
    stop_replay_requested = Signal()

    def __init__(self) -> None:
        super().__init__("回放")
        self.setMaximumWidth(310)
        self.raw_path = QLineEdit()
        self.csv_path = QLineEdit()
        self.raw_path.setMaximumWidth(220)
        self.csv_path.setMaximumWidth(220)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["raw_frames.bin", "decoded.csv"])
        self.type_combo.setMaximumWidth(150)
        self.speed_combo = QComboBox()
        for speed in ("0.25x", "0.5x", "1x", "2x", "5x"):
            self.speed_combo.addItem(speed, float(speed.rstrip("x")))
        self.speed_combo.setMaximumWidth(90)

        start_button = QPushButton("开始")
        pause_button = QPushButton("暂停")
        resume_button = QPushButton("继续")
        stop_button = QPushButton("停止")
        for button in (start_button, pause_button, resume_button, stop_button):
            button.setMaximumWidth(70)
        start_button.clicked.connect(self._emit_start)
        pause_button.clicked.connect(self.pause_replay_requested)
        resume_button.clicked.connect(self.resume_replay_requested)
        stop_button.clicked.connect(self.stop_replay_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        layout.addWidget(QLabel("raw_frames.bin"))
        layout.addWidget(self.raw_path)
        layout.addWidget(QLabel("decoded.csv"))
        layout.addWidget(self.csv_path)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.speed_combo)
        buttons = QGridLayout()
        buttons.setSpacing(4)
        for index, button in enumerate((start_button, pause_button, resume_button, stop_button)):
            buttons.addWidget(button, index // 2, index % 2)
        layout.addLayout(buttons)

    def _emit_start(self) -> None:
        """根据当前回放类型选择对应路径，并发出开始回放信号。"""
        replay_type = self.type_combo.currentText()
        path = self.raw_path.text() if replay_type == "raw_frames.bin" else self.csv_path.text()
        self.start_replay_requested.emit(replay_type, path, self.speed_combo.currentData())
