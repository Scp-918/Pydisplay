"""回放 worker。

ReplayWorker 在后台线程中按时间戳节奏投递数据，避免 GUI 阻塞。
它既可以回放 RawReplayItem，也可以回放 DecodedSample。

支持：
- 0.25x / 0.5x / 1x / 2x / 5x；
- 暂停；
- 继续；
- 停止。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum
import logging
import threading
import time
from typing import Any

from pydisplay.protocol.models import DecodedSample
from .raw_bin_reader import RawReplayItem


LOGGER = logging.getLogger(__name__)

SUPPORTED_SPEEDS = {0.25, 0.5, 1.0, 2.0, 5.0}


class ReplayState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    FINISHED = "finished"
    ERROR = "error"


class ReplayWorker:
    """后台回放 decoded sample 或 raw item。"""

    def __init__(
        self,
        items: Iterable[Any],
        *,
        on_item: Callable[[Any], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.items = list(items)
        self.on_item = on_item
        self.on_error = on_error
        self.state = ReplayState.IDLE
        self.last_error: str | None = None
        self.speed = 1.0
        self._thread: threading.Thread | None = None
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

    def start(self, *, speed: float = 1.0) -> None:
        """启动回放线程。"""
        if speed not in SUPPORTED_SPEEDS:
            raise ValueError(f"unsupported replay speed: {speed}")
        if self._thread and self._thread.is_alive():
            raise RuntimeError("replay is already running")
        self.speed = speed
        self._pause_event.clear()
        self._stop_event.clear()
        self.state = ReplayState.PLAYING
        self._thread = threading.Thread(target=self._run, name="ReplayWorker", daemon=True)
        self._thread.start()

    def pause(self) -> None:
        """暂停回放；线程会停在循环中等待 resume。"""
        if self.state == ReplayState.PLAYING:
            self.state = ReplayState.PAUSED
            self._pause_event.set()

    def resume(self) -> None:
        """继续回放。"""
        if self.state == ReplayState.PAUSED:
            self.state = ReplayState.PLAYING
            self._pause_event.clear()

    def stop(self) -> None:
        self.state = ReplayState.STOPPING
        self._stop_event.set()
        self._pause_event.clear()
        if self._thread is threading.current_thread():
            return
        self.wait()
        if not (self._thread and self._thread.is_alive()) and self.state == ReplayState.STOPPING:
            self.state = ReplayState.IDLE

    def wait(self, timeout_s: float | None = None) -> None:
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout_s)

    def _run(self) -> None:
        previous_ts: int | None = None
        try:
            for item in self.items:
                while self._pause_event.is_set() and not self._stop_event.is_set():
                    time.sleep(0.005)
                if self._stop_event.is_set():
                    self.state = ReplayState.IDLE
                    return

                ts = _timestamp_ns(item)
                if previous_ts is not None:
                    delay = max(0.0, (ts - previous_ts) / 1_000_000_000.0 / self.speed)
                    if delay:
                        _sleep_interruptible(delay, self._stop_event, self._pause_event)
                if self._stop_event.is_set():
                    self.state = ReplayState.IDLE
                    return
                self.on_item(item)
                previous_ts = ts
            self.state = ReplayState.FINISHED
        except Exception as exc:
            LOGGER.exception("Replay failed")
            self.last_error = str(exc)
            self.state = ReplayState.ERROR
            if self.on_error:
                self.on_error(exc)


def _timestamp_ns(item: Any) -> int:
    if isinstance(item, RawReplayItem):
        return item.timestamp_ns
    if isinstance(item, DecodedSample):
        if item.timestamp_pc_ns:
            return item.timestamp_pc_ns
        return int(item.relative_time_s * 1_000_000_000)
    return int(getattr(item, "timestamp_ns", 0))


def _sleep_interruptible(delay_s: float, stop_event: threading.Event, pause_event: threading.Event) -> None:
    """可被 stop/pause 打断的 sleep，避免长时间 sleep 导致停止不及时。"""
    deadline = time.monotonic() + delay_s
    while time.monotonic() < deadline and not stop_event.is_set():
        if pause_event.is_set():
            break
        time.sleep(min(0.01, deadline - time.monotonic()))
