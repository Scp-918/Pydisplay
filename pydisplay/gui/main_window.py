"""GUI 主窗口。

MainWindow 负责把各个面板组装起来，并连接用户操作与后台服务：
- 串口面板 -> SerialManager；
- 控制面板 -> SerialWriter / protocol.commands；
- 记录面板 -> RecorderWorker；
- 回放面板 -> ReplayWorker；
- 串口或回放数据 -> DataPipeline -> PlotPanel；
- HealthMonitor -> HealthPanel。

重要原则：
GUI 主线程只做界面显示和 signal/slot 调度，不直接阻塞读串口、不直接写文件。
"""

from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QScrollArea, QSplitter, QVBoxLayout, QWidget

from pydisplay.config import DEFAULT_K_VALUE, WINDOW_TITLE
from pydisplay.gui.widgets.control_panel import ControlPanel
from pydisplay.gui.widgets.health_panel import HealthPanel
from pydisplay.gui.widgets.plot_panel import PlotPanel
from pydisplay.gui.widgets.recorder_panel import RecorderPanel
from pydisplay.gui.widgets.replay_panel import ReplayPanel
from pydisplay.gui.widgets.serial_panel import SerialPanel
from pydisplay.io.serial_manager import SerialManager, SerialState, SerialStatus
from pydisplay.io.serial_reader import RawChunk
from pydisplay.protocol.models import DecodeConfig, DecodedSample
from pydisplay.recorder.metadata import build_metadata
from pydisplay.recorder.recorder_worker import RecorderWorker
from pydisplay.replay.decoded_csv_reader import read_decoded_csv
from pydisplay.replay.raw_bin_reader import RawReplayItem, read_raw_replay_items
from pydisplay.replay.replay_worker import ReplayWorker
from pydisplay.services.health_monitor import HealthMonitor
from pydisplay.services.pipeline import DataPipeline
from pydisplay.version import __version__


