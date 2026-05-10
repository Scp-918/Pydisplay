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


@dataclass(frozen=True, slots=True)
class PlotGroupConfig:
    """一个绘图区块的静态配置。

    grid_position 使用 Qt 的 addWidget(row, column, row_span, column_span) 顺序。
    curves 表示总图中绘制哪些曲线；subplots 表示哪些曲线还需要独立子图。
    """

    key: str
    title: str
    curves: tuple[str, ...]
    subplots: tuple[str, ...]
    unit: str
    grid_position: tuple[int, int, int, int]


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

CURVE_BY_KEY = {curve.key: curve for curve in CURVES}


PLOT_GROUPS = (
    PlotGroupConfig(
        key="ppg",
        title="a. 3色 PPG",
        curves=("ppg_g", "ppg_r", "ppg_ir"),
        subplots=("ppg_g", "ppg_r", "ppg_ir"),
        unit="raw",
        grid_position=(0, 0, 2, 1),
    ),
    PlotGroupConfig(
        key="uh23",
        title="b. 2/3号 Uh",
        curves=("uh2", "uh3"),
        subplots=("uh2", "uh3"),
        unit="V",
        grid_position=(0, 1, 2, 1),
    ),
    PlotGroupConfig(
        key="uc23",
        title="c. 2/3号 Uc",
        curves=("uc2", "uc3"),
        subplots=("uc2", "uc3"),
        unit="V",
        grid_position=(0, 2, 1, 1),
    ),
    PlotGroupConfig(
        key="ud",
        title="d. UD1 / UD2",
        curves=("ud1", "ud2"),
        subplots=("ud1", "ud2"),
        unit="ratio",
        grid_position=(1, 2, 1, 1),
    ),
    PlotGroupConfig(
        key="acc",
        title="f. 3轴 ACC",
        curves=("acc_x", "acc_y", "acc_z"),
        subplots=(),
        unit="g",
        grid_position=(2, 0, 1, 1),
    ),
    PlotGroupConfig(
        key="gyro",
        title="g. 3轴 GYRO",
        curves=("gyro_x", "gyro_y", "gyro_z"),
        subplots=(),
        unit="dps",
        grid_position=(2, 1, 1, 1),
    ),
    PlotGroupConfig(
        key="sensor14",
        title="e. 1/4号 Uh / Uc",
        curves=("uh1", "uc1", "uh4", "uc4"),
        subplots=(),
        unit="V",
        grid_position=(2, 2, 1, 1),
    ),
)
