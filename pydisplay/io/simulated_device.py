"""无硬件调试用模拟数据。

重要：这里是 simulation only, not firmware protocol。
它生成的是“看起来像 decoded sample 的数据”，用于测试 GUI 曲线和回放流程。
不要把这里的数值格式当成固件通信协议。
"""

from __future__ import annotations

import math
import time

from pydisplay.protocol.models import DecodedSample


def generate_mock_decoded_sample(index: int, *, timestamp_ns: int | None = None) -> DecodedSample:
    """生成一条仅供 UI 调试使用的模拟 DecodedSample。"""

    ts = time.time_ns() if timestamp_ns is None else timestamp_ns
    t = index / 100.0
    return DecodedSample(
        timestamp_pc_ns=ts,
        relative_time_s=t,
        frame_seq=None,
        sample_seq=index,
        ppg_g=100_000 + 1000 * math.sin(t),
        ppg_r=95_000 + 800 * math.sin(t + 0.5),
        ppg_ir=120_000 + 1200 * math.sin(t + 1.0),
        acc_x=0.01 * math.sin(t),
        acc_y=0.01 * math.cos(t),
        acc_z=1.0,
        gyro_x=0.1 * math.sin(t),
        gyro_y=0.1 * math.cos(t),
        gyro_z=0.0,
        uh1=1.0,
        uh2=2.0,
        uh3=3.0,
        uh4=4.0,
        uc1=0.5,
        uc2=1.0,
        uc3=1.5,
        uc4=2.0,
        ud1=0.25,
        ud2=0.4,
        source="simulation only, not firmware protocol",
    )
