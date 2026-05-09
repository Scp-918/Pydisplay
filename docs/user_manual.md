# Pydisplay User Manual

## Quick Start

Run:

```powershell
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

Use the left-side panels for serial connection, firmware control, recording, replay, and health status. The right side displays realtime plots.

## Serial Workflow

Click `刷新串口`, choose the HJ380 COM port, keep baudrate `460800` unless firmware changes, then click `打开串口`. Use `关闭串口` before starting raw/csv replay.

## Recording Workflow

Set the record path and experiment name, then click `开始记录`. Stop recording before closing the application. Each session contains `raw_frames.bin`, `decoded.csv`, and `metadata.json`.

## Replay Workflow

Choose either `raw_frames.bin` or `decoded.csv`, select a speed, then start replay. Realtime serial mode and replay mode should not be used at the same time in this initial version.

## Protocol

The parser uses the firmware-confirmed data frame documented in `docs/protocol_analysis.md`. The only unresolved protocol item is the absence of a firmware protocol version field; metadata records it as `null`.
