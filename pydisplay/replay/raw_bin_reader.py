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
    """读取 raw bin 并转换成 ReplayWorker 可处理的 RawReplayItem 列表。

    正常新记录会包含 RAW_SERIAL_CHUNK，这些 chunk 是最接近真实串口输入的
    数据源，里面已经包含有效帧、无效帧、半包和粘包。因此只要存在 raw chunk，
    默认就只回放 raw chunk，避免把同一次记录里的 valid_frame 诊断记录重复喂给
    parser。

    如果旧文件没有 raw chunk，则退回到完整帧/坏帧 fragment 的记录。这个 fallback
    不能完全恢复串口粘包形态，但至少能按记录时间戳把有效帧和无效片段都回放出来。
    """
    _header, records = read_raw_bin(path)
    if include_types is None:
        has_raw_chunks = any(record.record_type == RecordType.RAW_SERIAL_CHUNK for record in records)
        allowed = (
            {RecordType.RAW_SERIAL_CHUNK}
            if has_raw_chunks
            else {RecordType.VALID_RAW_FRAME, RecordType.BAD_FRAME_FRAGMENT}
        )
    else:
        allowed = include_types
    return [
        RawReplayItem(record.timestamp_ns, record.payload, record.record_type)
        for record in records
        if record.record_type in allowed
    ]
