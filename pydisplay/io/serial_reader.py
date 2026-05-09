"""Background serial reader."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import threading
import time


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RawChunk:
    timestamp_ns: int
    data: bytes
    port: str


class SerialReader:
    """Read raw bytes from a serial-like object on a background thread."""

    def __init__(
        self,
        serial_obj: object,
        *,
        port: str,
        on_chunk: Callable[[RawChunk], None],
        on_error: Callable[[Exception], None] | None = None,
        poll_interval_s: float = 0.005,
        max_read_size: int = 4096,
    ) -> None:
        self.serial_obj = serial_obj
        self.port = port
        self.on_chunk = on_chunk
        self.on_error = on_error
        self.poll_interval_s = poll_interval_s
        self.max_read_size = max_read_size
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.bytes_received_total = 0
        self.last_rx_time_ns: int | None = None
        self.read_error_count = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name=f"SerialReader-{self.port}", daemon=True)
        self._thread.start()

    def stop(self, timeout_s: float = 1.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout_s)

    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def read_once(self, timestamp_ns: int | None = None) -> RawChunk | None:
        waiting = self.serial_buffer_bytes
        read_size = min(max(1, waiting), self.max_read_size)
        data = self.serial_obj.read(read_size)
        if not data:
            return None

        chunk = RawChunk(
            timestamp_ns=time.time_ns() if timestamp_ns is None else timestamp_ns,
            data=bytes(data),
            port=self.port,
        )
        self.bytes_received_total += len(chunk.data)
        self.last_rx_time_ns = chunk.timestamp_ns
        self.on_chunk(chunk)
        return chunk

    @property
    def serial_buffer_bytes(self) -> int:
        try:
            return int(getattr(self.serial_obj, "in_waiting", 0))
        except Exception:
            LOGGER.exception("Failed to read serial in_waiting")
            return 0

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.read_once()
            except Exception as exc:
                self.read_error_count += 1
                LOGGER.exception("Serial read failed on %s", self.port)
                if self.on_error:
                    self.on_error(exc)
                self._stop_event.set()
                break
            time.sleep(self.poll_interval_s)
