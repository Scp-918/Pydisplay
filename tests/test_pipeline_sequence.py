from __future__ import annotations

from pydisplay.io.serial_reader import RawChunk
from pydisplay.protocol.models import DecodeConfig, DecodedSample
from pydisplay.services.pipeline import DataPipeline


HEADER = b"\xAA\xBB"
TAIL = b"\xCC"
PAYLOAD_LENGTH = 93


def build_frame(frame_seq: int, payload_byte: int = 1) -> bytes:
    payload = bytes([payload_byte]) * PAYLOAD_LENGTH
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return HEADER + payload + bytes([checksum]) + frame_seq.to_bytes(2, "little") + TAIL


def test_pipeline_adds_sequence_tracking_fields_and_health_counts() -> None:
    decoded: list[DecodedSample] = []
    pipeline = DataPipeline(decode_config=DecodeConfig(k=5.0), on_decoded=decoded.append)

    pipeline.handle_raw_chunk(RawChunk(timestamp_ns=1_000_000_000, data=build_frame(100), port="test"))
    pipeline.handle_raw_chunk(RawChunk(timestamp_ns=1_010_000_000, data=build_frame(103), port="test"))

    assert len(decoded) == 2
    assert decoded[0].frame_seq == 100
    assert decoded[0].absolute_seq_u64 == 0
    assert decoded[0].seq_gap == 0
    assert decoded[0].lost_before == 0
    assert decoded[1].frame_seq == 103
    assert decoded[1].absolute_seq_u64 == 3
    assert decoded[1].seq_gap == 3
    assert decoded[1].lost_before == 2
    assert decoded[1].segment_id == 0

    snapshot = pipeline.health.snapshot(now_ns=2_000_000_000)
    assert snapshot.lost_frames == 2
    assert snapshot.lost_frame_ratio == 2 / 4
    assert snapshot.duplicate_seq_count == 0
    assert snapshot.seq_reset_count == 0


def test_pipeline_reset_stream_state_starts_sequence_and_timebase_over() -> None:
    decoded: list[DecodedSample] = []
    pipeline = DataPipeline(decode_config=DecodeConfig(k=5.0), on_decoded=decoded.append)

    pipeline.handle_raw_chunk(RawChunk(timestamp_ns=1_000_000_000, data=build_frame(100), port="test"))
    pipeline.reset_stream_state()
    pipeline.handle_raw_chunk(RawChunk(timestamp_ns=2_000_000_000, data=build_frame(100), port="test"))

    assert decoded[-1].absolute_seq_u64 == 0
    assert decoded[-1].seq_gap == 0
    assert decoded[-1].lost_before == 0
    assert decoded[-1].relative_time_s == 0.0
