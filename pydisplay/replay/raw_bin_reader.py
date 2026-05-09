"""Read raw_frames.bin for replay."""

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
