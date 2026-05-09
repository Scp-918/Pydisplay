# Pydisplay Protocol Analysis

## 1. Firmware Source

- Repo: https://github.com/Scp-918/PulseTIMR2/tree/Single
- Branch: Single
- Commit: `3714333572dc985c407dbb680183785cc0b92b66`
- Local analysis path: `.codex_firmware/PulseTIMR2`
- Analysis date: 2026-05-10
- Target MCU: STM32G474
- Build system: CMake

## 2. Search Scope

Checked firmware paths:

- `CMakeLists.txt`
- `Core/Src/`
- `Core/Inc/`
- `Sensorlist/`
- `README.md`

Searched required protocol and sensor keywords including `0xAA`, `0xBB`, `0xCC`, `UART`, `USART`, `HAL_UART`, `DMA`, `BLE`, `HJ131`, `HJ380`, `frame`, `packet`, `protocol`, `checksum`, `crc`, `sum`, `PPG`, `LED`, `IMU`, `ACC`, `GYRO`, `ADC`, `voltage`, `Uh`, `Uc`, `UD`, `cmd`, `command`, `control`, `mode`, `range`, `pulse`, `brightness`, and `metadata`.

## 3. Confirmed Summary

| Item | Conclusion | Source |
|---|---|---|
| Data link | USART1 through BLE transparent serial, target baudrate 460800 | `README.md:205`, `Core/Src/usart.c:43-44`, `Core/Inc/ble.h:16` |
| Data frame header | `0xAA 0xBB` | `Core/Inc/ble_comm.h:36-37`, `Core/Src/ble_comm.c:72-73` |
| Data frame tail | `0xCC` | `Core/Inc/ble_comm.h:38`, `Core/Src/ble_comm.c:122-123` |
| Data frame length | Fixed 49 bytes | `Core/Inc/ble_comm.h:27`, `README.md:205` |
| Payload length | 45 bytes, byte 2 through byte 46 | `Core/Inc/ble_comm.h:44-59`, `Core/Src/ble_comm.c:75-114` |
| Checksum | XOR of bytes `[2..46]`, header and tail excluded | `Core/Inc/ble_comm.h:61-66`, `Core/Src/ble_comm.c:115-120`, `README.md:213` |
| Byte order | Data payload values are little-endian in BLE frame | `Core/Src/ble_comm.c:27-52`, `README.md:207` |
| Frame sequence | Not present in data frame | No sequence field in `Core/Inc/ble_comm.h:41-62` |
| Firmware timestamp | Not present in data frame | No timestamp field in `Core/Inc/ble_comm.h:41-62`; search found only timeout uses of `HAL_GetTick` |
| Nominal output cadence | 4-phase 400 Hz state machine produces one fused frame per phase-4 cycle, intended 100 Hz | `Core/Src/main.c:831-835`, `Core/Src/main.c:883-887` |
| Active TX path | Main loop packs one 49-byte frame and sends it by UART DMA when pending | `Core/Src/main.c:1035-1040` |
| Control frame | 13 bytes, header `0xAB 0xCD`, tail `0xEF 0xFA`, no checksum field found | `Core/Src/main.c:64-78`, `Core/Src/main.c:451-504`, `README.md:216-230` |
| Control ACK | Confirmed no ACK/NACK response for sensor parameter frame | User confirmation 2026-05-10; `Core/Src/main.c:517-530`, `Core/Src/main.c:1164-1195`; only internal `g_sensor_cfg_apply_error` |
| Protocol version | Not found | `rg protocol_version/PROTOCOL_VERSION/version` found no frame version definition |

## 4. Data Frame Layout

Single data frame:

```text
0..1   header: 0xAA 0xBB
2..46  payload
47     checksum: XOR(bytes 2..46)
48     tail: 0xCC
```

Payload fields:

