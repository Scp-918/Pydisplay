"""Read decoded.csv into DecodedSample objects."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from pydisplay.protocol.models import DecodedSample
from pydisplay.recorder.csv_writer import CSV_FIELDS


class DecodedCsvFormatError(ValueError):
    """Raised when decoded.csv is missing required fields or values."""


def read_decoded_csv(path: str | Path) -> list[DecodedSample]:
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        missing = set(CSV_FIELDS) - set(reader.fieldnames or [])
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise DecodedCsvFormatError(f"decoded.csv missing required fields: {missing_text}")
        return [_row_to_sample(row) for row in reader]


def _row_to_sample(row: dict[str, str]) -> DecodedSample:
    try:
        return DecodedSample(
            relative_time_s=_float(row["relative_time_s"]),
            timestamp_pc_ns=int(float(row["timestamp_pc_ns"])),
            frame_seq=_optional_int(row["frame_seq"]),
            sample_seq=_optional_int(row["sample_seq"]),
            ppg_g=_float(row["PPG_G"]),
            ppg_r=_float(row["PPG_R"]),
            ppg_ir=_float(row["PPG_IR"]),
            acc_x=_float(row["ACC_X"]),
            acc_y=_float(row["ACC_Y"]),
            acc_z=_float(row["ACC_Z"]),
            gyro_x=_float(row["GYRO_X"]),
            gyro_y=_float(row["GYRO_Y"]),
            gyro_z=_float(row["GYRO_Z"]),
            uh1=_float(row["Uh1"]),
            uh2=_float(row["Uh2"]),
            uh3=_float(row["Uh3"]),
            uh4=_float(row["Uh4"]),
            uc1=_float(row["Uc1"]),
            uc2=_float(row["Uc2"]),
            uc3=_float(row["Uc3"]),
            uc4=_float(row["Uc4"]),
            ud1=_float(row["UD1"]),
            ud2=_float(row["UD2"]),
            parser_valid=_bool(row["parser_valid"]),
            source=row["source"] or "decoded_csv",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DecodedCsvFormatError(f"decoded.csv row is invalid: {exc}") from exc


def _optional_int(value: str) -> int | None:
    if value == "":
        return None
    return int(float(value))


def _float(value: str) -> float:
    if value.lower() == "nan":
        return math.nan
    return float(value)


def _bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}
