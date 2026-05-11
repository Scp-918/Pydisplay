"""PyQtGraph 曲线管理器。

初始化时创建所有 PlotWidget 和 PlotDataItem。
刷新时只调用已有曲线的 setData()，避免每帧创建新曲线导致卡顿。
"""

from __future__ import annotations

import time

from .curve_config import CURVE_BY_KEY, CURVES, PLOT_GROUPS, PlotGroupConfig
from .ring_buffer import SampleRingBuffer


class PlotManager:
    """持有所有曲线对象，并集中刷新。"""

    def __init__(self, layout, *, window_seconds: float = 10.0) -> None:
        import pyqtgraph as pg

        self.window_seconds = window_seconds
        self.visible: dict[str, bool] = {curve.key: True for curve in CURVES}
        self.curves: dict[str, list[object]] = {curve.key: [] for curve in CURVES}
        self.plot_widgets = {}

        layout.setSpacing(8)
        for column in range(3):
            layout.setColumnStretch(column, 1)
        for row in range(3):
            layout.setRowStretch(row, 1)

        for group in PLOT_GROUPS:
            widget = self._build_group_widget(pg, group)
            row, column, row_span, column_span = group.grid_position
            layout.addWidget(widget, row, column, row_span, column_span)

    def set_curve_visible(self, key: str, visible: bool) -> None:
        self.visible[key] = visible
        for item in self.curves.get(key, []):
            item.setVisible(visible)

    def set_window_seconds(self, window_seconds: float) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.window_seconds = window_seconds

    def refresh(self, buffer: SampleRingBuffer) -> None:
        """按当前可见性从 ring buffer 读取数据并刷新曲线。"""
        for key, items in self.curves.items():
            if not self.visible.get(key, True):
                continue
            x, y = buffer.get_series(key, self.window_seconds)
            for item in items:
                item.setData(x, y)

    def clear(self) -> None:
        """立即清空屏幕上已有的 PlotDataItem 数据。"""
        for items in self.curves.values():
            for item in items:
                item.setData([], [])

    def _build_group_widget(self, pg, group: PlotGroupConfig):
        """创建一个九宫格中的绘图区块。

        a/b/c/d 这类 show_combined=False 的区块只包含独立子图；
        subplot_groups 可在一个子图里绘制多条曲线，例如 1 号传感器 Uh/Uc。
        """
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout

        container = QGroupBox(group.title)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(4)

        link_root = None
        if group.show_combined:
            main_plot = self._make_plot(pg, group.title, group.unit, minimum_height=170)
            if len(group.curves) > 1:
                main_plot.addLegend(offset=(5, 5))
            container_layout.addWidget(main_plot)
            self.plot_widgets[f"{group.key}:main"] = main_plot
            link_root = main_plot
            for curve_key in group.curves:
                self._add_curve(pg, main_plot, curve_key)

        for curve_key in group.subplots:
            curve = CURVE_BY_KEY[curve_key]
            link_root = self._add_subplot(
                pg,
                container_layout,
                group_key=group.key,
                plot_key=curve_key,
                title=curve.label,
                unit=curve.unit,
                curve_keys=(curve_key,),
                link_root=link_root,
            )

        for index, subplot_group in enumerate(group.subplot_groups, start=1):
            link_root = self._add_subplot(
                pg,
                container_layout,
                group_key=group.key,
                plot_key=f"group{index}",
                title=subplot_group.title,
                unit=subplot_group.unit,
                curve_keys=subplot_group.curves,
                link_root=link_root,
            )

        return container

    def _add_subplot(self, pg, layout, *, group_key: str, plot_key: str, title: str, unit: str, curve_keys: tuple[str, ...], link_root):
        subplot = self._make_plot(pg, title, unit, minimum_height=118)
        if len(curve_keys) > 1:
            subplot.addLegend(offset=(5, 5))
        if link_root is None:
            link_root = subplot
        else:
            subplot.setXLink(link_root)
        layout.addWidget(subplot)
        self.plot_widgets[f"{group_key}:{plot_key}"] = subplot
        for curve_key in curve_keys:
            self._add_curve(pg, subplot, curve_key, width=1.0)
        return link_root

    @staticmethod
    def _make_plot(pg, title: str, unit: str, *, minimum_height: int):
        plot = pg.PlotWidget(title=title)
        plot.setMinimumHeight(minimum_height)
        plot.showGrid(x=True, y=True, alpha=0.2)
        plot.setLabel("bottom", "时间", units="s")
        plot.setLabel("left", title, units=unit)
        plot.enableAutoRange(axis="y", enable=True)
        return plot

    def _add_curve(self, pg, plot, curve_key: str, *, width: float = 1.2) -> None:
        curve = CURVE_BY_KEY[curve_key]
        item = plot.plot(name=curve.label, pen=pg.mkPen(curve.color, width=width))
        self.curves[curve_key].append(item)


class PlotFpsCounter:
    def __init__(self) -> None:
        self.frames = 0
        self.last_time = time.monotonic()
        self.fps = 0.0

    def tick(self) -> float:
        self.frames += 1
        now = time.monotonic()
        elapsed = now - self.last_time
        if elapsed >= 1.0:
            self.fps = self.frames / elapsed
            self.frames = 0
            self.last_time = now
        return self.fps
