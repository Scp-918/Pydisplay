"""raw_frames.bin 回放读取模块。

raw bin 记录的是串口线程当时读到的 chunk。一个 chunk 不一定等于一帧：
有时只有半个帧头，有时一次 read 会包含两帧。直接按 chunk 时间戳回放会让
100 Hz 固件帧流变成抖动的成组投递，Windows 上还容易被短 sleep 精度进一步拖慢。

因此 GUI 默认采用“100 Hz 帧节拍重建”：先从 raw chunk 中提取有效固件帧，
再按固件 frame_seq 重建每帧时间戳，最后仍把完整 raw frame 送回 parser/decoder
链路。这样不修改原始 bin 文件，同时避免把串口 read 的时间戳误当作采样时间戳。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydisplay.protocol.constants import FRAME_HEADER, FRAME_LENGTH, FRAME_SEQ_OFFSET
from pydisplay.protocol.models import ParsedFrame
from pydisplay.protocol.parser import FrameParser
from pydisplay.protocol.sequence import RESET_OR_REORDER_THRESHOLD
from pydisplay.recorder.raw_bin_format import RawBinRecord, RecordType, read_raw_bin


DEFAULT_RAW_REPLAY_FRAME_HZ = 100.0


class RawReplayTimingMode(str, Enum):
    """raw bin 回放节拍模式。"""

    FRAME_CLOCK_100HZ = "frame_clock_100hz"
    ORIGINAL_TIMESTAMPS = "original_timestamps"


@dataclass(frozen=True, slots=True)
class RawReplayItem:
    timestamp_ns: int
    data: bytes
    record_type: RecordType


def read_raw_replay_items(
    path: str | Path,
    *,
    include_types: set[RecordType] | None = None,
    timing_mode: RawReplayTimingMode | str = RawReplayTimingMode.FRAME_CLOCK_100HZ,
    frame_hz: float = DEFAULT_RAW_REPLAY_FRAME_HZ,
) -> list[RawReplayItem]:
    """读取 raw bin 并转换成 ReplayWorker 可处理的 RawReplayItem 列表。

    默认使用 100 Hz 帧节拍重建。若调用者显式传入 include_types，或 timing_mode
    选择 ORIGINAL_TIMESTAMPS，则保留旧的按 record 原始时间戳回放方式，便于调试
    串口 chunk 本身。
    """
    _header, records = read_raw_bin(path)
    mode = RawReplayTimingMode(timing_mode)
    if frame_hz <= 0:
        raise ValueError("frame_hz must be positive")

    if include_types is None and mode == RawReplayTimingMode.FRAME_CLOCK_100HZ:
        reconstructed = _read_frame_clock_items(records, frame_hz=frame_hz)
        if reconstructed:
            return reconstructed

    return _read_original_timestamp_items(records, include_types=include_types)


def _read_original_timestamp_items(
    records: list[RawBinRecord],
    *,
    include_types: set[RecordType] | None,
) -> list[RawReplayItem]:
    """按 raw bin record 原始时间戳回放，主要用于诊断 chunk 级问题。"""
    if include_types is None:
        has_raw_chunks = any(record.record_type == RecordType.RAW_SERIAL_CHUNK for record in records)
        allowed = (
            {RecordType.RAW_SERIAL_CHUNK}
            if has_raw_chunks
            else {RecordType.VALID_RAW_FRAME, RecordType.BAD_FRAME_FRAGMENT}
        )
    else:
        allowed = include_types
    return [RawReplayItem(record.timestamp_ns, record.payload, record.record_type) for record in records if record.record_type in allowed]


def _read_frame_clock_items(records: list[RawBinRecord], *, frame_hz: float) -> list[RawReplayItem]:
    """从 raw bin 中提取有效固件帧，并重建稳定的每帧时间戳。"""
    raw_chunks = [record for record in records if record.record_type == RecordType.RAW_SERIAL_CHUNK]
    if raw_chunks:
        frames = _parse_frames_from_raw_chunks(raw_chunks)
        if frames:
            frame_records = [(frame.timestamp_ns, frame.raw, frame.frame_seq) for frame in frames]
            return _rebuild_frame_clock_items(frame_records, frame_hz=frame_hz)

    valid_records = [
        record
        for record in records
        if record.record_type == RecordType.VALID_RAW_FRAME and _looks_like_complete_frame(record.payload)
    ]
    if valid_records:
        frame_records = [(record.timestamp_ns, record.payload, _frame_seq_from_raw(record.payload)) for record in valid_records]
        return _rebuild_frame_clock_items(frame_records, frame_hz=frame_hz)

    return []


def _parse_frames_from_raw_chunks(records: list[RawBinRecord]) -> list[ParsedFrame]:
    """复用真实 parser 从串口 chunk 中提取有效帧。"""
    parser = FrameParser()
    frames: list[ParsedFrame] = []
    for record in records:
        frames.extend(parser.feed(record.payload, timestamp_ns=record.timestamp_ns))
    return frames


def _rebuild_frame_clock_items(
    frame_records: list[tuple[int, bytes, int | None]],
    *,
    frame_hz: float,
) -> list[RawReplayItem]:
    """按固件帧序号重建 100 Hz 时间轴。

    若 frame_seq 连续，时间戳每帧前进 10 ms；若中间确有丢帧，按 seq delta
    留出对应时间间隔；若遇到重复或疑似重启/乱序，则只前进一个采样周期，避免
    生成极大的回放空洞。
    """
    if not frame_records:
        return []

    interval_ns = int(round(1_000_000_000 / frame_hz))
    current_ts = frame_records[0][0]
    previous_seq = frame_records[0][2]
    items = [RawReplayItem(current_ts, frame_records[0][1], RecordType.VALID_RAW_FRAME)]

    for _original_ts, raw, frame_seq in frame_records[1:]:
        step = 1
        if previous_seq is not None and frame_seq is not None:
            delta = (frame_seq - previous_seq) & 0xFFFF
            if 1 <= delta < RESET_OR_REORDER_THRESHOLD:
                step = delta
        current_ts += interval_ns * step
        items.append(RawReplayItem(current_ts, raw, RecordType.VALID_RAW_FRAME))
        previous_seq = frame_seq
    return items


def _looks_like_complete_frame(payload: bytes) -> bool:
    return len(payload) == FRAME_LENGTH and payload.startswith(FRAME_HEADER)


def _frame_seq_from_raw(payload: bytes) -> int | None:
    if len(payload) < FRAME_SEQ_OFFSET + 2:
        return None
    return payload[FRAME_SEQ_OFFSET] | (payload[FRAME_SEQ_OFFSET + 1] << 8)
