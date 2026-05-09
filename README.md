# Pydisplay

Pydisplay is a Python GUI upper-computer project for the STM32G474 PulseTIMR2 firmware on branch `Single`. It receives HJ131 data through an HJ380 BLE serial port, decodes the confirmed firmware protocol, displays real-time plots, records data, and supports replay-based no-hardware debugging.

## Environment

- Conda environment: `Pydisplay_env`
- GUI stack: PySide6 + PyQtGraph
- Firmware: `https://github.com/Scp-918/PulseTIMR2/tree/Single`
- Receiver serial module: HJ380

Dependencies are expected to already be installed in `Pydisplay_env`.

## Start

```powershell
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

For non-interactive startup validation:

```powershell
python -m pydisplay --smoke-test
```

## Current Status

- Protocol analysis is documented in `docs/protocol_analysis.md`.
- Blocking protocol decode questions have been resolved in `docs/protocol_questions.md`.
- Stage 1 provides the package entry point, logging setup, and an empty Chinese PySide6 main window.

Later stages will add parser/decoder, serial I/O, recorder, replay, health monitoring, and full plotting.

## Tests

```powershell
pytest
```
