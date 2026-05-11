"""decoded.csv 写入模块。

CSV 文件面向实验数据分析，适合 Excel / Origin / MATLAB / Python 读取。
这里使用标准库 csv，不使用 pandas，也不会每帧打开/关闭文件。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TextIO

from pydisplay.protocol.models import DecodedSample


CSV_FIELDS = [
    "relative_time_s",
    "timestamp_pc_ns",
    "frame_seq",
    "absolute_seq_u64",
    "seq_gap",
    "lost_before",
    "segment_id",
    "sample_seq",
    "PPG_G",
    "PPG_R",
    "PPG_IR",
    "ACC_X",
    "ACC_Y",
    "ACC_Z",
    "GYRO_X",
    "GYRO_Y",
    "GYRO_Z",
    "Uh1",
    "Uh2",
    "Uh3",
    "Uh4",
    "Uc1",
    "Uc2",
    "Uc3",
    "Uc4",
    "UD1",
    "UD2",
    "parser_valid",
    "source",
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
    return {
        "relative_time_s": sample.relative_time_s,
        "timestamp_pc_ns": sample.timestamp_pc_ns,
        "frame_seq": "" if sample.frame_seq is None else sample.frame_seq,
        "absolute_seq_u64": "" if sample.absolute_seq_u64 is None else sample.absolute_seq_u64,
        "seq_gap": sample.seq_gap,
        "lost_before": sample.lost_before,
        "segment_id": sample.segment_id,
        "sample_seq": "" if sample.sample_seq is None else sample.sample_seq,
        "PPG_G": sample.ppg_g,
        "PPG_R": sample.ppg_r,
        "PPG_IR": sample.ppg_ir,
        "ACC_X": sample.acc_x,
        "ACC_Y": sample.acc_y,
        "ACC_Z": sample.acc_z,
        "GYRO_X": sample.gyro_x,
        "GYRO_Y": sample.gyro_y,
        "GYRO_Z": sample.gyro_z,
        "Uh1": sample.uh1,
        "Uh2": sample.uh2,
        "Uh3": sample.uh3,
        "Uh4": sample.uh4,
        "Uc1": sample.uc1,
        "Uc2": sample.uc2,
        "Uc3": sample.uc3,
        "Uc4": sample.uc4,
        "UD1": sample.ud1,
        "UD2": sample.ud2,
        "parser_valid": sample.parser_valid,
        "source": sample.source,
    }
