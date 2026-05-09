"""raw_frames.bin 回放读取模块。

raw bin 回放尽量复用真实链路：读出原始 bytes 后再交给 parser/decoder。
这样可以检查 parser 在历史数据上的表现，也能复盘坏帧问题。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydisplay.recorder.raw_bin_format import RecordType, read_raw_bin


@dataclass(frozen=True, slots=True)
class RawReplayItem:
    timestamp_ns: int
    data: bytes
    record_type: RecordType


def read_raw_replay_items(
    path: str | Path,
    *,
    include_types: set[RecordType] | None = None,
) -> list[RawReplayItem]:
    """读取 raw bin 并转换成 ReplayWorker 可处理的 RawReplayItem 列表。"""
    _header, records = read_raw_bin(path)
    allowed = include_types or {
        RecordType.RAW_SERIAL_CHUNK,
        RecordType.VALID_RAW_FRAME,
        RecordType.BAD_FRAME_FRAGMENT,
    }
    return [
        RawReplayItem(record.timestamp_ns, record.payload, record.record_type)
        for record in records
        if record.record_type in allowed
    ]
