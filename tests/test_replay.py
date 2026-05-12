from __future__ import annotations

import csv
import time

import pytest

from pydisplay.recorder.csv_writer import CSV_FIELDS, DecodedCsvWriter
from pydisplay.recorder.raw_bin_format import RawBinWriter, RecordType
from pydisplay.replay.decoded_csv_reader import DecodedCsvFormatError, read_decoded_csv
from pydisplay.replay.raw_bin_reader import RawReplayItem, RawReplayTimingMode, read_raw_replay_items
from pydisplay.replay.replay_worker import ReplayState, ReplayWorker
from pydisplay.protocol.models import DecodedSample

HEADER = b"\xAA\xBB"
TAIL = b"\xCC"
PAYLOAD_LENGTH = 45
FRAME_INTERVAL_NS = 10_000_000


def build_frame(frame_seq: int, payload_byte: int = 1) -> bytes:
    payload = bytes([payload_byte]) * PAYLOAD_LENGTH
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return HEADER + payload + bytes([checksum]) + frame_seq.to_bytes(2, "little") + TAIL


def sample(index: int, t: float = 0.0) -> DecodedSample:
    return DecodedSample(
        timestamp_pc_ns=index,
        relative_time_s=t,
        frame_seq=index & 0xFFFF,
        sample_seq=index,
        absolute_seq_u64=index,
        seq_gap=1 if index else 0,
        lost_before=0,
        segment_id=0,
        ppg_g=1,
        ppg_r=2,
        ppg_ir=3,
        acc_x=0,
        acc_y=0,
        acc_z=1,
        gyro_x=0,
        gyro_y=0,
        gyro_z=0,
        uh1=1,
        uh2=2,
        uh3=3,
        uh4=4,
        uc1=0.5,
        uc2=1,
        uc3=1.5,
        uc4=2,
        ud1=0.25,
        ud2=0.4,
    )


def test_read_raw_replay_items_prefers_raw_serial_chunks(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 100, b"abc")
        writer.write_record(RecordType.VALID_RAW_FRAME, 150, b"frame")
        writer.write_record(RecordType.BAD_FRAME_FRAGMENT, 200, b"bad")

    items = read_raw_replay_items(path)

    assert items == [
        RawReplayItem(timestamp_ns=100, data=b"abc", record_type=RecordType.RAW_SERIAL_CHUNK),
    ]


def test_read_raw_replay_items_reconstructs_100hz_frames_from_raw_chunks(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    frame1 = build_frame(100, payload_byte=1)
    frame2 = build_frame(101, payload_byte=2)
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 1_000_000_000, frame1[:1])
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 1_005_000_000, frame1[1:] + frame2)

    items = read_raw_replay_items(path)

    assert [item.data for item in items] == [frame1, frame2]
    assert [item.record_type for item in items] == [RecordType.VALID_RAW_FRAME, RecordType.VALID_RAW_FRAME]
    assert [item.timestamp_ns for item in items] == [1_005_000_000, 1_005_000_000 + FRAME_INTERVAL_NS]


def test_read_raw_replay_items_preserves_sequence_gaps_in_frame_clock(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    frame1 = build_frame(100, payload_byte=1)
    frame2 = build_frame(103, payload_byte=2)
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 1_000_000_000, frame1 + frame2)

    items = read_raw_replay_items(path)

    assert [item.timestamp_ns for item in items] == [1_000_000_000, 1_000_000_000 + 3 * FRAME_INTERVAL_NS]


def test_read_raw_replay_items_can_use_original_chunk_timestamps(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    frame = build_frame(100)
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 100, frame[:1])
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 200, frame[1:])

    items = read_raw_replay_items(path, timing_mode=RawReplayTimingMode.ORIGINAL_TIMESTAMPS)

    assert items == [
        RawReplayItem(timestamp_ns=100, data=frame[:1], record_type=RecordType.RAW_SERIAL_CHUNK),
        RawReplayItem(timestamp_ns=200, data=frame[1:], record_type=RecordType.RAW_SERIAL_CHUNK),
    ]


def test_read_raw_replay_items_falls_back_to_valid_frames(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.VALID_RAW_FRAME, 150, b"frame")
        writer.write_record(RecordType.BAD_FRAME_FRAGMENT, 200, b"bad")

    items = read_raw_replay_items(path)

    assert items == [
        RawReplayItem(timestamp_ns=150, data=b"frame", record_type=RecordType.VALID_RAW_FRAME),
        RawReplayItem(timestamp_ns=200, data=b"bad", record_type=RecordType.BAD_FRAME_FRAGMENT),
    ]