class MainWindow(QMainWindow):
    """Pydisplay 主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1360, 860)

        # 后台服务对象。它们和 GUI 分开，便于测试和后续替换实现。
        self.health = HealthMonitor()
        self.recorder = RecorderWorker()
        self.pipeline = DataPipeline(
            decode_config=DecodeConfig(k=DEFAULT_K_VALUE),
            recorder=self.recorder,
            health=self.health,
            on_decoded=self._handle_decoded_sample,
        )
        self.serial_manager = SerialManager(
            on_chunk=self.pipeline.handle_raw_chunk,
            on_error=lambda exc: self._show_error("串口异常", str(exc)),
            on_state_changed=self._handle_serial_status,
        )
        self.replay_worker: ReplayWorker | None = None

        self.serial_panel = SerialPanel()
        self.control_panel = ControlPanel()
        self.recorder_panel = RecorderPanel()
        self.health_panel = HealthPanel()
        self.replay_panel = ReplayPanel()
        self.plot_panel = PlotPanel()
        self.plot_panel.on_plot_frame = self.health.add_plot_frame

        self._wire_signals()
        self._build_layout()

        self.health_timer = QTimer(self)
        self.health_timer.setInterval(500)
        self.health_timer.timeout.connect(self._refresh_health)
        self.health_timer.start()
        self.statusBar().showMessage(f"Pydisplay 上位机 v{__version__}")
        self.serial_panel.refresh_ports()

    def _build_layout(self) -> None:
        """创建左侧控制区和右侧绘图区。"""
        left = QWidget()
        left.setMinimumWidth(260)
        left.setMaximumWidth(360)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)
        left_layout.addWidget(self.serial_panel)
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(self.recorder_panel)
        left_layout.addWidget(self.health_panel)
        left_layout.addWidget(self.replay_panel)
        left_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left)
        scroll.setMinimumWidth(270)
        scroll.setMaximumWidth(380)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)
        splitter.addWidget(self.plot_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 1020])

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _wire_signals(self) -> None:
        """把各个面板的 Qt signal 接到 MainWindow 的处理函数。"""
        self.serial_panel.open_requested.connect(self._open_serial)
        self.serial_panel.close_requested.connect(self._close_serial)
        self.serial_panel.reconnect_requested.connect(self._reconnect_serial)
        self.serial_panel.start_receiving_requested.connect(self._start_receiving)
        self.serial_panel.pause_receiving_requested.connect(self._pause_receiving)
        self.control_panel.k_value_changed.connect(self._update_k)
        self.control_panel.control_command_requested.connect(self._send_control)
        self.recorder_panel.start_recording_requested.connect(self._start_recording)
        self.recorder_panel.stop_recording_requested.connect(self._stop_recording)
        self.replay_panel.start_replay_requested.connect(self._start_replay)
        self.replay_panel.pause_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.pause())
        self.replay_panel.resume_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.resume())
        self.replay_panel.stop_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.stop())

    def _open_serial(self, port: str, baudrate: int) -> None:
        """打开串口；真正读取由 SerialReader 后台线程完成。"""
        self.serial_manager.open(port, baudrate)
        self.health.set_states(serial_state=self._serial_state_text())

    def _close_serial(self) -> None:
        if getattr(self.recorder.state, "value", None) == "recording":
            self._stop_recording()
        self.serial_manager.close()
        self.health.set_states(serial_state=self._serial_state_text(), recording_state=self.recorder.state.name)

    def _reconnect_serial(self) -> None:
        self.serial_manager.reconnect()
        self.health.set_states(serial_state=self._serial_state_text())

    def _start_receiving(self) -> None:
        """继续从已打开串口读取数据。"""
        if not self.serial_manager.is_connected():
            self._show_error("接收不可用", "请先打开串口")
            return
        self.serial_manager.start_receiving()
        self.health.set_states(serial_state=self._serial_state_text())

    def _pause_receiving(self) -> None:
        """暂停后台串口读取，但保持串口连接和记录系统状态不变。"""
        if not self.serial_manager.is_connected():
            self._show_error("接收不可用", "请先打开串口")
            return
        self.serial_manager.pause_receiving()
        self.health.set_states(serial_state=self._serial_state_text())

    def _send_control(self, metadata) -> None:
        """发送控制命令；bytes 编码由 protocol.commands 完成。"""
        result = self.serial_manager.write_control(metadata)
        if result.success:
            self.pipeline.decode_config.gyro_range_code = metadata.gyro_range
            self.pipeline.decode_config.accel_range_code = metadata.accel_range
            self.statusBar().showMessage("控制命令已发送")
        else:
            self._show_error("发送失败", result.error_message or "串口未连接")

    def _update_k(self, value: float) -> None:
        self.pipeline.decode_config.k = value

    def _start_recording(self, base_dir: str, experiment_name: str) -> None:
        """启动后台记录，不在 GUI 主线程写数据文件。"""
        metadata = build_metadata(
            record_path=base_dir,
            serial_port=self.serial_manager.status.port,
            baudrate=self.serial_manager.status.baudrate,
            k=self.pipeline.decode_config.k,
        )
        try:
            session_dir = self.recorder.start(base_dir=base_dir, experiment_name=experiment_name, metadata=metadata)
        except Exception as exc:
            self._show_error("记录启动失败", str(exc))
            return
        self.recorder_panel.set_status(f"记录中：{session_dir}")
        self.health.set_states(recording_state=self.recorder.state.name)

    def _stop_recording(self) -> None:
        try:
            self.recorder.stop()
        except Exception as exc:
            self.recorder_panel.set_status(f"记录停止失败：{exc}")
            self._show_error("记录停止失败", str(exc))
            self.health.set_states(recording_state=self.recorder.state.name)
            return
        self.recorder_panel.set_status("记录已停止")
        self.health.set_states(recording_state=self.recorder.state.name)

    def _start_replay(self, replay_type: str, path: str, speed: float) -> None:
        """启动回放；初版要求回放和实时串口互斥。"""
        if self.serial_manager.is_connected():
            self._show_error("回放不可用", "请先关闭实时串口连接")
            return
        try:
            if replay_type == "raw_frames.bin":
                items = read_raw_replay_items(path)
            else:
                items = read_decoded_csv(path)
        except Exception as exc:
            self._show_error("回放文件错误", str(exc))
            return

        self.replay_worker = ReplayWorker(items, on_item=self._handle_replay_item, on_error=lambda exc: self._show_error("回放异常", str(exc)))
        self.replay_worker.start(speed=speed)
        self.health.set_states(replay_state=self.replay_worker.state.name)

    def _handle_replay_item(self, item) -> None:
        """处理回放 worker 投递的数据。"""
        if isinstance(item, RawReplayItem):
            self.pipeline.handle_raw_chunk(RawChunk(timestamp_ns=item.timestamp_ns, data=item.data, port="replay"))
        elif isinstance(item, DecodedSample):
            self._handle_decoded_sample(item)
            self.health.add_decoded_sample()

    def _handle_decoded_sample(self, sample: DecodedSample) -> None:
        self.plot_panel.add_sample(sample)

    def _refresh_health(self) -> None:
        """低频刷新健康面板，避免每帧更新 QLabel。"""
        self.health.set_states(
            serial_state=self._serial_state_text(),
            recording_state=self.recorder.state.name,
            replay_state=self.replay_worker.state.name if self.replay_worker else "IDLE",
        )
        self.health.set_queue_sizes(
            plot_queue_size=len(self.plot_panel.buffer),
            record_queue_size=self.recorder.queue_size,
        )
        snapshot = self.health.snapshot(now_ns=time.time_ns())
        self.health_panel.update_snapshot(snapshot)

    def _handle_serial_status(self, status: SerialStatus) -> None:
        """把 SerialManager 状态同步到串口面板。"""
        self.serial_panel.set_status(status.state.name)
        if status.state != SerialState.CONNECTED:
            self.serial_panel.set_receive_status("未接收")
        else:
            self.serial_panel.set_receiving_paused(status.receive_paused)

    def _serial_state_text(self) -> str:
        if self.serial_manager.state == SerialState.CONNECTED and self.serial_manager.status.receive_paused:
            return "CONNECTED/PAUSED"
        return self.serial_manager.state.name

    def _show_error(self, title: str, message: str) -> None:
        self.health.set_last_error(message)
        self.statusBar().showMessage(f"{title}：{message}")
        QMessageBox.warning(self, title, message)
