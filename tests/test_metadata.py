from __future__ import annotations

import json
import math

from pydisplay.protocol.models import DecodedSample
from pydisplay.recorder.csv_writer import CSV_FIELDS, DecodedCsvWriter
from pydisplay.recorder.metadata import build_metadata, write_metadata


def sample() -> DecodedSample:
    return DecodedSample(
        timestamp_pc_ns=100,
        relative_time_s=0.1,
        frame_seq=None,
        sample_seq=1,
        ppg_g=1,
        ppg_r=2,
        ppg_ir=3,
        acc_x=0.1,
        acc_y=0.2,
        acc_z=0.3,
        gyro_x=0.4,
        gyro_y=0.5,
        gyro_z=0.6,
        uh1=1.0,
        uh2=2.0,
        uh3=3.0,
        uh4=4.0,
        uc1=0.5,
        uc2=1.0,
        uc3=1.5,
        uc4=2.0,
        ud1=0.25,
        ud2=math.nan,
    )


def test_decoded_csv_writer_outputs_expected_fields(tmp_path) -> None:
    path = tmp_path / "decoded.csv"
    with DecodedCsvWriter(path) as writer:
        writer.write_sample(sample())

    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].split(",") == CSV_FIELDS
    assert "0.25" in lines[1]
    assert "nan" in lines[1]


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
    assert loaded["firmware"]["branch"] == "Single"
    assert loaded["serial"]["port"] == "COM7"
    assert loaded["protocol"]["frame_header"] == "AA BB"
    assert loaded["protocol"]["frame_length"] == 49
    assert loaded["protocol"]["raw_bin_format_version"] == 1
    assert "UD1" in loaded["csv_fields"]
