from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许脚本从项目根目录以外运行时仍能 import pydisplay。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydisplay.recorder.raw_bin_format import read_raw_bin


def main() -> int:
    """打印 raw_frames.bin 的文件头和前几条记录，便于人工检查。"""
    parser = argparse.ArgumentParser(description="Inspect Pydisplay raw_frames.bin")
    parser.add_argument("path")
    args = parser.parse_args()
    header, records = read_raw_bin(args.path)
    print(f"magic={header.magic!r} version={header.format_version} created_unix_ns={header.created_unix_ns}")
    print(f"records={len(records)}")
    for record in records[:10]:
        print(f"{record.timestamp_ns} {record.record_type.name} {len(record.payload)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
