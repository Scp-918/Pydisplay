"""固件数据帧流式 parser。

串口读出来的是连续 bytes，不能假设一次 read 正好是一帧。
这个 parser 使用内部 buffer 处理：

1. 帧头前噪声；
2. 半包；
3. 粘包；
4. checksum 错误；
5. 帧尾错误；
6. 坏帧后的 resync；
7. buffer 不能无限增长。

输入：任意长度 bytes。
输出：0 个或多个 `ParsedFrame`。
"""

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
    """把连续 byte stream 解析成固件有效帧。"""

    def __init__(self, max_buffer_bytes: int = FRAME_LENGTH * 8) -> None:
        if max_buffer_bytes < FRAME_LENGTH:
            raise ValueError("max_buffer_bytes must be at least one frame")
        self.max_buffer_bytes = max_buffer_bytes
        self._buffer = bytearray()
        self.stats = ParserStats()

    def feed(self, data: bytes, timestamp_ns: int | None = None) -> list[ParsedFrame]:
        """喂入一段串口 bytes，并返回当前能解析出的完整有效帧。"""
        if not data:
            self._update_buffer_stat()
            return []

        timestamp = timestamp_ns if timestamp_ns is not None else time.time_ns()
        self.stats.total_bytes += len(data)
        self._buffer.extend(data)
        frames: list[ParsedFrame] = []

        while self._buffer:
            # 每轮先把 buffer 对齐到帧头。若只有半个帧头 0xAA，会保留下来等下一次 feed。
            self._discard_noise_before_header()
            if len(self._buffer) < FRAME_LENGTH:
                break

            candidate = bytes(self._buffer[:FRAME_LENGTH])
            if candidate[TAIL_OFFSET : TAIL_OFFSET + 1] != FRAME_TAIL:
                # 帧尾错误说明当前位置大概率不是一帧，统计后向后滑动 1 字节重新找帧头。
                self._mark_bad_frame("tail error", tail=True)
                self._resync_after_bad_candidate()
                continue

            expected = calculate_checksum(candidate[PAYLOAD_START_OFFSET : PAYLOAD_END_OFFSET + 1])
            if candidate[CHECKSUM_OFFSET] != expected:
                # checksum 错误同样只丢弃当前起点，避免清空整段 buffer 导致后续好帧丢失。
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
        """丢弃帧头前噪声，但保留可能的半帧头。"""
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
    """固件确认的 checksum：payload 每个字节逐个 XOR。"""
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return checksum
