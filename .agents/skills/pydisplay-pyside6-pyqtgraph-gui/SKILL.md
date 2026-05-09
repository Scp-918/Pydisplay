---
name: pydisplay-pyside6-pyqtgraph-gui
description: Use this skill when building the Pydisplay PySide6 Chinese GUI, PyQtGraph realtime plotting, plot buffers, GUI panels, Qt timers, curve visibility controls, or UI smoke tests.
---

# Pydisplay PySide6 PyQtGraph GUI Skill

## Purpose

Use this skill for GUI work:

- main window layout;
- serial connection panel;
- lower-device control panel;
- recording panel;
- health monitor panel;
- realtime plot panel;
- replay panel;
- Chinese labels and buttons;
- PyQtGraph plotting;
- GUI timers;
- plot performance optimization;
- GUI smoke tests.

## Required UI Sections

The main window must contain:

1. 串口连接区；
2. 下位机控制区；
3. 记录设置区；
4. 链路健康监控区；
5. 实时绘图区；
6. 回放区。

The GUI must be suitable for long-running laboratory experiments.

## Language Requirement

User-facing UI text should be Chinese.

Examples:

```text
串口
波特率
打开串口
关闭串口
重连
开始记录
停止记录
暂停绘图
继续绘图
回放 raw 文件
回放 CSV 文件
链路状态
坏帧率
记录队列
```

Avoid mojibake. Ensure Python files are UTF-8.

## Main Window Design

Recommended layout:

```text
MainWindow
  ├── top/left control area
  │     ├── SerialPanel
  │     ├── ControlPanel
  │     ├── RecordPanel
  │     ├── ReplayPanel
  │     └── HealthPanel
  └── central/right plot area
        └── PlotPanel with multiple PlotWidgets
```

Acceptable UI containers:

* `QMainWindow`;
* `QWidget`;
* `QSplitter`;
* `QGroupBox`;
* `QTabWidget`;
* `QScrollArea`.

## Plot Requirements

Use PyQtGraph.

Must plot:

1. PPG_G / PPG_R / PPG_IR;
2. accelerometer X/Y/Z;
3. gyroscope X/Y/Z;
4. Uh_1..Uh_4;
5. Uc_1..Uc_4;
6. UD_1..UD_2.

Recommended plot groups:

```text
PPG
Acceleration
Gyroscope
Uh
Uc
UD
```

Each plot should have:

* clear title;
* x-axis time in seconds;
* y-axis label and unit if known;
* legend or curve labels;
* auto range or reasonable range control.

## Plot Refresh Rule

Do not redraw on every sample.

Use a Qt timer:

```text
default plot refresh = 20 Hz
allowed range = 10–30 Hz
```

The data rate is expected to be 100 Hz, but plotting is lower frequency.

## Ring Buffer Rule

Do not let plot arrays grow without limit.

Maintain recent N seconds only.

Default:

```text
sample_rate = 100 Hz
window_seconds = 30
max_points = 3000
```

Support changing window length if convenient.

## Plot Optimization

Required:

* create curves once;
* call `setData` during refresh;
* skip hidden curves;
* do not recreate PlotWidget during runtime;
* do not update QLabel every sample;
* do not use pandas in the GUI update path;
* keep GUI thread responsive.

Recommended:

* use list/deque/numpy ring buffers;
* enable PyQtGraph clip/downsampling if useful;
* support pause plotting while recording continues.

## Pause Plot Behavior

When user clicks pause plotting:

* stop updating graphs;
* continue serial receive;
* continue parser;
* continue decoder;
* continue recorder;
* continue health statistics.

When plotting resumes:

* draw latest data window.

## Curve Visibility

Support hiding heavy or unwanted curves.

Minimum acceptable:

* checkboxes for each plot group;
* or checkboxes for individual curves if feasible.

Hidden curves should not call `setData`.

## Health Panel Refresh

Use a separate timer:

```text
health refresh = 1–5 Hz
```

Do not update health labels per frame.

## Control Panel

Include inputs for:

* PPG mode;
* LED brightness;
* PPG range;
* pulse width;
* IMU range;
* k value.

The k value affects UD calculation.

Command parameters must be validated before sending.

The exact command bytes must be produced by `protocol.command`, not by GUI code.

## Record Panel

Include:

* recording directory;
* recording name or file prefix;
* start recording;
* stop recording;
* record status;
* queue length display.

GUI must not write files directly.

## Replay Panel

Include:

* select raw_frames.bin;
* select decoded.csv;
* start replay;
* pause;
* continue;
* stop;
* playback speed.

Supported speeds:

```text
0.25x
0.5x
1x
2x
5x
```

## GUI Architecture Rule

GUI widgets should emit intent signals.

Business logic should live in services or workers.

Avoid putting parser, recorder, or serial IO logic directly in `MainWindow`.

## Context7 MCP

When uncertain about PySide6, Qt signals/slots, QThread, QTimer, or PyQtGraph APIs, use Context7 MCP to inspect current package documentation before coding.

Do not guess PySide6 method signatures when documentation can be checked.

## GUI Tests

Use `pytest-qt` for smoke tests.

Minimum tests:

* main window can instantiate;
* panels can instantiate;
* plot panel can receive fake samples;
* pause/resume toggles state;
* health panel update does not crash;
* close window stops timers/workers gracefully.

## Completion Criteria

Before committing:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_gui_smoke.py
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check pydisplay/gui
```

Then commit:

```bash
git add .
git commit -m "implement pyside6 gui and pyqtgraph realtime plotting"
```