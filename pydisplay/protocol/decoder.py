"""固件帧 decoder。

parser 只负责判断一帧是否合法；decoder 负责解释每个字段的含义。
debugADC 分支只把 AD4007 的 signed int24 原始码解成 4 通道 x 6 slot。
PPG/IMU 仍保留在固件帧中，但不上抛到 GUI/CSV 的 DecodedSample。

注意：不要在这里读串口、写文件或操作 GUI。
"""

from __future__ import annotations

from .constants import ADC_SLOT_OFFSETS, FRAME_LENGTH
from .errors import FrameDecodeError
from .models import DecodeConfig, DecodedSample, ParsedFrame


def decode_frame(frame: ParsedFrame, config: DecodeConfig) -> DecodedSample:
    """把一个合法 ParsedFrame 转成 DecodedSample。"""
    if len(frame.raw) != FRAME_LENGTH:
        raise FrameDecodeError(f"expected {FRAME_LENGTH} bytes, got {len(frame.raw)}")
    if not frame.checksum_ok:
        raise FrameDecodeError("cannot decode frame with failed checksum")

    raw = frame.raw
    adc_slots = {name: _read_s24(raw, offset) for name, offset in ADC_SLOT_OFFSETS.items()}
    if config.start_time_ns is None:
        # 第一个有效帧作为本次实时流/RAW 回放的时间零点。
        # 之前每帧都临时使用自己的 timestamp 作零点，导致所有 x 坐标都是 0。
        config.start_time_ns = frame.timestamp_ns
    start_time = config.start_time_ns

    return DecodedSample(
        timestamp_pc_ns=frame.timestamp_ns,
        relative_time_s=(frame.timestamp_ns - start_time) / 1_000_000_000.0,
        frame_seq=frame.frame_seq,
        sample_seq=frame.sample_seq,
        **adc_slots,
        parser_valid=True,
        source=frame.source,
    )


def _read_u24(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16)


def _read_s24(data: bytes, offset: int) -> int:
    value = _read_u24(data, offset)
    if value >= 8_388_608:
        value -= 16_777_216
    return value
