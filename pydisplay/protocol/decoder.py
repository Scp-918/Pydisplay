"""固件帧 decoder。

parser 只负责判断一帧是否合法；decoder 负责解释每个字段的含义。
本文件根据 `docs/protocol_analysis.md` 做以下转换：

- int24 AD4007 原始码 -> 电压；
- uint24 PPG -> 固件 raw count；
- int16 IMU -> g / dps；
- Uh/Uc -> UD1/UD2。

注意：不要在这里读串口、写文件或操作 GUI。
"""

from __future__ import annotations

import math

from .constants import (
    ACCEL_MG_PER_LSB,
    ACC_X_OFFSET,
    ACC_Y_OFFSET,
    ACC_Z_OFFSET,
    ADC_CHANNEL_OFFSETS,
    ADC_FULL_SCALE_COUNTS,
    ADC_VREF,
    FRAME_LENGTH,
    GYRO_MDPS_PER_LSB,
    GYRO_X_OFFSET,
    GYRO_Y_OFFSET,
    GYRO_Z_OFFSET,
    PPG_G_OFFSET,
    PPG_IR_OFFSET,
    PPG_R_OFFSET,
)
from .errors import FrameDecodeError
from .models import DecodeConfig, DecodedSample, ParsedFrame


def decode_frame(frame: ParsedFrame, config: DecodeConfig) -> DecodedSample:
    """把一个合法 ParsedFrame 转成 DecodedSample。"""
    if len(frame.raw) != FRAME_LENGTH:
        raise FrameDecodeError(f"expected {FRAME_LENGTH} bytes, got {len(frame.raw)}")
    if not frame.checksum_ok:
        raise FrameDecodeError("cannot decode frame with failed checksum")

    raw = frame.raw
    # early_code -> Uc，late_code -> Uh；offset 来自 constants.py。
    uc = {channel: _adc_voltage(raw, offsets["uc"]) for channel, offsets in ADC_CHANNEL_OFFSETS.items()}
    uh = {channel: _adc_voltage(raw, offsets["uh"]) for channel, offsets in ADC_CHANNEL_OFFSETS.items()}

    warnings: list[str] = []
    # 用户确认：UD1 使用通道 2，UD2 使用通道 3。
    ud1 = _calculate_ud(uh[2], uc[2], config.k, config.ud_epsilon, "UD1", warnings)
    ud2 = _calculate_ud(uh[3], uc[3], config.k, config.ud_epsilon, "UD2", warnings)

    gyro_scale = _lookup_scale(GYRO_MDPS_PER_LSB, config.gyro_range_code, "gyro") / 1000.0
    accel_scale = _lookup_scale(ACCEL_MG_PER_LSB, config.accel_range_code, "accel") / 1000.0
    start_time = frame.timestamp_ns if config.start_time_ns is None else config.start_time_ns

    return DecodedSample(
        timestamp_pc_ns=frame.timestamp_ns,
        relative_time_s=(frame.timestamp_ns - start_time) / 1_000_000_000.0,
        frame_seq=frame.frame_seq,
        sample_seq=frame.sample_seq,
        ppg_g=float(_read_u24(raw, PPG_G_OFFSET)),
        ppg_r=float(_read_u24(raw, PPG_R_OFFSET)),
        ppg_ir=float(_read_u24(raw, PPG_IR_OFFSET)),
        acc_x=_read_s16(raw, ACC_X_OFFSET) * accel_scale,
        acc_y=_read_s16(raw, ACC_Y_OFFSET) * accel_scale,
        acc_z=_read_s16(raw, ACC_Z_OFFSET) * accel_scale,
        gyro_x=_read_s16(raw, GYRO_X_OFFSET) * gyro_scale,
        gyro_y=_read_s16(raw, GYRO_Y_OFFSET) * gyro_scale,
        gyro_z=_read_s16(raw, GYRO_Z_OFFSET) * gyro_scale,
        uh1=uh[1],
        uh2=uh[2],
        uh3=uh[3],
        uh4=uh[4],
        uc1=uc[1],
        uc2=uc[2],
        uc3=uc[3],
        uc4=uc[4],
        ud1=ud1,
        ud2=ud2,
        parser_valid=True,
        source=frame.source,
        warnings=warnings,
    )


def _lookup_scale(table: dict[int, float], code: int, name: str) -> float:
    try:
        return table[code]
    except KeyError as exc:
        raise FrameDecodeError(f"unsupported {name} range code: 0x{code:02X}") from exc


def _adc_voltage(data: bytes, offset: int) -> float:
    """AD4007 int24 原始码转电压，公式来自用户确认。"""
    return _read_s24(data, offset) * (ADC_VREF / ADC_FULL_SCALE_COUNTS)


def _read_u24(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16)


def _read_s24(data: bytes, offset: int) -> int:
    value = _read_u24(data, offset)
    if value >= 8_388_608:
        value -= 16_777_216
    return value


def _read_s16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little", signed=True)


def _calculate_ud(uh: float, uc: float, k: float, epsilon: float, label: str, warnings: list[str]) -> float:
    """计算 UD，分母接近 0 时返回 NaN 而不是抛异常。"""
    denominator = k - uc
    if abs(denominator) < epsilon:
        warnings.append(f"{label} denominator is near zero")
        return math.nan
    return (uh - uc) / denominator
