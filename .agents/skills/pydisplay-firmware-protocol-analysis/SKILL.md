---
name: pydisplay-firmware-protocol-analysis
description: Use this skill when analyzing STM32G474 firmware, sensorlist documents, UART/BLE frame format, checksum, scaling factors, or control command protocol before implementing the Python GUI parser. Do not use this skill for GUI layout or plotting-only tasks.
---

# Pydisplay Firmware Protocol Analysis Skill

## Purpose

Use this skill before implementing or modifying any code related to:

- data frame parsing;
- frame length;
- field order;
- byte order;
- checksum or CRC;
- PPG / IMU / voltage scaling;
- upper-computer control command format;
- ACK / NACK handling;
- protocol version;
- simulator fake frame generation.

The key rule is:

> Do not invent the communication protocol. Confirm it from firmware source code, protocol definitions, sensorlist files, or project documentation.

The user has confirmed only these protocol facts:

```text
Frame header = 0xAA 0xBB
Frame tail   = 0xCC
```

Everything else must be verified.

## Required Context

Project directory:

```text
D:\Desktop\STM32G474\Pydisplay
```

Firmware repository:

```text
https://github.com/Scp-918/PulseTIMR2/tree/Single
```

MCU:

```text
STM32G474
```

Build system:

```text
CMake
```

Bluetooth path:

```text
STM32G474 -> HJ131 BLE module -> HJ380 BLE module -> PC serial port -> Python GUI
```

Python interpreter:

```text
D:\Code\anaconda24\envs\Pydisplay_env\python
```

## Mandatory First Step

Before writing parser, decoder, command, simulator, or fake frame code, inspect the firmware repository and local files.

Use local search commands such as:

```bash
rg "0xAA|0xBB|0xCC|frame|Frame|FRAME|packet|Packet|UART|USART|DMA|BLE|HJ131|HJ380|checksum|crc|CRC|PPG|IMU|acc|gyro|Uh|Uc|LED|mode|brightness|range|pulse|metadata"
```

Also inspect likely directories:

```text
Core/
Core/Src/
Core/Inc/
Drivers/
sensorlist/
CMakeLists.txt
```

If the firmware repo is not available locally, clone it or ask the user to provide the local path. If network access is unavailable, report this clearly and continue only with non-protocol modules.

## What Must Be Confirmed

For the data frame:

* frame header;
* frame tail;
* total frame length;
* payload length;
* whether there is a length field;
* field order;
* field type and signedness;
* byte order;
* sequence number field;
* device timestamp field;
* checksum / CRC algorithm;
* whether checksum includes header;
* whether checksum includes tail;
* sample rate;
* PPG_G / PPG_R / PPG_IR fields;
* accelerometer X/Y/Z fields;
* gyroscope X/Y/Z fields;
* Uh channel fields;
* Uc channel fields;
* voltage scaling;
* PPG scaling;
* accelerometer scaling;
* gyroscope scaling.

For control commands:

* command frame header;
* command frame tail;
* command length;
* command ID;
* parameter encoding;
* parameter range;
* checksum / CRC;
* byte order;
* ACK / NACK response;
* timeout behavior;
* retry behavior.

Required control parameters:

* PPG mode;
* LED brightness;
* PPG range;
* pulse width;
* IMU range.

## Required Output

Create or update:

```text
docs/protocol_analysis.md
```

The report must include:

```markdown
# Protocol Analysis

## Firmware source files checked

List all files that were actually inspected.

## Data frame format

- Header:
- Tail:
- Frame length:
- Payload length:
- Length field:
- Field order:
- Field types:
- Signedness:
- Endianness:
- Checksum / CRC:
- Sequence field:
- Device timestamp field:
- Sample rate:

## Data fields

- PPG_G:
- PPG_R:
- PPG_IR:
- Acc X:
- Acc Y:
- Acc Z:
- Gyro X:
- Gyro Y:
- Gyro Z:
- Uh channels:
- Uc channels:

## Scaling factors

- PPG:
- Acc:
- Gyro:
- Uh:
- Uc:
- UD:

## Control command format

- PPG mode:
- LED brightness:
- PPG range:
- Pulse width:
- IMU range:

## ACK / NACK behavior

Describe if available.

## Evidence

For each important conclusion, cite the source file path and nearby symbol/function/macro name.

## Unresolved questions

List every missing or ambiguous protocol item.

## Implementation decision

State whether parser implementation is allowed to proceed.
```

## Pause Conditions

Pause protocol implementation and create:

```text
docs/protocol_blockers.md
```

if any of the following are unknown:

* frame length;
* payload field order;
* byte order;
* checksum;
* PPG scaling;
* IMU scaling;
* Uh / Uc scaling;
* command frame format;
* command parameter ranges;
* ACK / NACK behavior if required by GUI.

The blocker report must include:

* confirmed facts;
* unknown facts;
* exact files searched;
* search keywords used;
* questions for the user or firmware engineer;
* safe work that can continue, such as GUI skeleton, recorder scaffolding, and decoded CSV replay.

## Allowed Work While Protocol Is Blocked

If protocol is blocked, do not implement real parser or real command builder.

Allowed:

* GUI layout;
* serial port scan/open/close skeleton;
* health panel skeleton;
* record panel skeleton;
* decoded.csv replay using placeholder documented fields;
* fake decoded sample generator for UI testing;
* test scaffolding;
* README and docs.

## Commit Rule

After completing protocol analysis:

```bash
git add .
git commit -m "add firmware protocol analysis report"
```

Only commit if the working tree contains a coherent report and no speculative parser implementation.