# Pydisplay

Pydisplay is a Python upper-computer GUI for the STM32G474 PulseTIMR2 firmware on branch `Single`. It receives HJ131 data through an HJ380 BLE serial port, parses the confirmed 49-byte firmware frame, decodes PPG/IMU/Uh/Uc/UD values, plots them with PySide6 + PyQtGraph, records data, and replays saved sessions without hardware.

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
5. Data receiving starts after the port is opened. Use `暂停接收` to pause background reads while keeping the serial port open, and `开始接收` to resume.
6. Use `关闭串口` or `重连` for recovery.

Serial reading runs in a background thread. GUI controls do not read the serial port directly.

## Control Commands

The control panel builds the confirmed 13-byte firmware control frame through `pydisplay.protocol.commands`. Supported fields:

- PPG mode and MultiLED sub-mode
- Green/Red/IR LED levels `0..9`
- PPG ADC range `0x01..0x04`
- PPG pulse width `0x01..0x04`
- Gyro range `0x01..0x03`
- Accel range `0x01..0x04`

The firmware design is no ACK/NACK for this control frame.

## Data Recording

Recording creates a session directory:

```text
records/
  YYYYMMDD_HHMMSS_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

`raw_frames.bin` stores raw serial chunks or raw frames with PC timestamps. `decoded.csv` stores decoded samples. `metadata.json` stores software, firmware, serial, protocol, CSV, and control metadata. File writing is handled by `RecorderWorker`, not the GUI thread.

## Replay Mode

Replay supports:

- `raw_frames.bin`: replays raw records back through the parser/decoder path.
- `decoded.csv`: restores decoded samples directly for UI and algorithm debugging.
- Speeds: `0.25x`, `0.5x`, `1x`, `2x`, `5x`.
- Pause, resume, and stop.

Initial GUI behavior treats realtime serial input and replay as mutually exclusive.

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
- If bad frame ratio rises, inspect `raw_frames.bin` and `docs/protocol_analysis.md` field definitions.
- If recording fails, check path permissions and `logs/pydisplay.log`.
