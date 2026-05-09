from __future__ import annotations

import pytest

from pydisplay.recorder.raw_bin_format import (
    FORMAT_VERSION,
    MAGIC,
    RawBinFormatError,
    RawBinRecord,
    RawBinWriter,
    RecordType,
    read_raw_bin,
)


def test_raw_bin_writer_records_header_and_records(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"

    with RawBinWriter(path, created_unix_ns=123) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 1000, b"abc")
        writer.write_record(RecordType.VALID_RAW_FRAME, 2000, b"frame")

    header, records = read_raw_bin(path)
    assert header.magic == MAGIC
    assert header.format_version == FORMAT_VERSION
    assert header.created_unix_ns == 123
    assert records == [
        RawBinRecord(RecordType.RAW_SERIAL_CHUNK, 1000, b"abc"),
        RawBinRecord(RecordType.VALID_RAW_FRAME, 2000, b"frame"),
    ]


def test_raw_bin_reader_rejects_bad_magic(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    path.write_bytes(b"bad")

    with pytest.raises(RawBinFormatError):
        read_raw_bin(path)
