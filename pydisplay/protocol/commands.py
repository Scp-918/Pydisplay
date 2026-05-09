"""Control command encoder for the confirmed 13-byte firmware frame."""

from __future__ import annotations

from .constants import (
    ACCEL_MG_PER_LSB,
    CONTROL_FRAME_HEADER,
    CONTROL_FRAME_LENGTH,
    CONTROL_FRAME_TAIL,
    GYRO_MDPS_PER_LSB,
    LED_LEVEL_MAX,
    LED_LEVEL_MIN,
    PPG_MODE_VALUES,
    PPG_MULTI_SUBMODE_VALUES,
)
from .errors import CommandValidationError
from .models import CommandFrame, ControlMetadata


def build_control_command(metadata: ControlMetadata) -> CommandFrame:
    _validate(metadata)
    data = bytes(
        [
            *CONTROL_FRAME_HEADER,
            metadata.ppg_mode,
            metadata.ppg_multi_submode,
            metadata.led_green,
            metadata.led_red,
            metadata.led_ir,
            metadata.ppg_adc_range,
            metadata.ppg_pulse_width,
            metadata.gyro_range,
            metadata.accel_range,
            *CONTROL_FRAME_TAIL,
        ]
    )
    if len(data) != CONTROL_FRAME_LENGTH:
        raise CommandValidationError("encoded control frame length mismatch")
    return CommandFrame(data=data, expects_ack=False)


def _validate(metadata: ControlMetadata) -> None:
    _check_in(metadata.ppg_mode, PPG_MODE_VALUES, "ppg_mode")
    _check_in(metadata.ppg_multi_submode, PPG_MULTI_SUBMODE_VALUES, "ppg_multi_submode")
    if metadata.ppg_mode != 0x01 and metadata.ppg_multi_submode != 0x01:
        raise CommandValidationError("non-MultiLED modes require ppg_multi_submode 0x01")

    for name, value in (
        ("led_green", metadata.led_green),
        ("led_red", metadata.led_red),
        ("led_ir", metadata.led_ir),
    ):
        if not LED_LEVEL_MIN <= value <= LED_LEVEL_MAX:
            raise CommandValidationError(f"{name} must be {LED_LEVEL_MIN}..{LED_LEVEL_MAX}")

    _check_range(metadata.ppg_adc_range, 0x01, 0x04, "ppg_adc_range")
    _check_range(metadata.ppg_pulse_width, 0x01, 0x04, "ppg_pulse_width")
    _check_in(metadata.gyro_range, GYRO_MDPS_PER_LSB, "gyro_range")
    _check_in(metadata.accel_range, ACCEL_MG_PER_LSB, "accel_range")


def _check_in(value: int, choices: dict[int, object], name: str) -> None:
    if value not in choices:
        valid = ", ".join(f"0x{item:02X}" for item in sorted(choices))
        raise CommandValidationError(f"{name} must be one of {valid}")


def _check_range(value: int, minimum: int, maximum: int, name: str) -> None:
    if not minimum <= value <= maximum:
        raise CommandValidationError(f"{name} must be 0x{minimum:02X}..0x{maximum:02X}")
