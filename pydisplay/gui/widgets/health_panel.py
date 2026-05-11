"""链路健康显示面板。

该面板只显示 HealthSnapshot 中已经算好的结果。
它不做复杂统计，也不每帧刷新；刷新频率由 MainWindow 的 QTimer 控制。
"""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QSizePolicy

from pydisplay.services.health_monitor import HealthSnapshot


class HealthPanel(QGroupBox):
    def __init__(self) -> None:
        super().__init__("链路健康")
        self.setMaximumWidth(360)
        self.labels: dict[str, QLabel] = {}
        layout = QFormLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        for key, title in (
            ("serial_state", "串口状态"),
            ("recording_state", "记录状态"),
            ("replay_state", "回放状态"),
            ("bytes_per_second", "bytes/s"),
            ("valid_frame_rate", "有效帧率"),
            ("bad_frame_rate", "坏帧率"),
            ("bad_frames", "坏帧数量"),
            ("bad_frame_ratio", "坏帧比例"),
            ("lost_frames", "丢包数量"),
            ("lost_frame_ratio", "丢包比例"),
            ("duplicate_seq_count", "序号重复"),
            ("seq_reset_count", "序号重置/乱序"),
            ("resync_count", "resync 次数"),
            ("serial_buffer_bytes", "串口缓冲"),
            ("parser_buffer_bytes", "解析缓冲"),
            ("plot_fps", "绘图 FPS"),
            ("record_queue_size", "记录队列"),
            ("last_error", "最近错误"),
        ):
            label = QLabel("--")
            label.setMinimumWidth(220)
            label.setMaximumWidth(260)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            label.setWordWrap(key == "last_error")
            if key == "last_error":
                label.setMinimumHeight(34)
            self.labels[key] = label
            layout.addRow(title, label)

    def update_snapshot(self, snapshot: HealthSnapshot) -> None:
        """把 HealthSnapshot 格式化成用户可读中文指标。"""
        values = {
            "serial_state": snapshot.serial_state,
            "recording_state": snapshot.recording_state,
            "replay_state": snapshot.replay_state,
            "bytes_per_second": f"{snapshot.bytes_per_second:.1f}",
            "valid_frame_rate": f"{snapshot.valid_frame_rate:.1f} Hz",
            "bad_frame_rate": f"{snapshot.bad_frame_rate:.1f} Hz",
            "bad_frames": str(snapshot.bad_frames),
            "bad_frame_ratio": f"{snapshot.bad_frame_ratio:.2%}",
            "lost_frames": str(snapshot.lost_frames),
            "lost_frame_ratio": f"{snapshot.lost_frame_ratio:.2%}",
            "duplicate_seq_count": str(snapshot.duplicate_seq_count),
            "seq_reset_count": str(snapshot.seq_reset_count),
            "resync_count": str(snapshot.resync_count),
            "serial_buffer_bytes": f"{snapshot.serial_buffer_bytes} bytes",
            "parser_buffer_bytes": f"{snapshot.parser_buffer_bytes} bytes",
            "plot_fps": f"{snapshot.plot_fps:.1f}",
            "record_queue_size": str(snapshot.record_queue_size),
            "last_error": snapshot.last_error or "--",
        }
        for key, value in values.items():
            self.labels[key].setText(value)
