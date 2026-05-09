"""Serial connection panel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from pydisplay.io.port_discovery import list_serial_ports


class SerialPanel(QGroupBox):
    refresh_ports_requested = Signal()
    open_requested = Signal(str, int)
    close_requested = Signal()
    reconnect_requested = Signal()

    def __init__(self) -> None:
        super().__init__("串口连接")
        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["460800", "230400", "115200", "921600"])
        self.status_label = QLabel("未连接")

        refresh_button = QPushButton("刷新串口")
        open_button = QPushButton("打开串口")
        close_button = QPushButton("关闭串口")
        reconnect_button = QPushButton("重连")
        refresh_button.clicked.connect(self.refresh_ports)
        open_button.clicked.connect(self._emit_open)
        close_button.clicked.connect(self.close_requested)
        reconnect_button.clicked.connect(self.reconnect_requested)

        form = QFormLayout()
        form.addRow("端口", self.port_combo)
        form.addRow("波特率", self.baud_combo)
        form.addRow("状态", self.status_label)
        buttons = QHBoxLayout()
        for button in (refresh_button, open_button, close_button, reconnect_button):
            buttons.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def refresh_ports(self) -> None:
        self.refresh_ports_requested.emit()
        ports = list_serial_ports()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.display_name, port.device)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _emit_open(self) -> None:
        port = self.port_combo.currentData() or self.port_combo.currentText()
        if port:
            self.open_requested.emit(str(port), int(self.baud_combo.currentText()))
