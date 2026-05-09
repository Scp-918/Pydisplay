"""绘图曲线配置。

每条曲线的 key 必须对应 DecodedSample 的字段名。
label 是 GUI 中显示的名称，unit 是 y 轴单位或说明。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurveConfig:
    key: str
    label: str
    group: str
    unit: str
    color: str


CURVES = [
    CurveConfig("ppg_g", "PPG_G", "PPG", "raw", "#2ca02c"),
    CurveConfig("ppg_r", "PPG_R", "PPG", "raw", "#d62728"),
    CurveConfig("ppg_ir", "PPG_IR", "PPG", "raw", "#7f7f7f"),
    CurveConfig("acc_x", "ACC_X", "ACC", "g", "#1f77b4"),
    CurveConfig("acc_y", "ACC_Y", "ACC", "g", "#ff7f0e"),
    CurveConfig("acc_z", "ACC_Z", "ACC", "g", "#2ca02c"),
    CurveConfig("gyro_x", "GYRO_X", "GYRO", "dps", "#1f77b4"),
    CurveConfig("gyro_y", "GYRO_Y", "GYRO", "dps", "#ff7f0e"),
    CurveConfig("gyro_z", "GYRO_Z", "GYRO", "dps", "#2ca02c"),
    CurveConfig("uh1", "Uh1", "Uh", "V", "#1f77b4"),
    CurveConfig("uh2", "Uh2", "Uh", "V", "#ff7f0e"),
    CurveConfig("uh3", "Uh3", "Uh", "V", "#2ca02c"),
    CurveConfig("uh4", "Uh4", "Uh", "V", "#9467bd"),
    CurveConfig("uc1", "Uc1", "Uc", "V", "#1f77b4"),
    CurveConfig("uc2", "Uc2", "Uc", "V", "#ff7f0e"),
    CurveConfig("uc3", "Uc3", "Uc", "V", "#2ca02c"),
    CurveConfig("uc4", "Uc4", "Uc", "V", "#9467bd"),
    CurveConfig("ud1", "UD1", "UD", "ratio", "#17becf"),
    CurveConfig("ud2", "UD2", "UD", "ratio", "#e377c2"),
]
