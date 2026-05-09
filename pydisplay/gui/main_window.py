"""Main PySide6 window."""

from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QScrollArea, QSplitter, QVBoxLayout, QWidget

from pydisplay.config import WINDOW_TITLE
from pydisplay.gui.widgets.control_panel import ControlPanel
from pydisplay.gui.widgets.health_panel import HealthPanel
from pydisplay.gui.widgets.plot_panel import PlotPanel
from pydisplay.gui.widgets.recorder_panel import RecorderPanel
from pydisplay.gui.widgets.replay_panel import ReplayPanel
from pydisplay.gui.widgets.serial_panel import SerialPanel
from pydisplay.io.serial_manager import SerialManager
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
    """Main application window with panels and non-blocking worker wiring."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1360, 860)

        self.health = HealthMonitor()
        self.recorder = RecorderWorker()
        self.pipeline = DataPipeline(
            decode_config=DecodeConfig(k=5.0),
            recorder=self.recorder,
            health=self.health,
            on_decoded=self._handle_decoded_sample,
        )
        self.serial_manager = SerialManager(
            on_chunk=self.pipeline.handle_raw_chunk,
            on_error=lambda exc: self._show_error("串口异常", str(exc)),
            on_state_changed=lambda status: self.serial_panel.set_status(status.state.name),
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
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.serial_panel)
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(self.recorder_panel)
        left_layout.addWidget(self.replay_panel)
        left_layout.addWidget(self.health_panel)
        left_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)
        splitter.addWidget(self.plot_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _wire_signals(self) -> None:
        self.serial_panel.open_requested.connect(self._open_serial)
        self.serial_panel.close_requested.connect(self._close_serial)
        self.serial_panel.reconnect_requested.connect(self._reconnect_serial)
        self.control_panel.k_value_changed.connect(self._update_k)
        self.control_panel.control_command_requested.connect(self._send_control)
        self.recorder_panel.start_recording_requested.connect(self._start_recording)
        self.recorder_panel.stop_recording_requested.connect(self._stop_recording)
        self.replay_panel.start_replay_requested.connect(self._start_replay)
        self.replay_panel.pause_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.pause())
        self.replay_panel.resume_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.resume())
        self.replay_panel.stop_replay_requested.connect(lambda: self.replay_worker and self.replay_worker.stop())

    def _open_serial(self, port: str, baudrate: int) -> None:
        self.serial_manager.open(port, baudrate)
        self.health.set_states(serial_state=self.serial_manager.state.name)

    def _close_serial(self) -> None:
        self.serial_manager.close()
        self.health.set_states(serial_state=self.serial_manager.state.name)

    def _reconnect_serial(self) -> None:
        self.serial_manager.reconnect()
        self.health.set_states(serial_state=self.serial_manager.state.name)

    def _send_control(self, metadata) -> None:
        result = self.serial_manager.write_control(metadata)
        if result.success:
            self.statusBar().showMessage("控制命令已发送")
        else:
            self._show_error("发送失败", result.error_message or "串口未连接")

    def _update_k(self, value: float) -> None:
        self.pipeline.decode_config.k = value

    def _start_recording(self, base_dir: str, experiment_name: str) -> None:
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
        self.recorder.stop()
        self.recorder_panel.set_status("记录已停止")
        self.health.set_states(recording_state=self.recorder.state.name)

    def _start_replay(self, replay_type: str, path: str, speed: float) -> None:
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
        if isinstance(item, RawReplayItem):
            self.pipeline.handle_raw_chunk(RawChunk(timestamp_ns=item.timestamp_ns, data=item.data, port="replay"))
        elif isinstance(item, DecodedSample):
            self._handle_decoded_sample(item)
            self.health.add_decoded_sample()

    def _handle_decoded_sample(self, sample: DecodedSample) -> None:
        self.plot_panel.add_sample(sample)

    def _refresh_health(self) -> None:
        self.health.set_states(
            serial_state=self.serial_manager.state.name,
            recording_state=self.recorder.state.name,
            replay_state=self.replay_worker.state.name if self.replay_worker else "IDLE",
        )
        self.health.set_queue_sizes(
            plot_queue_size=len(self.plot_panel.buffer),
            record_queue_size=self.recorder.queue_size,
        )
        snapshot = self.health.snapshot(now_ns=time.time_ns())
        self.health_panel.update_snapshot(snapshot)

    def _show_error(self, title: str, message: str) -> None:
        self.health.set_last_error(message)
        self.statusBar().showMessage(f"{title}：{message}")
        QMessageBox.warning(self, title, message)
