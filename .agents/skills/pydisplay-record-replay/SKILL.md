---
name: pydisplay-record-replay
description: Use when implementing or reviewing Pydisplay data recording, raw_frames.bin, decoded.csv, metadata.json, batch file writing, replay from raw or CSV, replay speed control, and non-blocking recorder/replay workers.
---

# Pydisplay Record and Replay Skill

Use this skill when building or modifying recording and replay functionality for the STM32G474 Pydisplay Python GUI.

The highest priorities are data integrity, non-blocking operation, and reproducibility.

## Scope

This skill covers:

- `raw_frames.bin` design.
- `decoded.csv` design.
- `metadata.json` design.
- Batch writing.
- Recorder worker thread.
- Replay worker thread.
- Replay from raw frames.
- Replay from decoded CSV.
- Metadata consistency.
- Recording and replay tests.

This skill does not confirm protocol fields. Use `pydisplay-protocol-audit` first.

## Target files

Recommended files:

    src/pydisplay/io/recorder.py
    src/pydisplay/io/replay.py
    src/pydisplay/core/models.py
    src/pydisplay/core/metrics.py
    src/pydisplay/utils/timebase.py
    src/pydisplay/utils/paths.py
    src/pydisplay/utils/version.py
    docs/data_format.md
    tests/test_recorder.py
    tests/test_replay.py

## Recording requirements

Each recording session must create a separate folder, for example:

    records/
      2026-05-10_实验名/
        raw_frames.bin
        decoded.csv
        metadata.json
        run.log

The GUI must allow user to select recording path and file/session name.

Recording must include:

1. `raw_frames.bin`
   - Original raw frames.
   - PC timestamp.
   - Valid and invalid frames when available.
   - Enough information for protocol debugging.

2. `decoded.csv`
   - Human-readable decoded data.
   - Relative time.
   - Useful for Excel / Origin / MATLAB.

3. `metadata.json`
   - Experiment parameters.
   - Serial settings.
   - Protocol settings.
   - Software version.
   - Firmware repository or commit if available.
   - CSV schema.

## Threading rules

Recorder must run outside GUI thread.

Do not:

- Write files in GUI thread.
- Flush every frame.
- Use pandas append per frame.
- Block serial reader waiting for disk writes.
- Silently drop recorded data.

Do:

- Use queue-based handoff.
- Use buffered binary file writing for raw frames.
- Use `csv.writer` or buffered text writes for CSV.
- Batch writes.
- Flush at controlled intervals or on stop.
- Close files safely.
- Expose queue length and error state to health panel.

## Queue policy

Separate queues are recommended:

- raw frame record queue
- decoded sample record queue

Rules:

1. Recorder queue length must be visible in health panel.
2. If queue grows above threshold, show warning.
3. If recording cannot keep up, show explicit error.
4. Do not discard raw frames without explicit fatal error.
5. Plot data may be dropped under load, but recording data must be preserved.

## `raw_frames.bin` format

Use a documented sequential binary format.

Recommended format:

Header:

    magic: 8 bytes = b"PYDSPRAW"
    version: uint16
    header_len: uint16
    created_unix_ns: uint64
    reserved: bytes

Repeated records:

    pc_timestamp_ns: uint64
    frame_len: uint32
    flags: uint16
    raw_frame_bytes: frame_len bytes

Flags may include:

- bit 0: checksum_ok
- bit 1: decoded_ok
- bit 2: parser_resynced_before_frame
- bit 3: bad_tail
- bit 4: length_error
- bit 5: reserved

If final record count is hard to backfill, store count in metadata instead.

Document exact format in:

    docs/data_format.md

## `decoded.csv` columns

Use stable column names.

Recommended columns:

    pc_time_iso
    pc_time_ns
    t_rel_s
    frame_index
    sample_index
    valid
    checksum_ok
    ppg_g
    ppg_r
    ppg_ir
    acc_x
    acc_y
    acc_z
    gyro_x
    gyro_y
    gyro_z
    uh_1
    uh_2
    uh_3
    uh_4
    uc_1
    uc_2
    uc_3
    uc_4
    ud_1
    ud_2
    k
    parser_state
    error_code

If protocol audit confirms additional fields, add them with clear names and update metadata schema.

