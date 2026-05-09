from __future__ import annotations

import pytest

from pydisplay.protocol.commands import build_control_command
from pydisplay.protocol.errors import CommandValidationError
from pydisplay.protocol.models import ControlMetadata


def test_build_control_command_encodes_confirmed_firmware_frame() -> None:
    command = build_control_command(
        ControlMetadata(
            ppg_mode=0x01,
            ppg_multi_submode=0x05,
            led_green=9,
            led_red=8,
            led_ir=7,
            ppg_adc_range=0x04,
            ppg_pulse_width=0x03,
            gyro_range=0x02,
            accel_range=0x04,
        )
    )

    assert command.data == bytes(
        [
            0xAB,
            0xCD,
            0x01,
            0x05,
            9,
            8,
            7,
            0x04,
            0x03,
            0x02,
            0x04,
            0xEF,
            0xFA,
        ]
    )
    assert command.expects_ack is False


def test_build_control_command_rejects_invalid_led_level() -> None:
    with pytest.raises(CommandValidationError):
        build_control_command(
            ControlMetadata(
                ppg_mode=0x01,
                ppg_multi_submode=0x01,
                led_green=10,
                led_red=0,
                led_ir=0,
                ppg_adc_range=0x01,
                ppg_pulse_width=0x01,
                gyro_range=0x01,
                accel_range=0x01,
            )
        )


def test_build_control_command_rejects_non_multi_submode_for_hr() -> None:
    with pytest.raises(CommandValidationError):
        build_control_command(
            ControlMetadata(
                ppg_mode=0x02,
                ppg_multi_submode=0x05,
                led_green=1,
                led_red=1,
                led_ir=1,
                ppg_adc_range=0x01,
                ppg_pulse_width=0x01,
                gyro_range=0x01,
                accel_range=0x01,
            )
        )
