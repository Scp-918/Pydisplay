# Pydisplay User Manual

## Quick Start

Run:

```powershell
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

Windows users can also double-click `Start_Pydisplay.bat` in the project root. It starts the app through the `Pydisplay_env` conda environment. If `conda` is not on PATH, use Anaconda Prompt and the command-line steps above.

Use the left-side panels for serial connection, firmware control, recording, replay, and health status. The right side displays realtime plots.

The left-side order is `串口连接 -> 下位机控制 -> 数据记录 -> 链路健康 -> 回放`. Replay is below health in the scrollable column, so routine monitoring keeps health visible and replay inputs stay lower until needed.

## Serial Workflow

Click `刷新串口`, choose the HJ380 COM port, keep baudrate `460800` unless firmware changes, then click `打开串口`. Data receiving starts after the port is opened. Use `暂停接收` to pause background serial reads without closing the port, and `开始接收` to resume. Use `关闭串口` before starting raw/csv replay.

## Plot Workflow

The top of the plot panel contains `暂停绘图`, `清空图表`, and `X轴长度`. Use `清空图表` to clear only the current visible plot buffer; serial receiving and recording are not stopped. Use `X轴长度` to choose how many recent seconds are visible on the realtime x-axis. Curve visibility checkboxes are placed further down at the bottom of the plot scroll area.

The default plot x-axis length is `5 s`. The realtime x-axis starts from the first decoded firmware frame, so new samples spread along time instead of stacking at x=0.

The plot grid uses `a,b,c / a,b,d / f,g,e`: `a` PPG, `b` Uh2/Uh3, `c` Uc2/Uc3, `d` UD1/UD2, `e` Uh/Uc channel 1/4, `f` ACC, and `g` GYRO. Areas `a` to `d` show only per-channel subplots with shared x-axes. Area `e` has two subplots: sensor 1 Uh/Uc and sensor 4 Uh/Uc. Areas `f` and `g` remain compact multi-curve plots. Plot titles do not include the grid letters.

Color choices are muted and signal-oriented: PPG is green/red/purple, Uh2/Uh3 is red/orange, Uc2/Uc3 is blue/cyan, UD1/UD2 is yellow/orange, and ACC/GYRO axes use distinct subdued colors.

## Control Defaults

The control panel starts with the firmware default parameter array from `Core/Src/main.c` on branch `Single`: k is `24`, PPG mode is `MultiLED`, Multi sub-mode is `G-R-IR`, Green/Red/IR LED levels are `5/1/1`, PPG range is `3`, pulse width is `3`, gyro range is `500 dps`, and accel range is `2 g`. The initial decoder uses the same gyro/accel range codes.

## Recording Workflow

Set the record path and experiment name, then click `开始记录`. Clicking `关闭串口` while recording automatically stops and finalizes the recording; `暂停接收` only pauses serial reads and keeps the recorder state unchanged. Each session contains `raw_frames.bin`, `decoded.csv`, and `metadata.json`.

## Replay Workflow

Choose either `raw_frames.bin` or `decoded.csv`, select a speed, then start replay. Realtime serial mode and replay mode should not be used at the same time in this initial version. Raw replay uses raw serial chunks when available and ignores debug-only bad-frame fragments by default; decoded CSV replay synthesizes 100 Hz timing from row order.

## Protocol

The parser uses the firmware-confirmed data frame documented in `docs/protocol_analysis.md`. The only unresolved protocol item is the absence of a firmware protocol version field; metadata records it as `null`.
