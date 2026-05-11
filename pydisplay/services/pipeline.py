"""实时数据 pipeline。

Pipeline 是整个数据链路的“中间调度器”：

RawChunk
  -> FrameParser
  -> ParsedFrame
  -> decode_frame
  -> DecodedSample
  -> RecorderWorker / GUI Plot / HealthMonitor

它不直接操作 GUI 控件，也不直接打开串口。
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from pydisplay.io.serial_reader import RawChunk
from pydisplay.protocol.decoder import decode_frame
from pydisplay.protocol.models import DecodeConfig, DecodedSample
from pydisplay.protocol.parser import FrameParser
from pydisplay.protocol.sequence import FrameSequenceTracker
from pydisplay.recorder.recorder_worker import RecorderWorker
from .data_bus import DataBus
from .health_monitor import HealthMonitor


LOGGER = logging.getLogger(__name__)


class DataPipeline:
    """纯 Python 数据流水线，方便测试和复用。"""

    def __init__(
        self,
        *,
        decode_config: DecodeConfig,
        parser: FrameParser | None = None,
        recorder: RecorderWorker | None = None,
        bus: DataBus | None = None,
        health: HealthMonitor | None = None,
        on_decoded: Callable[[DecodedSample], None] | None = None,
    ) -> None:
        self.parser = parser or FrameParser()
        self.sequence_tracker = FrameSequenceTracker()
        self.decode_config = decode_config
        self.recorder = recorder
        self.bus = bus or DataBus()
        self.health = health or HealthMonitor()
        self.on_decoded = on_decoded

    def reset_stream_state(self) -> None:
        """Reset parser, sequence tracker, and decoder time zero for a new input stream."""
        self.parser = FrameParser(max_buffer_bytes=self.parser.max_buffer_bytes)
        self.sequence_tracker = FrameSequenceTracker()
        self.decode_config.start_time_ns = None

    def handle_raw_chunk(self, chunk: RawChunk) -> None:
        """处理串口 reader 或 raw 回放送来的一段原始 bytes。"""
        self.health.add_raw_bytes(len(chunk.data))
        if self.recorder and self.recorder.state.value == "recording":
            self.recorder.enqueue_raw_chunk(chunk.timestamp_ns, chunk.data)
        frames = self.parser.feed(chunk.data, timestamp_ns=chunk.timestamp_ns)
        self.health.update_parser_stats(self.parser.stats)
        for frame in frames:
            if self.recorder and self.recorder.state.value == "recording":
                self.recorder.enqueue_valid_frame(frame.timestamp_ns, frame.raw)
            try:
                sample = decode_frame(frame, self.decode_config)
            except Exception as exc:
                LOGGER.exception("Decode failed")
                self.health.add_decode_error(str(exc))
                continue
            sequence = self.sequence_tracker.update(frame.frame_seq)
            sample.absolute_seq_u64 = sequence.absolute_seq_u64
            sample.seq_gap = sequence.seq_gap
            sample.lost_before = sequence.lost_before
            sample.segment_id = sequence.segment_id
            if sequence.is_duplicate:
                sample.warnings.append("duplicate firmware frame_seq")
            if sequence.is_reset:
                sample.warnings.append("firmware frame_seq reset or severe reorder")
            self.health.add_sequence_result(
                lost_before=sequence.lost_before,
                duplicate=sequence.is_duplicate,
                reset=sequence.is_reset,
            )
            self.health.add_decoded_sample()
            self.bus.put_decoded_for_plot(sample)
            if self.recorder and self.recorder.state.value == "recording":
                self.recorder.enqueue_decoded(sample)
            if self.on_decoded:
                self.on_decoded(sample)