| Offset | Field | Bytes | Type | Signed | Endian | Scale / decode | Source |
|---:|---|---:|---|---|---|---|---|
| 2 | Uc1 / adc_ch1_early_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | `volts = signed_int24 * (4.096 / 131072.0)` | `Core/Src/ble_comm.c:81-89`, `Core/Src/main.c:607-630`; user confirmation 2026-05-10 |
| 5 | Uh1 / adc_ch1_late_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 8 | Uc2 / adc_ch2_early_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 11 | Uh2 / adc_ch2_late_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 14 | Uc3 / adc_ch3_early_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 17 | Uh3 / adc_ch3_late_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 20 | Uc4 / adc_ch4_early_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 23 | Uh4 / adc_ch4_late_code | 3 | int24 stored from `int32_t` low 24 bits | signed raw code | little | same as above | same as above |
| 26 | PPG_G | 3 | uint24 | unsigned | little | Firmware-aligned MAX30101 raw count | `Core/Src/ble_comm.c:92-101`, `Core/Src/MAX30101.c:577-596` |
| 29 | PPG_R | 3 | uint24 | unsigned | little | Firmware-aligned MAX30101 raw count | same as above |
| 32 | PPG_IR | 3 | uint24 | unsigned | little | Firmware-aligned MAX30101 raw count | same as above |
| 35 | GYRO_X | 2 | int16 | signed | little | `dps = raw * mdps_per_lsb / 1000` | `Core/Src/ble_comm.c:104-113`, `Core/Src/LSM9DS1.c:212-217`, `Core/Src/LSM9DS1.c:587-590` |
| 37 | GYRO_Y | 2 | int16 | signed | little | same as above | same as above |
| 39 | GYRO_Z | 2 | int16 | signed | little | same as above | same as above |
| 41 | ACC_X | 2 | int16 | signed | little | `g = raw * mg_per_lsb / 1000` | `Core/Src/ble_comm.c:104-113`, `Core/Src/LSM9DS1.c:212-217`, `Core/Src/LSM9DS1.c:581-584` |
| 43 | ACC_Y | 2 | int16 | signed | little | same as above | same as above |
| 45 | ACC_Z | 2 | int16 | signed | little | same as above | same as above |
| 47 | checksum | 1 | uint8 | unsigned | n/a | XOR of bytes 2..46 | `Core/Src/ble_comm.c:115-120` |
| 48 | tail | 1 | uint8 | unsigned | n/a | `0xCC` | `Core/Src/ble_comm.c:122-123` |

Important mapping note: firmware order for IMU is `Gx, Gy, Gz, Ax, Ay, Az`, not acceleration first. The Python decoder should expose both source order and user-facing names clearly.

## 5. ADC / Voltage Data

Confirmed:

- ADC payload covers 4 phase/state channels, each with `early_code` and `late_code`.
- Each transmitted ADC value is written as the low 24 bits of an `int32_t` in little-endian order.
- AD4007 raw acquisition decodes 24-bit SPI data by right-shifting 6 bits, masking 18 bits, sign-extending bit 17, and averaging samples.
- Firmware defines `AD4007_VREF = 4.096f`.
- User confirmation on 2026-05-10 maps `adc_data[ch].early_code` to `Uc` and `adc_data[ch].late_code` to `Uh`.
- The 4 transmitted ADC channels map in frame order to experiment channels `1..4`.
- PC-side AD4007 conversion uses no external offset and the 17-bit full-scale denominator:

```text
temp32 = data[0] + data[1] * 256 + data[2] * 65536
if temp32 >= 8388608:
    temp32 -= 16777216
volts = temp32 * (4.096 / 131072.0)
```

Sources:

- `Core/Inc/sensor_ringbuffer.h:41-62`
- `Core/Inc/AD4007.h:12-44`
- `Core/Src/AD4007.c:74-91`
- `Core/Src/AD4007.c:340-362`
- `Core/Src/main.c:564-630`
- User confirmation 2026-05-10 for Uh/Uc mapping and PC-side voltage formula.

No external gain, external offset, or calibration term has been specified for PC decoding. Metadata should record the formula above and leave calibration fields empty unless later provided.

## 6. PPG Decode

Confirmed:

- PPG source sensor is MAX30101.
- PPG output fields are Green, Red, IR.
- Firmware reads FIFO entries as 3 bytes per active LED channel.
- Firmware converts each FIFO channel as big-endian 3-byte raw, then right shifts by `s_ppg_right_shift` and masks by `s_ppg_valid_mask`.
- The transmitted BLE frame contains the already aligned `ppg_data[0..2]` as 3-byte little-endian unsigned integers.
- User confirmation on 2026-05-10: PPG should be recorded as firmware output raw counts only, with no PC-side physical scaling.

LED pulse-width dependent valid bits:

| `led_pw_code` | Valid bits | Right shift before storage in `ppg_data` |
|---:|---:|---:|
| 0 | 15 | 3 |
| 1 | 16 | 2 |
| 2 | 17 | 1 |
| 3 | 18 | 0 |

Sources:

- `Core/Src/MAX30101.c:39-47`
- `Core/Src/MAX30101.c:79-95`
- `Core/Src/MAX30101.c:577-596`
- `Core/Src/ble_comm.c:92-101`
- `Core/Inc/MAX30101.h:82-86`

## 7. IMU Decode

Confirmed:

- IMU source sensor is LSM9DS1.
- SPI burst read begins at `OUT_X_L_G`; output registers are little-endian.
- `imu_data[0..5]` maps to `Gx, Gy, Gz, Ax, Ay, Az`.
- Gyro scaling: `dps = raw * mdps_per_lsb / 1000`.
- Accel scaling: `g = raw * mg_per_lsb / 1000`.

Accel ranges:

| Control code | Range | Scale |
|---:|---|---:|
| `0x01` | +/-2 g | 0.061 mg/LSB |
| `0x02` | +/-4 g | 0.122 mg/LSB |
| `0x03` | +/-8 g | 0.244 mg/LSB |
| `0x04` | +/-16 g | 0.732 mg/LSB |

Gyro ranges:

