"""数据记录子包。

负责生成 raw_frames.bin、decoded.csv 和 metadata.json。
文件写入由 RecorderWorker 后台线程完成。
"""

from .csv_writer import DecodedCsvWriter
from .metadata import build_metadata, write_metadata
from .raw_bin_format import RawBinWriter, RecordType
from .recorder_worker import RecorderWorker, RecordingState

__all__ = [
    "DecodedCsvWriter",
    "RawBinWriter",
    "RecorderWorker",
    "RecordingState",
    "RecordType",
    "build_metadata",
    "write_metadata",
]
