"""metadata.json 生成模块。

metadata 用来记录“这次实验是在什么条件下采集的”。
后处理时不要只看 decoded.csv，还应一起保存 metadata.json。

这里记录软件版本、固件信息、串口信息、k 值、协议字段布局和 CSV 字段说明。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydisplay import __version__
from pydisplay.protocol.constants import (
    BYTE_ORDER,
    FRAME_HEADER,
    FRAME_LENGTH,
    FRAME_TAIL,
    PAYLOAD_LENGTH,
    PROTOCOL_VERSION,
)
from .csv_writer import CSV_FIELDS
from .raw_bin_format import FORMAT_VERSION


FIRMWARE_REPO = "https://github.com/Scp-918/PulseTIMR2/tree/Single"
FIRMWARE_BRANCH = "Single"
FIRMWARE_COMMIT = "3714333572dc985c407dbb680183785cc0b92b66"


def build_metadata(
    *,
    record_path: str | Path,
    record_start_time: str | None = None,
    record_end_time: str | None = None,
    serial_port: str | None = None,
    baudrate: int | None = None,
    k: float | None = None,
    control_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造一份 metadata 字典。

    GUI 或 RecorderWorker 可以传入实际串口、波特率、k 值等信息。
    没有的字段保留为 None，避免编造。
    """
    return {
        "software": {"name": "Pydisplay", "version": __version__},
        "firmware": {
            "repo": FIRMWARE_REPO,
            "branch": FIRMWARE_BRANCH,
            "commit": FIRMWARE_COMMIT,
            "protocol_version": PROTOCOL_VERSION,
        },
        "session": {
            "record_start_time": record_start_time,
            "record_end_time": record_end_time,
            "record_path": str(record_path),
        },
        "serial": {"port": serial_port, "baudrate": baudrate, "device": "HJ380"},
        "bluetooth": {"tx_module": "HJ131", "rx_module": "HJ380"},
        "decode": {"k": k, "ud_formula": "UD = (Uh - Uc) / (k - Uc)"},
        "control_parameters": control_parameters
        or {
            "ppg_mode": None,
            "led_brightness": None,
            "ppg_range": None,
            "pulse_width": None,
            "imu_range": None,
        },
        "protocol": {
            "frame_header": _hex_bytes(FRAME_HEADER),
            "frame_tail": _hex_bytes(FRAME_TAIL),
            "frame_length": FRAME_LENGTH,
            "payload_length": PAYLOAD_LENGTH,
            "byte_order": BYTE_ORDER,
            "checksum": "xor bytes 2..46",
            "protocol_version": PROTOCOL_VERSION,
            "raw_bin_format_version": FORMAT_VERSION,
            "field_layout": [
                {"offset": 2, "field": "Uc1", "bytes": 3, "type": "int24"},
                {"offset": 5, "field": "Uh1", "bytes": 3, "type": "int24"},
                {"offset": 8, "field": "Uc2", "bytes": 3, "type": "int24"},
                {"offset": 11, "field": "Uh2", "bytes": 3, "type": "int24"},
                {"offset": 14, "field": "Uc3", "bytes": 3, "type": "int24"},
                {"offset": 17, "field": "Uh3", "bytes": 3, "type": "int24"},
                {"offset": 20, "field": "Uc4", "bytes": 3, "type": "int24"},
                {"offset": 23, "field": "Uh4", "bytes": 3, "type": "int24"},
                {"offset": 26, "field": "PPG_G", "bytes": 3, "type": "uint24"},
                {"offset": 29, "field": "PPG_R", "bytes": 3, "type": "uint24"},
                {"offset": 32, "field": "PPG_IR", "bytes": 3, "type": "uint24"},
                {"offset": 35, "field": "GYRO_X", "bytes": 2, "type": "int16"},
                {"offset": 37, "field": "GYRO_Y", "bytes": 2, "type": "int16"},
                {"offset": 39, "field": "GYRO_Z", "bytes": 2, "type": "int16"},
                {"offset": 41, "field": "ACC_X", "bytes": 2, "type": "int16"},
                {"offset": 43, "field": "ACC_Y", "bytes": 2, "type": "int16"},
                {"offset": 45, "field": "ACC_Z", "bytes": 2, "type": "int16"},
            ],
        },
        "csv_fields": {field: _csv_field_description(field) for field in CSV_FIELDS},
    }


def write_metadata(path: str | Path, metadata: dict[str, Any]) -> None:
    """把 metadata 以 UTF-8 JSON 写入磁盘。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _hex_bytes(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def _csv_field_description(field: str) -> str:
    descriptions = {
        "relative_time_s": "Relative time from recording start, seconds",
        "timestamp_pc_ns": "PC timestamp in ns",
        "frame_seq": "Firmware frame sequence if available",
        "sample_seq": "PC parser sample sequence",
        "parser_valid": "Whether parser accepted the source frame",
        "source": "Data source name",
    }
    return descriptions.get(field, f"Decoded field {field}")
