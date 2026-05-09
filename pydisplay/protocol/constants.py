"""Protocol constants confirmed in ``docs/protocol_analysis.md``."""

from __future__ import annotations

FRAME_HEADER = b"\xAA\xBB"
FRAME_TAIL = b"\xCC"
FRAME_LENGTH = 49
PAYLOAD_LENGTH = 45
CHECKSUM_OFFSET = 47
TAIL_OFFSET = 48
PAYLOAD_START_OFFSET = 2
PAYLOAD_END_OFFSET = 46
BYTE_ORDER = "little"
PROTOCOL_VERSION = None

ADC_VREF = 4.096
ADC_FULL_SCALE_COUNTS = 131_072.0

PPG_G_OFFSET = 26
PPG_R_OFFSET = 29
PPG_IR_OFFSET = 32

GYRO_X_OFFSET = 35
GYRO_Y_OFFSET = 37
GYRO_Z_OFFSET = 39
ACC_X_OFFSET = 41
ACC_Y_OFFSET = 43
ACC_Z_OFFSET = 45

ADC_CHANNEL_OFFSETS = {
    1: {"uc": 2, "uh": 5},
    2: {"uc": 8, "uh": 11},
    3: {"uc": 14, "uh": 17},
    4: {"uc": 20, "uh": 23},
}

ACCEL_MG_PER_LSB = {
    0x01: 0.061,
    0x02: 0.122,
    0x03: 0.244,
    0x04: 0.732,
}

GYRO_MDPS_PER_LSB = {
    0x01: 8.75,
    0x02: 17.50,
    0x03: 70.0,
}

CONTROL_FRAME_HEADER = b"\xAB\xCD"
CONTROL_FRAME_TAIL = b"\xEF\xFA"
CONTROL_FRAME_LENGTH = 13

PPG_MODE_VALUES = {0x01: "MultiLED", 0x02: "HR", 0x03: "SpO2"}
PPG_MULTI_SUBMODE_VALUES = {
    0x01: "G-R-IR",
    0x02: "G",
    0x03: "R",
    0x04: "IR",
    0x05: "R-IR",
}
LED_LEVEL_MIN = 0
LED_LEVEL_MAX = 9
