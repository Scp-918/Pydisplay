"""协议层数据模型。

本文件只定义“数据长什么样”，不做复杂逻辑。
这样 parser、decoder、串口、记录、GUI 都能使用统一的数据结构。

几个核心概念：
- RawFrame：原始 bytes；
- ParsedFrame：parser 验证通过的一帧；
- DecodedSample：decoder 输出的可绘图、可写 CSV 的一行数据；
- ParserStats：parser 健康统计；
- ControlMetadata：GUI 控制参数；
- CommandFrame：编码后的固件控制帧。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import DEFAULT_ACCEL_RANGE, DEFAULT_GYRO_RANGE


@dataclass(slots=True)
class RawFrame:
    timestamp_ns: int
    data: bytes
    source: str = "serial"


@dataclass(slots=True)
class ParsedFrame:
    timestamp_ns: int
    raw: bytes
    payload: bytes
    frame_seq: int | None
    sample_seq: int | None
    checksum_ok: bool
    source: str = "firmware"


@dataclass(slots=True)
class ParserStats:
    """parser 的累计统计，供 health monitor 和 GUI 展示。"""
    total_bytes: int = 0
    total_frames: int = 0
    valid_frames: int = 0
    bad_frames: int = 0
    resync_count: int = 0
    noise_bytes: int = 0
    buffer_bytes: int = 0
    checksum_errors: int = 0
    tail_errors: int = 0
    length_errors: int = 0
    decode_errors: int = 0
    last_error: str | None = None

    @property
    def bad_frame_ratio(self) -> float:
        # total_frames 包含有效帧和坏帧；没有帧时比例定义为 0。
        if self.total_frames == 0:
            return 0.0
        return self.bad_frames / self.total_frames


@dataclass(slots=True)
class DecodeConfig:
    """decoder 运行配置。

    k 来自 GUI 输入；gyro/accel range 来自当前下位机控制参数。
    start_time_ns 用于计算相对时间，None 时以当前帧时间为零点。
    """
    k: float
    start_time_ns: int | None = None
    gyro_range_code: int = DEFAULT_GYRO_RANGE
    accel_range_code: int = DEFAULT_ACCEL_RANGE
    ud_epsilon: float = 1e-9


@dataclass(slots=True)
class DecodedSample:
    """一条已经解码完成的数据样本。

    字段名和 `decoded.csv`、GUI 曲线 key 保持一致，避免转换时再做复杂映射。
    """
    timestamp_pc_ns: int
    relative_time_s: float
    frame_seq: int | None
    sample_seq: int | None
    ppg_g: float
    ppg_r: float
    ppg_ir: float
    acc_x: float
    acc_y: float
    acc_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    uh1: float
    uh2: float
    uh3: float
    uh4: float
    uc1: float
    uc2: float
    uc3: float
    uc4: float
    ud1: float
    ud2: float
    absolute_seq_u64: int | None = None
    seq_gap: int = 0
    lost_before: int = 0
    segment_id: int = 0
    parser_valid: bool = True
    source: str = "firmware"
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ControlMetadata:
    ppg_mode: int
    ppg_multi_submode: int
    led_green: int
    led_red: int
    led_ir: int
    ppg_adc_range: int
    ppg_pulse_width: int
    gyro_range: int
    accel_range: int


@dataclass(frozen=True, slots=True)
class CommandFrame:
    data: bytes
    expects_ack: bool = False
