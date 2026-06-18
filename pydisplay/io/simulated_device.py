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
    adc_fields = {
        f"adc_ch{channel}_slot{slot}": int((channel * 20_000) + (slot * 1200) + (3000 * math.sin(t * 4.0 + channel + slot * 0.25)))
        for channel in range(1, 5)
        for slot in range(6)
    }
    return DecodedSample(
        timestamp_pc_ns=ts,
        relative_time_s=t,
        frame_seq=None,
        sample_seq=index,
        **adc_fields,
        source="simulation only, not firmware protocol",
    )
