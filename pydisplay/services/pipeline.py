"""Realtime data pipeline wiring serial chunks to parser, decoder, recorder, and GUI queues."""

from __future__ import annotations

import logging
from collections.abc import Callable

from pydisplay.io.serial_reader import RawChunk
from pydisplay.protocol.decoder import decode_frame
from pydisplay.protocol.models import DecodeConfig, DecodedSample
from pydisplay.protocol.parser import FrameParser
from pydisplay.recorder.recorder_worker import RecorderWorker
from .data_bus import DataBus
from .health_monitor import HealthMonitor


LOGGER = logging.getLogger(__name__)


class DataPipeline:
    """Pure-Python pipeline; GUI polls DataBus instead of processing raw streams."""

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
        self.decode_config = decode_config
        self.recorder = recorder
        self.bus = bus or DataBus()
        self.health = health or HealthMonitor()
        self.on_decoded = on_decoded

    def handle_raw_chunk(self, chunk: RawChunk) -> None:
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
            self.health.add_decoded_sample()
            self.bus.put_decoded_for_plot(sample)
            if self.recorder and self.recorder.state.value == "recording":
                self.recorder.enqueue_decoded(sample)
            if self.on_decoded:
                self.on_decoded(sample)
