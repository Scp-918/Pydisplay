"""decoded.csv 写入模块。

CSV 文件面向实验数据分析，适合 Excel / Origin / MATLAB / Python 读取。
这里使用标准库 csv，不使用 pandas，也不会每帧打开/关闭文件。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TextIO

from pydisplay.protocol.constants import ADC_SLOT_FIELD_NAMES
from pydisplay.protocol.models import DecodedSample


CSV_FIELDS = [
    "frame_seq",
    "absolute_seq_u64",
    "segment_id",
    "sample_seq",
    *ADC_SLOT_FIELD_NAMES,
    "parser_valid",
]


class DecodedCsvWriter:
    """把 DecodedSample 写成固定字段顺序的 CSV。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._file: TextIO | None = None
        self._writer: csv.DictWriter | None = None

    def __enter__(self) -> "DecodedCsvWriter":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS)
        self._writer.writeheader()

    def write_sample(self, sample: DecodedSample) -> None:
        if self._writer is None:
            raise RuntimeError("decoded csv writer is not open")
        self._writer.writerow(sample_to_csv_row(sample))

    def flush(self) -> None:
        if self._file:
            self._file.flush()

    def close(self) -> None:
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None


def sample_to_csv_row(sample: DecodedSample) -> dict[str, object]:
    """把 dataclass 字段转换成 CSV 表头对应的字典。"""
    row: dict[str, object] = {
        "frame_seq": "" if sample.frame_seq is None else sample.frame_seq,
        "absolute_seq_u64": "" if sample.absolute_seq_u64 is None else sample.absolute_seq_u64,
        "segment_id": sample.segment_id,
        "sample_seq": "" if sample.sample_seq is None else sample.sample_seq,
        "parser_valid": sample.parser_valid,
    }
    for field in ADC_SLOT_FIELD_NAMES:
        row[field] = getattr(sample, field)
    return row
