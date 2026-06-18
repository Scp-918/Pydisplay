from __future__ import annotations

from pydisplay.protocol.parser import FrameParser


HEADER = b"\xAA\xBB"
TAIL = b"\xCC"
FRAME_LENGTH = 99
PAYLOAD_LENGTH = 93


def build_frame(payload: bytes | None = None, *, frame_seq: int = 0) -> bytes:
    payload = payload if payload is not None else bytes(range(1, PAYLOAD_LENGTH + 1))
    assert len(payload) == PAYLOAD_LENGTH
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return HEADER + payload + bytes([checksum]) + frame_seq.to_bytes(2, "little") + TAIL


def test_parser_emits_single_valid_frame() -> None:
    parser = FrameParser()
    frame = build_frame()

    frames = parser.feed(frame, timestamp_ns=123)

    assert len(frames) == 1
    assert frames[0].raw == frame
    assert frames[0].payload == frame[2:95]
    assert frames[0].frame_seq == 0
    assert frames[0].timestamp_ns == 123
    assert frames[0].checksum_ok is True
    assert parser.stats.total_bytes == 99
    assert parser.stats.total_frames == 1
    assert parser.stats.valid_frames == 1
    assert parser.stats.bad_frames == 0


def test_parser_handles_sticky_frames_and_split_frames() -> None:
    parser = FrameParser()
    frame1 = build_frame(bytes([1]) * PAYLOAD_LENGTH)
    frame2 = build_frame(bytes([2]) * PAYLOAD_LENGTH)

    assert parser.feed(frame1[:10]) == []
    frames = parser.feed(frame1[10:] + frame2)

    assert [frame.raw for frame in frames] == [frame1, frame2]
    assert parser.stats.valid_frames == 2
    assert parser.stats.buffer_bytes == 0


def test_parser_discards_noise_but_keeps_half_header() -> None:
    parser = FrameParser()
    frame = build_frame()

    assert parser.feed(b"\x00\x11\xAA") == []
    frames = parser.feed(b"\xBB" + frame[2:])

    assert len(frames) == 1
    assert frames[0].raw == frame
    assert parser.stats.noise_bytes == 2


def test_parser_recovers_after_bad_checksum() -> None:
    parser = FrameParser()
    bad = bytearray(build_frame(bytes([3]) * PAYLOAD_LENGTH))
    bad[95] ^= 0xFF
    good = build_frame(bytes([4]) * PAYLOAD_LENGTH)

    frames = parser.feed(bytes(bad) + good)

    assert [frame.raw for frame in frames] == [good]
    assert parser.stats.bad_frames == 1
    assert parser.stats.checksum_errors == 1
    assert parser.stats.resync_count == 1
    assert parser.stats.valid_frames == 1


def test_parser_recovers_after_bad_tail() -> None:
    parser = FrameParser()
    bad = bytearray(build_frame(bytes([5]) * PAYLOAD_LENGTH))
    bad[98] = 0x00
    good = build_frame(bytes([6]) * PAYLOAD_LENGTH)

    frames = parser.feed(bytes(bad) + good)

    assert [frame.raw for frame in frames] == [good]
    assert parser.stats.bad_frames == 1
    assert parser.stats.tail_errors == 1
    assert parser.stats.resync_count == 1


def test_parser_extracts_uint16_little_endian_frame_seq() -> None:
    parser = FrameParser()
    frame = build_frame(frame_seq=0x1234)

    frames = parser.feed(frame)

    assert len(frames) == 1
    assert len(frames[0].raw) == 99
    assert frames[0].frame_seq == 0x1234
    assert frames[0].sample_seq == 1


def test_parser_caps_buffer_growth() -> None:
    parser = FrameParser(max_buffer_bytes=128)

    frames = parser.feed(b"\x10" * 500)

    assert frames == []
    assert parser.stats.buffer_bytes <= 1
    assert parser.stats.noise_bytes >= 499
