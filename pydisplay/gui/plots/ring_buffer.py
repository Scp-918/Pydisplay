"""实时绘图 ring buffer。

绘图只需要最近 N 秒数据，不能把所有历史样本无限 append 到 list。
SampleRingBuffer 使用 deque(maxlen=capacity)，超过容量会自动丢弃最旧样本。
这只影响 GUI 显示，不影响 RecorderWorker 的全量记录。
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from pydisplay.protocol.models import DecodedSample


class SampleRingBuffer:
    """Store only the most recent decoded samples."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._samples: deque[DecodedSample] = deque(maxlen=capacity)

    def append(self, sample: DecodedSample) -> None:
        self._samples.append(sample)

    def extend(self, samples: Iterable[DecodedSample]) -> None:
        for sample in samples:
            self.append(sample)

    def clear(self) -> None:
        self._samples.clear()

    def __len__(self) -> int:
        return len(self._samples)

    def get_series(self, key: str, window_seconds: float | None = None) -> tuple[list[float], list[float]]:
        """取出某条曲线的 x/y 数据，必要时只返回最近 window_seconds 秒。"""
        samples = list(self._samples)
        if not samples:
            return [], []
        if window_seconds is not None:
            cutoff = samples[-1].relative_time_s - window_seconds
            samples = [sample for sample in samples if sample.relative_time_s >= cutoff]
        x = [float(sample.relative_time_s) for sample in samples]
        y = [float(getattr(sample, key)) for sample in samples]
        return x, y
