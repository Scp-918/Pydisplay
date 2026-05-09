"""Health and performance counters."""

from __future__ import annotations

from dataclasses import dataclass

from pydisplay.protocol.models import ParserStats


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    timestamp_ns: int
    serial_state: str
    recording_state: str
    replay_state: str
    bytes_per_second: float
    total_bytes: int
    serial_buffer_bytes: int
    valid_frame_rate: float
    bad_frame_rate: float
    valid_frames: int
    bad_frames: int
    bad_frame_ratio: float
    resync_count: int
    parser_buffer_bytes: int
    decoded_sample_rate: float
    decode_error_count: int
    plot_fps: float
    plot_queue_size: int
    record_queue_size: int
    record_error_count: int
    last_error: str | None


class HealthMonitor:
    """Accumulate counters and return low-frequency snapshots for the GUI."""

    def __init__(self) -> None:
        self.total_bytes = 0
        self.serial_buffer_bytes = 0
        self.valid_frames = 0
        self.bad_frames = 0
        self.resync_count = 0
        self.parser_buffer_bytes = 0
        self.decode_error_count = 0
        self.decoded_samples = 0
        self.plot_frames = 0
        self.plot_queue_size = 0
        self.record_queue_size = 0
        self.record_error_count = 0
        self.serial_state = "DISCONNECTED"
        self.recording_state = "IDLE"
        self.replay_state = "IDLE"
        self.last_error: str | None = None
        self._last_ns: int | None = None
        self._last_total_bytes = 0
        self._last_valid_frames = 0
        self._last_bad_frames = 0
        self._last_decoded_samples = 0
        self._last_plot_frames = 0

    def add_raw_bytes(self, count: int, *, serial_buffer_bytes: int | None = None) -> None:
        self.total_bytes += count
        if serial_buffer_bytes is not None:
            self.serial_buffer_bytes = serial_buffer_bytes

    def update_parser_stats(self, stats: ParserStats) -> None:
        self.valid_frames = stats.valid_frames
        self.bad_frames = stats.bad_frames
        self.resync_count = stats.resync_count
        self.parser_buffer_bytes = stats.buffer_bytes
        if stats.last_error:
            self.last_error = stats.last_error

    def add_decoded_sample(self) -> None:
        self.decoded_samples += 1

    def add_decode_error(self, message: str) -> None:
        self.decode_error_count += 1
        self.last_error = message

    def add_plot_frame(self) -> None:
        self.plot_frames += 1

    def set_queue_sizes(self, *, plot_queue_size: int | None = None, record_queue_size: int | None = None) -> None:
        if plot_queue_size is not None:
            self.plot_queue_size = plot_queue_size
        if record_queue_size is not None:
            self.record_queue_size = record_queue_size

    def set_states(
        self,
        *,
        serial_state: str | None = None,
        recording_state: str | None = None,
        replay_state: str | None = None,
    ) -> None:
        if serial_state is not None:
            self.serial_state = serial_state
        if recording_state is not None:
            self.recording_state = recording_state
        if replay_state is not None:
            self.replay_state = replay_state

    def set_record_error_count(self, count: int) -> None:
        self.record_error_count = count

    def set_last_error(self, message: str | None) -> None:
        self.last_error = message

    def snapshot(self, *, now_ns: int) -> HealthSnapshot:
        elapsed = 0.0 if self._last_ns is None else max((now_ns - self._last_ns) / 1_000_000_000.0, 1e-9)
        bytes_per_second = 0.0 if self._last_ns is None else (self.total_bytes - self._last_total_bytes) / elapsed
        valid_frame_rate = 0.0 if self._last_ns is None else (self.valid_frames - self._last_valid_frames) / elapsed
        bad_frame_rate = 0.0 if self._last_ns is None else (self.bad_frames - self._last_bad_frames) / elapsed
        decoded_sample_rate = 0.0 if self._last_ns is None else (self.decoded_samples - self._last_decoded_samples) / elapsed
        plot_fps = 0.0 if self._last_ns is None else (self.plot_frames - self._last_plot_frames) / elapsed
        total_frames = self.valid_frames + self.bad_frames
        bad_frame_ratio = self.bad_frames / total_frames if total_frames else 0.0

        snapshot = HealthSnapshot(
            timestamp_ns=now_ns,
            serial_state=self.serial_state,
            recording_state=self.recording_state,
            replay_state=self.replay_state,
            bytes_per_second=bytes_per_second,
            total_bytes=self.total_bytes,
            serial_buffer_bytes=self.serial_buffer_bytes,
            valid_frame_rate=valid_frame_rate,
            bad_frame_rate=bad_frame_rate,
            valid_frames=self.valid_frames,
            bad_frames=self.bad_frames,
            bad_frame_ratio=bad_frame_ratio,
            resync_count=self.resync_count,
            parser_buffer_bytes=self.parser_buffer_bytes,
            decoded_sample_rate=decoded_sample_rate,
            decode_error_count=self.decode_error_count,
            plot_fps=plot_fps,
            plot_queue_size=self.plot_queue_size,
            record_queue_size=self.record_queue_size,
            record_error_count=self.record_error_count,
            last_error=self.last_error,
        )
        self._last_ns = now_ns
        self._last_total_bytes = self.total_bytes
        self._last_valid_frames = self.valid_frames
        self._last_bad_frames = self.bad_frames
        self._last_decoded_samples = self.decoded_samples
        self._last_plot_frames = self.plot_frames
        return snapshot
