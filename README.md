# Pydisplay

Pydisplay is a Python upper-computer GUI for the STM32G474 PulseTIMR2 firmware on branch `Single`. It receives HJ131 data through an HJ380 BLE serial port, parses the confirmed 51-byte firmware frame, decodes PPG/IMU/Uh/Uc/UD values, plots them with PySide6 + PyQtGraph, records data, and replays saved sessions without hardware.

## Environment

- Conda environment: `Pydisplay_env`
- GUI stack: PySide6 + PyQtGraph
- Serial stack: pyserial
- Test stack: pytest
- Firmware repo: `https://github.com/Scp-918/PulseTIMR2/tree/Single`
- Firmware commit analyzed: `3714333572dc985c407dbb680183785cc0b92b66`

Dependencies are expected to already be installed in `Pydisplay_env`.

## Start

```powershell
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

Windows double-click startup:

1. Double-click `Start_Pydisplay.bat` in the project root.
2. The batch file enters this directory and runs `conda run -n Pydisplay_env python -m pydisplay`.
3. If Windows reports that `conda` cannot be found, start the app from Anaconda Prompt with the command-line steps above.

Non-interactive startup validation:

```powershell
conda run -n Pydisplay_env python -m pydisplay --smoke-test
```

## Serial Connection

1. Connect the HJ380 receiver module to the PC.
2. Click `刷新串口`.
3. Select the HJ380 COM port and baudrate. Firmware documentation targets `460800`.
4. Click `打开串口`.
5. Data receiving starts after the port is opened. Use `暂停接收` to pause background reads while keeping the serial port open, and `开始接收` to resume. When no serial port is open but replay is running, the same two buttons pause/resume replay.
6. Use `关闭串口` or `重连` for recovery.

Serial reading runs in a background thread. GUI controls do not read the serial port directly.

## GUI Layout

The left control column is intentionally compact so the realtime plots get more screen space. Its order is now:

```text
串口连接 -> 下位机控制 -> 数据记录 -> 链路健康 -> 回放
```

The replay panel sits below the health panel in the scrollable left column. In normal monitoring you usually see serial/control/recording/health first; scroll down when you need replay inputs.

The realtime plot header keeps `暂停绘图`, `清空图表`, and an editable `X轴长度` value. `清空图表` clears the current on-screen plot buffer only; it does not stop serial receiving or recording. Curve visibility checkboxes are placed further down at the bottom of the plot scroll area, so routine viewing gives more space to plots.

Startup defaults are aligned with the firmware initial state where possible: `k = 24`, realtime x-axis length is `5 s`, PPG mode is `MultiLED`, Multi sub-mode is `G-R-IR`, LED levels are Green `5`, Red `1`, IR `1`, PPG range is `3`, pulse width is `3`, gyro range is `500 dps`, and accel range is `2 g`.

The plot area uses a 3x3 layout:

```text
a, b, c
a, b, d
f, g, e
```

`a` is 3-color PPG, `b` is Uh channel 2/3, `c` is Uc channel 2/3, `d` is UD1/UD2, `e` is Uh/Uc channel 1/4, `f` is ACC, and `g` is GYRO. Areas `a` to `d` show per-channel subplots only, with shared x-axes inside each area. Area `e` now has one subplot for sensor 1 Uh/Uc and one subplot for sensor 4 Uh/Uc. Areas `f` and `g` use compact multi-curve plots. Plot titles do not include the grid letters.

Curve colors use muted, signal-oriented colors: PPG uses green/red/purple, Uh2/Uh3 uses red/orange, Uc2/Uc3 uses blue/cyan, and UD1/UD2 uses yellow/orange.

## Control Commands

The control panel builds the confirmed 13-byte firmware control frame through `pydisplay.protocol.commands`. Supported fields:

- PPG mode and MultiLED sub-mode
- Green/Red/IR LED levels `0..9`
- PPG ADC range `0x01..0x04`
- PPG pulse width `0x01..0x04`
- Gyro range `0x01..0x03`
- Accel range `0x01..0x04`

The firmware design is no ACK/NACK for this control frame.

The GUI control defaults follow the firmware `g_sensor_param_array` in `Core/Src/main.c` on branch `Single`: `01 01 05 01 01 03 03 02 01` for mode/submode/LED/range/pulse/gyro/accel. The initial decoder uses the same gyro and accel range codes, so plotted IMU values match the default firmware scale before any command is sent.

The realtime plot x-axis uses the first decoded firmware frame as time zero. This avoids the earlier symptom where every decoded sample had `relative_time_s = 0` and PyQtGraph showed each curve as a vertical line.

## Data Recording

Recording creates a session directory:

```text
records/
  YYYYMMDD_HHMMSS_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

`raw_frames.bin` stores raw serial chunks or raw frames with PC timestamps. `decoded.csv` stores compact decoded samples and intentionally omits `relative_time_s`, `timestamp_pc_ns`, `seq_gap`, `lost_before`, and `source`. `metadata.json` stores software, firmware, serial, protocol, CSV, and control metadata. File writing is handled by `RecorderWorker`, not the GUI thread.

## Replay Mode

Replay supports:

- `raw_frames.bin`: reads the raw serial chunks from the bin file, extracts valid firmware frames with the real parser, then replays those raw frames through the parser/decoder path on a reconstructed 100 Hz frame clock. This avoids using serial-read chunk timestamps as sample timestamps; a single serial read can contain half a frame or two frames, and short Windows sleeps can otherwise make playback look closer to 50 Hz. The original chunk-timestamp path remains available in code for diagnostics.
- `decoded.csv`: restores decoded samples directly for UI and algorithm debugging. Because compact CSV files no longer store timestamps, decoded CSV replay synthesizes 100 Hz timing from row order.
- Speeds: `0.25x`, `0.5x`, `1x`, `2x`, `5x`.
- Pause, resume, and stop.

Initial GUI behavior treats realtime serial input and replay as mutually exclusive.

Replay completion is detected by the number of records loaded from the file; the raw bin format does not need an end marker. This avoids confusing a normal "pause recording, then continue recording" workflow with artificial end records.

## Protocol Documentation

- `docs/protocol_analysis.md`: confirmed firmware protocol, field layout, checksum, scaling, commands.
- `docs/protocol_questions.md`: resolved and remaining non-blocking protocol questions.
- `docs/data_format.md`: raw bin, decoded CSV, and metadata formats.

Current non-blocking notes:

- No firmware protocol version field was found; metadata records `protocol_version = null`.
- No additional calibration table is applied beyond the confirmed AD4007 voltage formula and PPG raw counts.

## Tests

```powershell
pytest
```

Core tests do not require serial hardware.

## Useful Scripts

```powershell
python scripts\run_app.py
python scripts\inspect_raw_bin.py records\...\raw_frames.bin
python scripts\simulate_device.py
```

`simulate_device.py` emits decoded-looking samples for UI/debug work only and is marked `simulation only, not firmware protocol`.

## Troubleshooting

- If PySide6 is missing, confirm the active environment is `Pydisplay_env`.
- If no COM port appears, reconnect HJ380 and click `刷新串口`.
- If raw replay speed looks wrong, inspect the file with `scripts\inspect_raw_bin.py`. New GUI replay reconstructs a 100 Hz frame clock from valid frames and `frame_seq`, so irregular `raw_serial_chunk` timestamps do not slow the normal replay path.
- If recording fails, check path permissions and `logs/pydisplay.log`.
