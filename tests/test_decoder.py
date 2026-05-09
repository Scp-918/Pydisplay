from __future__ import annotations

import math

import pytest

from pydisplay.protocol.decoder import decode_frame
from pydisplay.protocol.models import DecodeConfig, ParsedFrame


HEADER = b"\xAA\xBB"
TAIL = b"\xCC"
PAYLOAD_LENGTH = 45


def u24(value: int) -> bytes:
    return value.to_bytes(3, "little", signed=False)


def s24(value: int) -> bytes:
    if value < 0:
        value = (1 << 24) + value
    return value.to_bytes(3, "little", signed=False)


def s16(value: int) -> bytes:
    return value.to_bytes(2, "little", signed=True)


def build_payload(
    *,
    uc1: int = 0,
    uh1: int = 131_072,
    uc2: int = 32_000,
    uh2: int = 64_000,
    uc3: int = 48_000,
    uh3: int = 96_000,
    uc4: int = -32_000,
    uh4: int = 0,
) -> bytes:
    payload = bytearray()
    for value in (uc1, uh1, uc2, uh2, uc3, uh3, uc4, uh4):
        payload += s24(value)
    payload += u24(1000)
    payload += u24(2000)
    payload += u24(3000)
    payload += s16(100)
    payload += s16(-100)
    payload += s16(0)
    payload += s16(1000)
    payload += s16(-1000)
    payload += s16(0)
    assert len(payload) == PAYLOAD_LENGTH
    return bytes(payload)


def build_parsed_frame(payload: bytes, timestamp_ns: int = 1_000_000_000) -> ParsedFrame:
    checksum = 0
    for byte in payload:
        checksum ^= byte
    raw = HEADER + payload + bytes([checksum]) + TAIL
    return ParsedFrame(
        timestamp_ns=timestamp_ns,
        raw=raw,
        payload=payload,
        frame_seq=None,
        sample_seq=7,
        checksum_ok=True,
    )


def test_decoder_outputs_ppg_imu_voltage_and_ud_values() -> None:
    frame = build_parsed_frame(build_payload(), timestamp_ns=1_500_000_000)
    config = DecodeConfig(k=5.0, start_time_ns=1_000_000_000, gyro_range_code=0x02, accel_range_code=0x01)

    sample = decode_frame(frame, config)

    assert sample.timestamp_pc_ns == 1_500_000_000
    assert sample.relative_time_s == pytest.approx(0.5)
    assert sample.frame_seq is None
    assert sample.sample_seq == 7
    assert sample.ppg_g == 1000
    assert sample.ppg_r == 2000
    assert sample.ppg_ir == 3000
    assert sample.gyro_x == pytest.approx(1.75)
    assert sample.gyro_y == pytest.approx(-1.75)
    assert sample.gyro_z == pytest.approx(0.0)
    assert sample.acc_x == pytest.approx(0.061)
    assert sample.acc_y == pytest.approx(-0.061)
    assert sample.acc_z == pytest.approx(0.0)
    assert sample.uc1 == pytest.approx(0.0)
    assert sample.uh1 == pytest.approx(4.096)
    assert sample.uc2 == pytest.approx(1.0)
    assert sample.uh2 == pytest.approx(2.0)
    assert sample.ud1 == pytest.approx(0.25)
    assert sample.ud2 == pytest.approx((3.0 - 1.5) / (5.0 - 1.5))
    assert sample.parser_valid is True
    assert sample.source == "firmware"


def test_decoder_returns_nan_when_ud_denominator_is_near_zero() -> None:
    frame = build_parsed_frame(build_payload())
    sample = decode_frame(frame, DecodeConfig(k=1.0))

    assert math.isnan(sample.ud1)
    assert any("UD1" in warning for warning in sample.warnings)
