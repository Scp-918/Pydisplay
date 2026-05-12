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
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self.items = list(items)
        self.on_item = on_item
        self.on_error = on_error
        self.on_finished = on_finished
        self.state = ReplayState.IDLE
        self.last_error: str | None = None
        self.speed = 1.0
        self.total_items = len(self.items)
        self.played_items = 0
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
        self.played_items = 0
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
            for index, item in enumerate(self.items):
                if not _wait_while_paused(self._stop_event, self._pause_event):
                    self.state = ReplayState.IDLE
                    return

                ts = _timestamp_ns(item)
                if previous_ts is not None:
                    delay = max(0.0, (ts - previous_ts) / 1_000_000_000.0 / self.speed)
                    if delay and not _sleep_interruptible(delay, self._stop_event, self._pause_event):
                        self.state = ReplayState.IDLE
                        return
                if self._stop_event.is_set():
                    self.state = ReplayState.IDLE
                    return
                self.on_item(item)
                self.played_items = index + 1
                previous_ts = ts
            self.state = ReplayState.FINISHED
            if self.on_finished:
                self.on_finished()
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


def _wait_while_paused(stop_event: threading.Event, pause_event: threading.Event) -> bool:
    """暂停时阻塞在这里；返回 False 表示回放被 stop 打断。"""
    while pause_event.is_set():
        if stop_event.wait(0.005):
            return False
    return not stop_event.is_set()


def _sleep_interruptible(delay_s: float, stop_event: threading.Event, pause_event: threading.Event) -> bool:
    """按回放节拍等待，同时支持 stop 和 pause。

    Windows 普通 sleep 对 5-10 ms 的短间隔可能明显超时。这里用 perf_counter
    计算绝对 deadline：大于数毫秒时短 sleep，最后阶段只 yield，减少短 sleep
    粒度造成的累计误差。pause 期间不消耗剩余等待时间。
    """
    if delay_s <= 0:
        return not stop_event.is_set()

    deadline = time.perf_counter() + delay_s
    while not stop_event.is_set():
        if pause_event.is_set():
            pause_start = time.perf_counter()
            if not _wait_while_paused(stop_event, pause_event):
                return False
            deadline += time.perf_counter() - pause_start
            continue

        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return True

        if remaining > 0.004:
            wait_s = min(0.002, remaining - 0.002)
            if stop_event.wait(wait_s):
                return False
        else:
            # 让出时间片但不请求毫秒级 sleep，降低 Windows timer 粒度影响。
            time.sleep(0)
    return False
