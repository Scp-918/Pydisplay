"""串口连接面板。

这个面板只负责用户输入和状态展示：
- 刷新 COM 口；
- 选择端口和波特率；
- 发出打开、关闭、重连信号。
- 发出开始接收、暂停接收信号。

它不直接持有 pyserial.Serial，也不读取串口数据。
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout

from pydisplay.io.port_discovery import list_serial_ports


class SerialPanel(QGroupBox):
    refresh_ports_requested = Signal()
    open_requested = Signal(str, int)
    close_requested = Signal()
    reconnect_requested = Signal()
    start_receiving_requested = Signal()
    pause_receiving_requested = Signal()

    def __init__(self) -> None:
        super().__init__("串口连接")
        self.setMaximumWidth(310)
        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["460800", "230400", "115200", "921600"])
        self.port_combo.setMaximumWidth(175)
        self.baud_combo.setMaximumWidth(120)
        self.status_label = QLabel("未连接")
        self.receive_status_label = QLabel("未接收")

        refresh_button = QPushButton("刷新串口")
        open_button = QPushButton("打开串口")
        close_button = QPushButton("关闭串口")
        reconnect_button = QPushButton("重连")
        start_receive_button = QPushButton("开始接收")
        pause_receive_button = QPushButton("暂停接收")
        refresh_button.clicked.connect(self.refresh_ports)
        open_button.clicked.connect(self._emit_open)
        close_button.clicked.connect(self.close_requested)
        reconnect_button.clicked.connect(self.reconnect_requested)
        start_receive_button.clicked.connect(self.start_receiving_requested)
        pause_receive_button.clicked.connect(self.pause_receiving_requested)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(4)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.addRow("端口", self.port_combo)
        form.addRow("波特率", self.baud_combo)
        form.addRow("状态", self.status_label)
        form.addRow("数据接收", self.receive_status_label)
        buttons = QGridLayout()
        buttons.setSpacing(4)
        for index, button in enumerate((refresh_button, open_button, close_button, reconnect_button, start_receive_button, pause_receive_button)):
            button.setMaximumWidth(86)
            buttons.addWidget(button, index // 3, index % 3)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def refresh_ports(self) -> None:
        """刷新下拉框中的端口列表。"""
        self.refresh_ports_requested.emit()
        ports = list_serial_ports()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.display_name, port.device)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_receiving_paused(self, paused: bool) -> None:
        """显示当前后台数据接收是否暂停。"""
        self.set_receive_status("已暂停" if paused else "接收中")

    def set_receive_status(self, text: str) -> None:
        self.receive_status_label.setText(text)

    def _emit_open(self) -> None:
        """把当前选择的端口和波特率通过 signal 发给主窗口。"""
        port = self.port_combo.currentData() or self.port_combo.currentText()
        if port:
            self.open_requested.emit(str(port), int(self.baud_combo.currentText()))
