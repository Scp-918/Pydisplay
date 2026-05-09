"""Dataclasses shared by parser, decoder, and command encoder."""

from __future__ import annotations

from dataclasses import dataclass, field


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
        if self.total_frames == 0:
            return 0.0
        return self.bad_frames / self.total_frames


@dataclass(slots=True)
class DecodeConfig:
    k: float
    start_time_ns: int | None = None
    gyro_range_code: int = 0x02
    accel_range_code: int = 0x01
    ud_epsilon: float = 1e-9


@dataclass(slots=True)
class DecodedSample:
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
