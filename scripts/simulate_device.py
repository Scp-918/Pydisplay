from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydisplay.io.simulated_device import generate_mock_decoded_sample


def main() -> int:
    print("simulation only, not firmware protocol")
    for index in range(5):
        sample = generate_mock_decoded_sample(index)
        print(index, sample.relative_time_s, sample.ppg_g, sample.ud1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
