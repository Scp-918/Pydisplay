from __future__ import annotations

import json

from pydisplay.protocol.models import DecodedSample
from pydisplay.recorder.csv_writer import CSV_FIELDS, DecodedCsvWriter, sample_to_csv_row
from pydisplay.recorder.metadata import build_metadata, write_metadata


def sample() -> DecodedSample:
    adc_fields = {f"adc_ch{channel}_slot{slot}": channel * 100 + slot for channel in range(1, 5) for slot in range(6)}
    return DecodedSample(
        timestamp_pc_ns=100,
        relative_time_s=0.1,
        frame_seq=42,
        sample_seq=1,
        absolute_seq_u64=1000,
        seq_gap=1,
        lost_before=0,
        segment_id=0,
        **adc_fields,
    )


def test_decoded_csv_writer_outputs_expected_fields(tmp_path) -> None:
    path = tmp_path / "decoded.csv"
    with DecodedCsvWriter(path) as writer:
        writer.write_sample(sample())

    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].split(",") == CSV_FIELDS
    assert {"absolute_seq_u64", "segment_id"} <= set(CSV_FIELDS)
    assert not {"relative_time_s", "timestamp_pc_ns", "seq_gap", "lost_before", "source"} & set(CSV_FIELDS)
    assert "100" in lines[1]
    assert "405" in lines[1]
    assert "adc_ch1_slot0" in CSV_FIELDS
    assert "UD1" not in CSV_FIELDS


def test_sequence_csv_fields_use_empty_string_for_none_values() -> None:
    item = sample()
    item.frame_seq = None
    item.absolute_seq_u64 = None

    row = sample_to_csv_row(item)

    assert row["frame_seq"] == ""
    assert row["absolute_seq_u64"] == ""
    assert row["segment_id"] == 0


def test_metadata_contains_protocol_recording_and_csv_fields(tmp_path) -> None:
    metadata = build_metadata(
        record_path=tmp_path,
        record_start_time="2026-05-10T03:00:00+08:00",
        serial_port="COM7",
        baudrate=460800,
        k=5.0,
    )
    path = tmp_path / "metadata.json"
    write_metadata(path, metadata)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["software"]["name"] == "Pydisplay"
    assert loaded["firmware"]["branch"] == "debugADC"
    assert loaded["serial"]["port"] == "COM7"
    assert loaded["protocol"]["frame_header"] == "AA BB"
    assert loaded["protocol"]["frame_length"] == 99
    assert loaded["protocol"]["raw_bin_format_version"] == 1
    assert "adc_ch4_slot5" in loaded["csv_fields"]
