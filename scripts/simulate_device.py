from __future__ import annotations

import sys
from pathlib import Path

# 这个脚本是无硬件演示入口，不依赖真实串口。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydisplay.io.simulated_device import generate_mock_decoded_sample


def main() -> int:
    """输出几条 simulation only 的 decoded sample，确认模拟模块可用。"""
    print("simulation only, not firmware protocol")
    for index in range(5):
        sample = generate_mock_decoded_sample(index)
        print(index, sample.relative_time_s, sample.ppg_g, sample.ud1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