If a field is unknown or unavailable, leave it blank rather than inventing values.

## `metadata.json` requirements

Metadata must include at least:

    {
      "serial": {
        "port": "",
        "baudrate": 0
      },
      "experiment": {
        "record_start_time": "",
        "record_end_time": "",
        "operator": "",
        "notes": ""
      },
      "parameters": {
        "k": null,
        "ppg_mode": null,
        "led_brightness": null,
        "ppg_range": null,
        "pulse_width": null,
        "imu_range": null
      },
      "software": {
        "name": "Pydisplay",
        "version": "",
        "python_version": "",
        "pyside6_version": "",
        "pyqtgraph_version": "",
        "platform": ""
      },
      "firmware": {
        "repository": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
        "commit": "",
        "branch": "Single"
      },
      "protocol": {
        "version": "",
        "frame_header": "AA BB",
        "frame_tail": "CC",
        "frame_length": null,
        "endianness": "",
        "checksum": "",
        "source_evidence": []
      },
      "csv_schema": [],
      "recording": {
        "raw_frames_file": "raw_frames.bin",
        "decoded_csv_file": "decoded.csv",
        "sample_rate_target_hz": 100,
        "flush_policy": "batch"
      }
    }

Add actual values where available.

## Recorder lifecycle

Implement explicit lifecycle:

1. `prepare_session`
2. `start`
3. `enqueue_raw_frame`
4. `enqueue_decoded_sample`
5. `stop_requested`
6. `drain_or_flush`
7. `write_final_metadata`
8. `close_files`

If error occurs:

1. Stop accepting new data if necessary.
2. Report error to GUI.
3. Attempt safe file close.
4. Preserve partial files.
5. Write error status to metadata if possible.

## Replay requirements

Support two replay modes:

### Raw replay

Input:

    raw_frames.bin

Flow:

    raw_frames.bin
      -> ReplayWorker
      -> RawFrame
      -> Parser/Decoder if needed
      -> DecodedSample
      -> plot queue
      -> metrics

Raw replay should be useful for debugging parser and decoder.

### CSV replay

Input:

    decoded.csv

Flow:

    decoded.csv
      -> ReplayWorker
      -> DecodedSample
      -> plot queue
      -> metrics

CSV replay should be useful when no hardware is available and the user only wants UI or algorithm debugging.

## Replay timing

Replay should simulate real acquisition:

- Default: 1.0x speed.
- Target rhythm: about 100 Hz when timestamps are unavailable.
- If timestamps are available, use recorded relative time.
- Support:
  - pause
  - continue
  - stop
  - speed up
  - slow down

Avoid blocking GUI during replay.

## Replay controls

GUI should expose:

- 选择 raw_frames.bin
- 选择 decoded.csv
- 开始回放
- 暂停
- 继续
- 停止
- 倍速
- 慢速

Replay and live serial acquisition should not run at the same time unless explicitly designed. If both are requested, show a clear warning.

## Tests

Test recorder with simulated samples:

1. Create temporary recording directory.
2. Write several raw frames.
3. Write several decoded samples.
4. Stop recorder.
5. Check files exist.
6. Check CSV header.
7. Check metadata fields.
8. Check raw file can be read sequentially.

Test replay:

1. Replay a sample raw file.
2. Replay a sample CSV file.
3. Pause and resume.
4. Stop early.
5. Handle malformed file.
6. Handle version mismatch.

Run:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_recorder.py tests/test_replay.py -q

## Manual validation checklist

- [ ] Start recording.
- [ ] Stop recording.
- [ ] raw_frames.bin exists and is non-empty.
- [ ] decoded.csv exists and opens in Excel-compatible form.
- [ ] metadata.json exists and contains serial settings, k, control parameters, software, protocol, start/end times.
- [ ] GUI does not freeze while recording.
- [ ] No per-frame flush.
- [ ] No pandas append per frame.
- [ ] Replay raw works.
- [ ] Replay CSV works.
- [ ] Replay pause/resume works.
- [ ] Replay speed control works.

## Git rule

After recording and replay implementation and tests pass:

    git status
    git add src/pydisplay/io docs/data_format.md tests
    git commit -m "add batch recorder and replay workers"