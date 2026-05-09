"""raw_frames.bin 二进制格式。

raw_frames.bin 的目的不是给人直接阅读，而是完整保存原始串口数据，
方便以后重新跑 parser、排查协议问题或复现实验。

文件由两部分组成：
1. 固定长度文件头；
2. 多条 record，每条 record 有类型、时间戳、payload 长度和 payload。

所有整数都使用 little-endian，格式见 `docs/data_format.md`。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import struct
from typing import BinaryIO


MAGIC = b"PYDISPRAW"
FORMAT_VERSION = 1
HEADER_LENGTH = 32
_HEADER_STRUCT = struct.Struct("<9sHQI9s")
_RECORD_STRUCT = struct.Struct("<BQI")


class RawBinFormatError(ValueError):
    """Raised when a raw bin file is invalid or unsupported."""


class RecordType(IntEnum):
    RAW_SERIAL_CHUNK = 1
    VALID_RAW_FRAME = 2
    BAD_FRAME_FRAGMENT = 3


@dataclass(frozen=True, slots=True)
class RawBinHeader:
    magic: bytes
    format_version: int
    created_unix_ns: int
    header_length: int


@dataclass(frozen=True, slots=True)
class RawBinRecord:
    record_type: RecordType
    timestamp_ns: int
    payload: bytes


class RawBinWriter:
    """按稳定格式写 raw bin 文件。"""

    def __init__(self, path: str | Path, *, created_unix_ns: int) -> None:
        self.path = Path(path)
        self.created_unix_ns = created_unix_ns
        self._file: BinaryIO | None = None

    def __enter__(self) -> "RawBinWriter":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("wb")
        self._file.write(_HEADER_STRUCT.pack(MAGIC, FORMAT_VERSION, self.created_unix_ns, HEADER_LENGTH, b"\x00" * 9))

    def write_record(self, record_type: RecordType, timestamp_ns: int, payload: bytes) -> None:
        """写入一条 raw 记录。

        不在这里每条 flush，避免 100 Hz 记录时造成不必要的磁盘压力。
        """
        if self._file is None:
            raise RawBinFormatError("raw bin writer is not open")
        payload = bytes(payload)
        self._file.write(_RECORD_STRUCT.pack(int(record_type), timestamp_ns, len(payload)))
        self._file.write(payload)

    def flush(self) -> None:
        if self._file:
            self._file.flush()

    def close(self) -> None:
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None


def read_raw_bin(path: str | Path) -> tuple[RawBinHeader, list[RawBinRecord]]:
    """一次性读取 raw bin 文件，主要用于测试和回放准备阶段。"""
    with Path(path).open("rb") as file:
        header_bytes = file.read(HEADER_LENGTH)
        if len(header_bytes) != HEADER_LENGTH:
            raise RawBinFormatError("raw bin header is incomplete")
        magic, version, created_unix_ns, header_length, _reserved = _HEADER_STRUCT.unpack(header_bytes)
        if magic != MAGIC:
            raise RawBinFormatError("raw bin magic mismatch")
        if version != FORMAT_VERSION:
            raise RawBinFormatError(f"unsupported raw bin version: {version}")
        if header_length != HEADER_LENGTH:
            raise RawBinFormatError(f"unsupported raw bin header length: {header_length}")

        records: list[RawBinRecord] = []
        while True:
            record_header = file.read(_RECORD_STRUCT.size)
            if not record_header:
                break
            if len(record_header) != _RECORD_STRUCT.size:
                raise RawBinFormatError("raw bin record header is incomplete")
            record_type_value, timestamp_ns, payload_length = _RECORD_STRUCT.unpack(record_header)
            try:
                record_type = RecordType(record_type_value)
            except ValueError as exc:
                raise RawBinFormatError(f"unknown raw bin record type: {record_type_value}") from exc
            payload = file.read(payload_length)
            if len(payload) != payload_length:
                raise RawBinFormatError("raw bin record payload is incomplete")
            records.append(RawBinRecord(record_type, timestamp_ns, payload))

    return RawBinHeader(magic, version, created_unix_ns, header_length), records
