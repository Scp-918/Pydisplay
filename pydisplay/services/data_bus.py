"""线程安全数据队列。

DataBus 用于 worker 和 GUI 之间传递数据。
绘图队列有上限：当 GUI 来不及画图时，只丢弃显示层旧数据，
不能丢弃记录数据。
"""

from __future__ import annotations

import queue

from pydisplay.io.serial_reader import RawChunk
from pydisplay.protocol.models import DecodedSample, ParsedFrame


class DataBus:
    def __init__(self, *, max_plot_queue: int = 5000) -> None:
        self.raw_chunks: queue.Queue[RawChunk] = queue.Queue()
        self.parsed_frames: queue.Queue[ParsedFrame] = queue.Queue()
        self.decoded_samples: queue.Queue[DecodedSample] = queue.Queue(maxsize=max_plot_queue)

    def put_decoded_for_plot(self, sample: DecodedSample) -> None:
        """把 decoded sample 放入绘图队列，满了就丢弃最旧显示数据。"""
        try:
            self.decoded_samples.put_nowait(sample)
        except queue.Full:
            # GUI display may drop old samples; recorder receives data separately.
            _ = self.decoded_samples.get_nowait()
            self.decoded_samples.put_nowait(sample)
