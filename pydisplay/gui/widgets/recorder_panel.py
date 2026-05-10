"""数据记录面板。

这个面板只让用户选择记录路径和实验名，并发出开始/停止记录请求。
实际文件写入由 RecorderWorker 后台线程完成。
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QVBoxLayout


class RecorderPanel(QGroupBox):
    start_recording_requested = Signal(str, str)
    stop_recording_requested = Signal()

    def __init__(self) -> None:
        super().__init__("数据记录")
        self.setMaximumWidth(310)
        self.path_edit = QLineEdit("records")
        self.name_edit = QLineEdit("experiment")
        self.path_edit.setMaximumWidth(220)
        self.name_edit.setMaximumWidth(220)
        self.status_label = QLabel("未记录")
        start_button = QPushButton("开始记录")
        stop_button = QPushButton("停止记录")
        start_button.setMaximumWidth(96)
        stop_button.setMaximumWidth(96)
        start_button.clicked.connect(lambda: self.start_recording_requested.emit(self.path_edit.text(), self.name_edit.text()))
        stop_button.clicked.connect(self.stop_recording_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        layout.addWidget(QLabel("记录路径"))
        layout.addWidget(self.path_edit)
        layout.addWidget(QLabel("文件名前缀"))
        layout.addWidget(self.name_edit)
        buttons = QGridLayout()
        buttons.setSpacing(4)
        buttons.addWidget(start_button, 0, 0)
        buttons.addWidget(stop_button, 0, 1)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
