from __future__ import annotations

import pytest

from pydisplay.protocol.decoder import decode_frame
from pydisplay.protocol.models import DecodeConfig, ParsedFrame


HEADER = b"\xAA\xBB"
TAIL = b"\xCC"
PAYLOAD_LENGTH = 93
ADC_SLOT_VALUES = tuple(range(1, 25))


def u24(value: int) -> bytes:
    return value.to_bytes(3, "little", signed=False)


def s24(value: int) -> bytes:
    if value < 0:
        value = (1 << 24) + value
    return value.to_bytes(3, "little", signed=False)


def s16(value: int) -> bytes:
    return value.to_bytes(2, "little", signed=True)


def build_payload(adc_values: tuple[int, ...] = ADC_SLOT_VALUES) -> bytes:
    assert len(adc_values) == 24
    payload = bytearray()
    for value in adc_values:
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


def build_parsed_frame(payload: bytes, timestamp_ns: int = 1_000_000_000, frame_seq: int = 0x0201) -> ParsedFrame:
    checksum = 0
    for byte in payload:
        checksum ^= byte
    raw = HEADER + payload + bytes([checksum]) + frame_seq.to_bytes(2, "little") + TAIL
    return ParsedFrame(
        timestamp_ns=timestamp_ns,
        raw=raw,
        payload=payload,
        frame_seq=frame_seq,
        sample_seq=7,
        checksum_ok=True,
    )


def test_decoder_outputs_24_signed_adc_slot_raw_codes() -> None:
    frame = build_parsed_frame(build_payload(), timestamp_ns=1_500_000_000)
    config = DecodeConfig(k=5.0, start_time_ns=1_000_000_000, gyro_range_code=0x02, accel_range_code=0x01)

    sample = decode_frame(frame, config)

    assert sample.timestamp_pc_ns == 1_500_000_000
    assert sample.relative_time_s == pytest.approx(0.5)
    assert sample.frame_seq == 0x0201
    assert sample.sample_seq == 7
    assert sample.adc_ch1_slot0 == 1
    assert sample.adc_ch1_slot5 == 6
    assert sample.adc_ch2_slot0 == 7
    assert sample.adc_ch3_slot5 == 18
    assert sample.adc_ch4_slot5 == 24
    assert sample.parser_valid is True
    assert sample.source == "firmware"
    assert not hasattr(sample, "ppg_g")
    assert not hasattr(sample, "ud1")


def test_decoder_preserves_signed_int24_slot_values() -> None:
    adc_values = (-1, -2, -3, -4, -5, -6) + tuple(range(7, 25))
    sample = decode_frame(build_parsed_frame(build_payload(adc_values)), DecodeConfig(k=5.0))

    assert sample.adc_ch1_slot0 == -1
    assert sample.adc_ch1_slot5 == -6


def test_decoder_initializes_timebase_once_when_start_time_is_missing() -> None:
    config = DecodeConfig(k=5.0)

    first = decode_frame(build_parsed_frame(build_payload(), timestamp_ns=1_000_000_000), config)
    second = decode_frame(build_parsed_frame(build_payload(), timestamp_ns=1_020_000_000), config)

    assert config.start_time_ns == 1_000_000_000
    assert first.relative_time_s == pytest.approx(0.0)
    assert second.relative_time_s == pytest.approx(0.02)