| Control code | Range | Scale |
|---:|---|---:|
| `0x01` | +/-245 dps | 8.75 mdps/LSB |
| `0x02` | +/-500 dps | 17.50 mdps/LSB |
| `0x03` | +/-2000 dps | 70.0 mdps/LSB |

Sources:

- `Core/Inc/LSM9DS1.h:72-103`
- `Core/Src/LSM9DS1.c:137-140`
- `Core/Src/LSM9DS1.c:212-217`
- `Core/Src/LSM9DS1.c:473-590`
- `Sensorlist/LSM9DS1.md:149-159`

## 8. Control Command Format

The firmware-supported sensor parameter frame is 13 bytes:

```text
0..1   header: 0xAB 0xCD
2      PPG mode
3      PPG multi sub-mode
4      Green LED level
5      Red LED level
6      IR LED level
7      PPG ADC range
8      PPG pulse width
9      Gyro range
10     Accel range
11..12 tail: 0xEF 0xFA
```

There is no checksum field in this command frame in the checked firmware. The firmware validates field ranges and discards invalid frames.

Parameter ranges:

| Field | Valid values | Meaning / mapping | Source |
|---|---|---|---|
| PPG mode | `0x01..0x03` | `0x01=MultiLED`, `0x02=HR`, `0x03=SpO2` | `README.md:222-224`, `Core/Src/main.c:470-477` |
| Multi sub-mode | `0x01..0x05` | `0x01=G-R-IR`, `0x02=G`, `0x03=R`, `0x04=IR`, `0x05=R-IR`; if mode is not MultiLED then must be `0x01` | `README.md:223-234`, `Core/Src/MAX30101.c:312-382`, `Core/Src/main.c:498-501` |
| LED levels | `0x00..0x09` each | Linear map to MAX30101 current register `0x00..0xFF`, about `0.2 mA/LSB` | `Core/Src/main.c:225-238`, `Core/Src/MAX30101.c:625` |
| PPG ADC range | `0x01..0x04` | Converted to MAX30101 `RGE` code by `value - 1`; exact nA table not enumerated in checked source except default `0x03 = 8192 nA` | `Core/Src/main.c:380`, `Core/Inc/MAX30101.h:82-83` |
| PPG pulse width | `0x01..0x04` | Converted to `LED_PW` code by `value - 1`; controls valid bits and SR/SMP_AVE combo | `Core/Src/main.c:267-345`, `Core/Src/main.c:381` |
| Gyro range | `0x01..0x03` | 245/500/2000 dps | `Core/Src/main.c:409-418` |
| Accel range | `0x01..0x04` | 2/4/8/16 g | `Core/Src/main.c:424-436` |

Receive/apply flow:

- UART IDLE + DMA receives host bytes: `Core/Src/ble.c:307-327`, `Core/Src/ble.c:389-454`.
- Main loop fetches received bytes and queues validated sensor parameters: `Core/Src/main.c:1044-1055`.
- Phase 1 applies PPG parameters; Phase 2 applies IMU parameters and starts a 100-cycle send hold window: `Core/Src/main.c:1164-1195`.

## 9. UD Decode Status

The requested PC-side formula is:

```text
UD = (Uh - Uc) / (k - Uc)
```

Firmware source checked in this analysis does not define the PC-facing names `Uh`, `Uc`, `UD`, `UD1`, or `UD2`. It transmits four ADC channels with `early_code` and `late_code`.

User confirmation on 2026-05-10 defines the mapping required for Python decoding:

- `early_code` is `Uc`.
- `late_code` is `Uh`.
- Frame ADC channel order maps directly to experiment channels `1..4`.
- `UD1` uses channel 2: `UD1 = (Uh2 - Uc2) / (k - Uc2)`.
- `UD2` uses channel 3: `UD2 = (Uh3 - Uc3) / (k - Uc3)`.
- If `abs(k - Uc)` is near zero, the decoder must not crash; it should return `NaN` and record a warning.

## 10. Open Questions

| ID | Question | Blocks parser / decoder / commands? | Handling |
|---|---|---|---|
| Q1 | Is there a protocol version number outside the frame, or should metadata record `null`? | No | Record `null` until firmware defines one. |
| Q2 | Are there later calibration constants for AD4007 or PPG that should be applied in post-processing? | No for initial decoder | Record raw/voltage formula and leave calibration metadata empty unless later provided. |

No blocking questions remain for implementing the real parser, decoder, or control command encoder described in this document.

## 11. Decision

The parser prerequisites are confirmed: fixed length, header, tail, byte order, field offsets, and XOR checksum are present in firmware.

The decoder prerequisites are now confirmed by firmware source plus the 2026-05-10 user confirmations for Uc/Uh mapping, AD4007 voltage conversion, PPG raw-count handling, and UD channel sources.

The command encoder prerequisites are confirmed: 13-byte command frame, parameter ranges, no checksum, and no ACK/NACK response. Python implementation may proceed, while metadata should record `protocol_version = null` because no firmware protocol version field was found.