def test_read_raw_replay_items_can_include_debug_records_explicitly(tmp_path) -> None:
    path = tmp_path / "raw_frames.bin"
    with RawBinWriter(path, created_unix_ns=1) as writer:
        writer.write_record(RecordType.RAW_SERIAL_CHUNK, 100, b"abc")
        writer.write_record(RecordType.BAD_FRAME_FRAGMENT, 200, b"bad")

    items = read_raw_replay_items(path, include_types={RecordType.BAD_FRAME_FRAGMENT})

    assert items == [
        RawReplayItem(timestamp_ns=200, data=b"bad", record_type=RecordType.BAD_FRAME_FRAGMENT),
    ]


def test_read_decoded_csv_restores_samples(tmp_path) -> None:
    path = tmp_path / "decoded.csv"
    with DecodedCsvWriter(path) as writer:
        writer.write_sample(sample(1, 0.0))
        writer.write_sample(sample(2, 0.01))

    samples = read_decoded_csv(path)

    assert [item.sample_seq for item in samples] == [1, 2]
    assert samples[1].relative_time_s == pytest.approx(0.01)
    assert samples[1].frame_seq == 2
    assert samples[1].absolute_seq_u64 == 2
    assert samples[1].segment_id == 0
    assert samples[0].source == "decoded_csv"


def test_read_decoded_csv_synthesizes_timing_for_compact_csv(tmp_path) -> None:
    path = tmp_path / "decoded.csv"
    with DecodedCsvWriter(path) as writer:
        writer.write_sample(sample(1, 0.0))
        writer.write_sample(sample(2, 9.0))

    samples = read_decoded_csv(path)

    assert [item.relative_time_s for item in samples] == pytest.approx([0.0, 0.01])
    assert [item.timestamp_pc_ns for item in samples] == [0, 10_000_000]


def test_read_decoded_csv_rejects_missing_fields(tmp_path) -> None:
    path = tmp_path / "decoded.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["relative_time_s"])
        writer.writeheader()
        writer.writerow({"relative_time_s": 0})

    with pytest.raises(DecodedCsvFormatError):
        read_decoded_csv(path)


def test_replay_worker_pause_resume_and_finish() -> None:
    items = [sample(1, 0.0), sample(2, 0.01)]
    seen: list[int | None] = []
    finished: list[bool] = []
    worker = ReplayWorker(
        items,
        on_item=lambda item: (seen.append(item.sample_seq), worker.pause()),
        on_finished=lambda: finished.append(True),
    )

    worker.start(speed=5.0)
    time.sleep(0.02)
    assert worker.state == ReplayState.PAUSED
    assert seen == [1]

    worker.resume()
    worker.wait(timeout_s=1.0)

    assert seen == [1, 2]
    assert worker.state == ReplayState.FINISHED
    assert finished == [True]


def test_replay_worker_pause_during_timestamp_delay_holds_next_item() -> None:
    items = [
        RawReplayItem(0, b"first", RecordType.RAW_SERIAL_CHUNK),
        RawReplayItem(200_000_000, b"second", RecordType.RAW_SERIAL_CHUNK),
    ]
    seen: list[bytes] = []
    worker = ReplayWorker(items, on_item=lambda item: seen.append(item.data))

    worker.start(speed=1.0)
    time.sleep(0.03)
    worker.pause()
    time.sleep(0.25)

    assert seen == [b"first"]
    assert worker.state == ReplayState.PAUSED

    worker.resume()
    worker.wait(timeout_s=1.0)

    assert seen == [b"first", b"second"]
    assert worker.state == ReplayState.FINISHED


def test_replay_worker_rejects_unsupported_speed() -> None:
    worker = ReplayWorker([], on_item=lambda item: None)

    with pytest.raises(ValueError):
        worker.start(speed=3.0)


def test_replay_worker_stop_from_callback_does_not_join_itself() -> None:
    items = [sample(1, 0.0), sample(2, 0.01)]
    seen: list[int | None] = []
    errors: list[Exception] = []

    def on_item(item: DecodedSample) -> None:
        seen.append(item.sample_seq)
        worker.stop()

    worker = ReplayWorker(items, on_item=on_item, on_error=errors.append)

    worker.start(speed=5.0)
    worker.wait(timeout_s=1.0)

    assert seen == [1]
    assert errors == []
    assert worker.state == ReplayState.IDLE
