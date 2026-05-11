"""固件协议常量。

本文件中的常量都必须来自 `docs/protocol_analysis.md`，不能凭经验猜。
上位机 parser、decoder、command encoder 都依赖这里：

- 数据帧：`AA BB` 开头，固定 51 字节，`CC` 结尾；
- payload：byte 2..46；
- checksum：payload 全部字节 XOR，frame_seq 不参与；
- 字段 offset：PPG、IMU、Uh/Uc 等在 51 字节帧中的位置；ADC/PPG/IMU 旧偏移保持不变。
- 控制帧：`AB CD ... EF FA`，共 13 字节。

如果以后固件协议变化，先更新协议分析文档，再同步改这个文件和测试。
"""

from __future__ import annotations

# 数据帧固定结构：header + payload + checksum + tail。
FRAME_HEADER = b"\xAA\xBB"
FRAME_TAIL = b"\xCC"
FRAME_LENGTH = 51
PAYLOAD_LENGTH = 45
CHECKSUM_OFFSET = 47
FRAME_SEQ_OFFSET = 48
TAIL_OFFSET = 50
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

# ADC 通道映射由用户在 2026-05-10 确认：
# early_code -> Uc，late_code -> Uh，帧中通道顺序对应实验通道 1..4。
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

# 控制帧用于上位机向固件发送 PPG/LED/IMU 参数，没有 ACK/NACK。
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

# 固件初始化默认控制参数，来源：
# `.codex_firmware/PulseTIMR2/Core/Src/main.c` 的 g_sensor_param_array。
# 这些值是上位机控制面板的默认选项，也用于初始 IMU 解算量程。
DEFAULT_PPG_MODE = 0x01
DEFAULT_PPG_MULTI_SUBMODE = 0x01
DEFAULT_LED_GREEN = 0x05
DEFAULT_LED_RED = 0x01
DEFAULT_LED_IR = 0x01
DEFAULT_PPG_ADC_RANGE = 0x03
DEFAULT_PPG_PULSE_WIDTH = 0x03
DEFAULT_GYRO_RANGE = 0x02
DEFAULT_ACCEL_RANGE = 0x01
