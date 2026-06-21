"""绘图曲线配置。

每条曲线的 key 必须对应 DecodedSample 的字段名。
label 是 GUI 中显示的名称，unit 是 y 轴单位或说明。
"""

from __future__ import annotations

from dataclasses import dataclass

from pydisplay.protocol.constants import ADC_VOLTS_PER_COUNT


@dataclass(frozen=True, slots=True)
class CurveConfig:
    key: str
    label: str
    group: str
    unit: str
    color: str
    scale: float = 1.0


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


SLOT_COLORS = ("#4C78A8", "#3F9C9A", "#75A66A", "#D08A3C", "#B65C5A", "#7A68A6")


CURVES = [
    CurveConfig(
        f"adc_ch{channel}_slot{slot}",
        f"CH{channel} Slot{slot}",
        f"ADC CH{channel}",
        "V",
        SLOT_COLORS[slot],
        ADC_VOLTS_PER_COUNT,
    )
    for channel in range(1, 5)
    for slot in range(6)
]

CURVE_BY_KEY = {curve.key: curve for curve in CURVES}


PLOT_GROUPS = tuple(
    PlotGroupConfig(
        key=f"adc_ch{channel}_slot{slot}",
        title=f"ADC CH{channel} {window_name} sample {sample_index + 1} (slot{slot})",
        curves=(f"adc_ch{channel}_slot{slot}",),
        subplots=(),
        unit="V",
        grid_position=(((channel - 1) * 2) + window_index, sample_index, 1, 1),
    )
    for channel in range(1, 5)
    for window_index, (window_name, slots) in enumerate((("early", range(3)), ("late", range(3, 6))))
    for sample_index, slot in enumerate(slots)
)
