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
class SubplotGroupConfig:
    """一个独立子图配置；可包含一条或多条曲线。"""

    title: str
    curves: tuple[str, ...]
    unit: str


@dataclass(frozen=True, slots=True)
class PlotGroupConfig:
    """一个绘图区块的静态配置。

    grid_position 使用 Qt 的 addWidget(row, column, row_span, column_span) 顺序。
    curves 表示该区块包含哪些曲线；subplots 表示哪些单曲线需要独立子图。
    subplot_groups 用于“一个子图内绘制多条曲线”的情况。
    show_combined 为 False 时不创建合并总图，只创建独立子图。
    """

    key: str
    title: str
    curves: tuple[str, ...]
    subplots: tuple[str, ...]
    unit: str
    grid_position: tuple[int, int, int, int]
    show_combined: bool = True
    subplot_groups: tuple[SubplotGroupConfig, ...] = ()


CURVES = [
    CurveConfig("ppg_g", "PPG_G", "PPG", "raw", "#3E8F5C"),
    CurveConfig("ppg_r", "PPG_R", "PPG", "raw", "#B94E4E"),
    CurveConfig("ppg_ir", "PPG_IR", "PPG", "raw", "#7A68A6"),
    CurveConfig("acc_x", "ACC_X", "ACC", "g", "#4F7FA8"),
    CurveConfig("acc_y", "ACC_Y", "ACC", "g", "#75A66A"),
    CurveConfig("acc_z", "ACC_Z", "ACC", "g", "#A77FB3"),
    CurveConfig("gyro_x", "GYRO_X", "GYRO", "dps", "#5D6FA8"),
    CurveConfig("gyro_y", "GYRO_Y", "GYRO", "dps", "#B56C82"),
    CurveConfig("gyro_z", "GYRO_Z", "GYRO", "dps", "#8C9856"),
    CurveConfig("uh1", "Uh1", "Uh", "V", "#9D6A66"),
    CurveConfig("uh2", "Uh2", "Uh", "V", "#B65C5A"),
    CurveConfig("uh3", "Uh3", "Uh", "V", "#C87A3A"),
    CurveConfig("uh4", "Uh4", "Uh", "V", "#A07144"),
    CurveConfig("uc1", "Uc1", "Uc", "V", "#5E83A6"),
    CurveConfig("uc2", "Uc2", "Uc", "V", "#4C78A8"),
    CurveConfig("uc3", "Uc3", "Uc", "V", "#3F9C9A"),
    CurveConfig("uc4", "Uc4", "Uc", "V", "#5C9A8D"),
    CurveConfig("ud1", "UD1", "UD", "ratio", "#BFA43A"),
    CurveConfig("ud2", "UD2", "UD", "ratio", "#D08A3C"),
]

CURVE_BY_KEY = {curve.key: curve for curve in CURVES}


PLOT_GROUPS = (
    PlotGroupConfig(
        key="ppg",
        title="3色 PPG",
        curves=("ppg_g", "ppg_r", "ppg_ir"),
        subplots=("ppg_g", "ppg_r", "ppg_ir"),
        unit="raw",
        grid_position=(0, 0, 2, 1),
        show_combined=False,
    ),
    PlotGroupConfig(
        key="uh23",
        title="2/3号 Uh",
        curves=("uh2", "uh3"),
        subplots=("uh2", "uh3"),
        unit="V",
        grid_position=(0, 1, 2, 1),
        show_combined=False,
    ),
    PlotGroupConfig(
        key="uc23",
        title="2/3号 Uc",
        curves=("uc2", "uc3"),
        subplots=("uc2", "uc3"),
        unit="V",
        grid_position=(0, 2, 1, 1),
        show_combined=False,
    ),
    PlotGroupConfig(
        key="ud",
        title="UD1 / UD2",
        curves=("ud1", "ud2"),
        subplots=("ud1", "ud2"),
        unit="ratio",
        grid_position=(1, 2, 1, 1),
        show_combined=False,
    ),
    PlotGroupConfig(
        key="acc",
        title="3轴 ACC",
        curves=("acc_x", "acc_y", "acc_z"),
        subplots=(),
        unit="g",
        grid_position=(2, 0, 1, 1),
    ),
    PlotGroupConfig(
        key="gyro",
        title="3轴 GYRO",
        curves=("gyro_x", "gyro_y", "gyro_z"),
        subplots=(),
        unit="dps",
        grid_position=(2, 1, 1, 1),
    ),
    PlotGroupConfig(
        key="sensor14",
        title="1/4号 Uh / Uc",
        curves=("uh1", "uc1", "uh4", "uc4"),
        subplots=(),
        unit="V",
        grid_position=(2, 2, 1, 1),
        show_combined=False,
        subplot_groups=(
            SubplotGroupConfig("1号传感器 Uh/Uc", ("uh1", "uc1"), "V"),
            SubplotGroupConfig("4号传感器 Uh/Uc", ("uh4", "uc4"), "V"),
        ),
    ),
)
