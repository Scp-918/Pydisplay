"""Streaming parser for the confirmed 49-byte firmware data frame."""

from __future__ import annotations

import time

from .constants import (
    CHECKSUM_OFFSET,
    FRAME_HEADER,
    FRAME_LENGTH,
    FRAME_TAIL,
    PAYLOAD_END_OFFSET,
    PAYLOAD_START_OFFSET,
    TAIL_OFFSET,
)
from .models import ParsedFrame, ParserStats


class FrameParser:
    """Parse a continuous byte stream into valid firmware frames."""

    def __init__(self, max_buffer_bytes: int = FRAME_LENGTH * 8) -> None:
        if max_buffer_bytes < FRAME_LENGTH:
            raise ValueError("max_buffer_bytes must be at least one frame")
        self.max_buffer_bytes = max_buffer_bytes
        self._buffer = bytearray()
        self.stats = ParserStats()

    def feed(self, data: bytes, timestamp_ns: int | None = None) -> list[ParsedFrame]:
        if not data:
            self._update_buffer_stat()
            return []

        timestamp = timestamp_ns if timestamp_ns is not None else time.time_ns()
        self.stats.total_bytes += len(data)
        self._buffer.extend(data)
        frames: list[ParsedFrame] = []

        while self._buffer:
            self._discard_noise_before_header()
            if len(self._buffer) < FRAME_LENGTH:
                break

            candidate = bytes(self._buffer[:FRAME_LENGTH])
            if candidate[TAIL_OFFSET : TAIL_OFFSET + 1] != FRAME_TAIL:
                self._mark_bad_frame("tail error", tail=True)
                self._resync_after_bad_candidate()
                continue

            expected = calculate_checksum(candidate[PAYLOAD_START_OFFSET : PAYLOAD_END_OFFSET + 1])
            if candidate[CHECKSUM_OFFSET] != expected:
                self._mark_bad_frame("checksum error", checksum=True)
                self._resync_after_bad_candidate()
                continue

            del self._buffer[:FRAME_LENGTH]
            self.stats.total_frames += 1
            self.stats.valid_frames += 1
            # 固件没有帧序号；sample_seq 使用 PC 端解析出的有效帧序号。
            frames.append(
                ParsedFrame(
                    timestamp_ns=timestamp,
                    raw=candidate,
                    payload=candidate[PAYLOAD_START_OFFSET : PAYLOAD_END_OFFSET + 1],
                    frame_seq=None,
                    sample_seq=self.stats.valid_frames,
                    checksum_ok=True,
                )
            )

        self._cap_buffer()
        self._update_buffer_stat()
        return frames

    def _discard_noise_before_header(self) -> None:
        index = self._buffer.find(FRAME_HEADER)
        if index > 0:
            del self._buffer[:index]
            self.stats.noise_bytes += index
            return
        if index == 0:
            return

        keep = 1 if self._buffer.endswith(FRAME_HEADER[:1]) else 0
        discard = len(self._buffer) - keep
        if discard > 0:
            del self._buffer[:discard]
            self.stats.noise_bytes += discard

    def _mark_bad_frame(self, message: str, *, checksum: bool = False, tail: bool = False) -> None:
        self.stats.total_frames += 1
        self.stats.bad_frames += 1
        self.stats.resync_count += 1
        self.stats.last_error = message
        if checksum:
            self.stats.checksum_errors += 1
        if tail:
            self.stats.tail_errors += 1

    def _resync_after_bad_candidate(self) -> None:
        # 保留当前坏帧后续字节，继续寻找下一个 0xAA 0xBB。
        del self._buffer[0]

    def _cap_buffer(self) -> None:
        if len(self._buffer) <= self.max_buffer_bytes:
            return

        keep = 1 if self._buffer.endswith(FRAME_HEADER[:1]) else 0
        discard = len(self._buffer) - keep
        del self._buffer[:discard]
        self.stats.noise_bytes += discard
        self.stats.length_errors += 1
        self.stats.last_error = "buffer overflow"

    def _update_buffer_stat(self) -> None:
        self.stats.buffer_bytes = len(self._buffer)


def calculate_checksum(payload: bytes) -> int:
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return checksum
