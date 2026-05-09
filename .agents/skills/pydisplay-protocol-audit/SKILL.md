---
name: pydisplay-protocol-audit
description: Use when analyzing STM32G474 firmware, sensorlist, LabVIEW artifacts, or docs to confirm BLE/serial frame format, checksum, byte order, scaling factors, and control command protocol for the Pydisplay Python GUI. Do not use for generic GUI work.
---

# Pydisplay Protocol Audit Skill

Use this skill before implementing or modifying any parser, decoder, checksum, or command-sending code in the STM32G474 Pydisplay project.

The core rule is: never invent the communication protocol. Confirm it from source code, sensorlist, LabVIEW artifacts, or project documentation.

## Inputs

Expected project context:

- MCU: STM32G474.
- Firmware repo or local copy may correspond to `https://github.com/Scp-918/PulseTIMR2/tree/Single`.
- Python GUI project directory: `D:\Desktop\STM32G474\Pydisplay`.
- Confirmed by user:
  - Frame header is currently `0xAA 0xBB`.
  - Frame tail is currently `0xCC`.
- Still required:
  - Locate evidence in firmware or documents.
  - Confirm frame length, payload layout, checksum, byte order, scaling factors, and command format.

## Required first steps

1. Inspect the repository layout.
2. Identify whether firmware source is present locally.
3. Search for protocol-related code and docs before writing parser code.
4. Produce or update `docs/protocol_analysis.md`.
5. Only write protocol implementation after evidence is documented.

Use searches similar to:

    rg -n "AA|BB|CC|frame|packet|header|tail|checksum|crc|UART|USART|HAL_UART|DMA|BLE|HJ131|HJ380|PPG|IMU|gyro|acc|Uh|Uc|UD|command|cmd|LED|mode|range|pulse" .

Also search for possible Chinese names:

    rg -n "帧头|帧尾|校验|协议|串口|蓝牙|命令|亮度|量程|脉宽|加速度|陀螺|电压|高电平|低电平|传感器" .

## Evidence requirements

For each confirmed protocol item, record:

- Source file path.
- Function or variable name.
- Line numbers when possible.
- Exact value or formula.
- Confidence level:
  - confirmed
  - probable
  - conflicting
  - unknown

Do not treat user-facing assumptions as implementation facts unless confirmed in source or documentation.

## Items that must be confirmed

### Frame structure

Confirm:

- Frame header bytes.
- Frame tail bytes.
- Fixed-length or variable-length frame.
- Total frame length.
- Payload length.
- Whether length field exists.
- Whether sequence number exists.
- Whether MCU timestamp exists.
- Whether sample index exists.
- Whether metadata or status bits exist.

### Payload layout

Confirm field order and data type for:

- PPG_G.
- PPG_R.
- PPG_IR.
- acc_x.
- acc_y.
- acc_z.
- gyro_x.
- gyro_y.
- gyro_z.
- Uh channel 1–4.
- Uc channel 1–4.
- UD channel 1–2, if transmitted.
- Any temperature, status, battery, error, sensor flag, or reserved field.

For each field, confirm:

- Integer or float.
- Signed or unsigned.
- Width in bytes.
- Endianness.
- Raw range.
- Physical unit.
- Scaling factor.
- Offset, if any.

### Checksum or CRC

Confirm:

- Algorithm:
  - sum
  - xor
  - CRC8
  - CRC16
  - other
- Initial value.
- Polynomial, if CRC.
- Reflected or not.
- Final xor, if any.
- Covered byte range.
- Location of checksum bytes.
- Whether header and tail are included.

Do not implement a guessed checksum. If not found, create a placeholder interface and stop protocol implementation.

### Control commands

Confirm command format for:

- PPG mode.
- LED brightness.
- PPG range.
- Pulse width.
- IMU range.

For each command, confirm:

- Command header.
- Command ID.
- Payload fields.
- Parameter type and range.
- Endianness.
- Checksum.
- Tail.
- Whether ACK or NACK exists.
- Whether command should be sent over same serial port.
- Whether command can be sent while streaming.

## Required output: protocol analysis report

Create or update:

    docs/protocol_analysis.md

The report must include:

    # Protocol Analysis

    ## Summary

    ## Confirmed frame format

    ## Confirmed payload layout

    ## Confirmed checksum

    ## Confirmed scaling factors

    ## Confirmed control commands

    ## Evidence table

    | Item | Value | Evidence | Confidence |
    | --- | --- | --- | --- |

    ## Conflicts

    ## Unknowns

    ## Questions for user

    ## Implementation decision

## Stop conditions

Pause and report before implementation if any of the following are true:

1. Frame length cannot be confirmed.
2. Payload field order cannot be confirmed.
3. Checksum cannot be confirmed.
4. Endianness cannot be confirmed.
5. Scaling factors cannot be confirmed.
6. Control command format cannot be confirmed.
7. Firmware and LabVIEW disagree.
8. `0xAA 0xBB` / `0xCC` conflicts with source evidence.
9. Sensorlist and firmware disagree.
10. Hardware behavior cannot be inferred from source.

Use this report format when stopping:

    ## 暂停原因

    ## 已确认内容

    ## 未确认内容

    ## 风险

    ## 需要用户确认的问题

## Implementation rules after confirmation

Once confirmed:

1. Put protocol constants in `src/pydisplay/config/protocol.yaml` or `src/pydisplay/core/constants.py`.
2. Put frame state machine in `src/pydisplay/protocol/frame_parser.py`.
3. Put checksum implementation in `src/pydisplay/protocol/checksum.py`.
4. Put payload decoder in `src/pydisplay/protocol/decoder.py`.
5. Put command builder in `src/pydisplay/protocol/commands.py`.
6. Add tests:
   - `tests/test_parser.py`
   - `tests/test_decoder.py`
   - `tests/test_commands.py`

## Parser design requirements

The parser must implement a resynchronizing state machine:

- `FIND_HEADER`
- `READ_BODY`
- `READ_TAIL`
- `CHECKSUM`
- `RESYNC`

It must track:

- total_frames
- valid_frames
- bad_frames
- bad_frame_ratio
- checksum_fail_count
- tail_mismatch_count
- length_error_count
- resync_count
- parser_buffer_bytes

Bad frames are counted. Do not allow one bad frame to corrupt the entire stream.

## Decoder rules

The decoder must:

1. Preserve PC receive timestamp.
2. Preserve frame index or sample index when available.
3. Convert raw fields using confirmed scaling only.
4. Compute:
   `UD = (Uh - Uc) / (k - Uc)`
5. Guard against denominator close to zero.
6. Mark invalid or suspicious samples explicitly.
7. Avoid GUI dependencies.

## Testing requirements

Use deterministic byte sequences.

Test at least:

1. Valid single frame.
2. Valid multiple frames concatenated.
3. Noise before header.
4. Partial frame across multiple chunks.
5. Bad tail.
6. Bad checksum.
7. Resync after corrupted frame.
8. Buffer does not grow without bound.
9. Decoder scaling.
10. Command builder format.

Run:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_parser.py tests/test_decoder.py tests/test_commands.py -q

## Git rule

After protocol audit and tests pass:

    git status
    git add docs/protocol_analysis.md src/pydisplay/protocol tests
    git commit -m "add protocol analysis and parser baseline"