---
name: pydisplay-recorder-replay
description: Use this skill when implementing Pydisplay raw_frames.bin recording, decoded.csv recording, metadata.json generation, recorder worker thread, replay worker, raw replay, CSV replay, or recording format tests.
---

# Pydisplay Recorder and Replay Skill

## Purpose

Use this skill for:

- data recording;
- raw frame binary format;
- decoded CSV format;
- metadata JSON;
- recorder thread;
- replay thread;
- raw file replay;
- decoded CSV replay;
- no-hardware testing.

## Required Output Files

Every recording session must generate:

```text
raw_frames.bin
decoded.csv
metadata.json
```

Recommended directory structure:

```text
recordings/
  YYYYMMDD_HHMMSS_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

## Recorder Thread Rule

The GUI thread must not write recording files.

Recorder must run in a worker thread or equivalent non-GUI execution context.

Data enters recorder through a queue.

## Recording Frequency

Record all decoded samples at the full target rate:

```text
100 Hz
```

Plot pause must not stop recording.

Plot visibility must not affect recording.

## Forbidden Patterns

Do not use:

```text
pandas append per frame
DataFrame rebuild per frame
to_csv per frame
flush per frame
GUI-thread file writing
unbounded recording queue without warning
```

## Recommended Writing Strategy

Use:

* `csv.writer`;
* buffered binary file writes;
* batch writes;
* periodic flush;
* final flush on stop;
* queue length monitoring;
* explicit dropped sample statistics if dropping is ever necessary.

## raw_frames.bin Format

Recommended format:

```text
File header:
  magic: 8 bytes, "PYDISP01"
  version: uint16
  reserved or header length if needed

Repeated record:
  host_timestamp_ns: uint64
  frame_len: uint32
  frame_bytes: uint8[frame_len]
```

Rules:

* `frame_bytes` must include frame header and frame tail;
* raw frames must be enough to replay parser/decoder behavior;
* use little-endian unless otherwise documented for the file format;
* document this format in `docs/architecture.md` or `docs/user_manual.md`.

## decoded.csv Format

The CSV is for Excel / Origin / MATLAB.

Recommended columns:

```text
sample_index
frame_seq
host_time_ns
relative_time_s
device_time
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
k_value
```

If the confirmed protocol contains more fields, append them without breaking these core fields.

If a field is unavailable, leave it empty or use a documented placeholder.

## metadata.json Requirements

`metadata.json` must include at least:

```json
{
  "software": {
    "name": "Pydisplay",
    "version": "0.1.0",
    "python_version": "",
    "platform": ""
  },
  "firmware": {
    "repository": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
    "branch": "Single",
    "commit": "",
    "commit_available": false
  },
  "protocol": {
    "version": "",
    "frame_header": "AA BB",
    "frame_tail": "CC",
    "frame_length": null,
    "endianness": "",
    "checksum": "",
    "source_files": []
  },
  "serial": {
    "port": "",
    "baudrate": 0,
    "bytesize": "",
    "parity": "",
    "stopbits": "",
    "timeout": ""
  },
  "control_settings": {
    "ppg_mode": "",
    "led_brightness": "",
    "ppg_range": "",
    "pulse_width": "",
    "imu_range": ""
  },
  "decode_settings": {
    "k_value": 0.0,
    "ud_formula": "UD = (Uh - Uc) / (k - Uc)"
  },
  "recording": {
    "recording_name": "",
    "recording_dir": "",
    "start_time_local": "",
    "end_time_local": "",
    "start_time_utc": "",
    "end_time_utc": "",
    "sample_rate_target_hz": 100,
    "raw_file": "raw_frames.bin",
    "decoded_file": "decoded.csv"
  },
  "csv_fields": {},
  "runtime_stats": {
    "total_frames": 0,
    "valid_frames": 0,
    "bad_frames": 0,
    "bad_frame_ratio": 0.0,
    "resync_count": 0,
    "dropped_record_samples": 0
  }
}
```

Update `end_time_*` and final `runtime_stats` when recording stops.

## Firmware Commit

If firmware repository exists locally and `git` can read it, include commit hash.

If unavailable:

```json
"commit_available": false
```

Do not fail recording just because firmware commit is unavailable.

## Replay Requirements

Support replay from:

1. `raw_frames.bin`;
2. `decoded.csv`.

### raw replay

Flow:

```text
raw_frames.bin
  -> RawFrameReader
  -> Decoder
  -> DecodedSample
  -> PlotBuffer / GUI
```

If the file contains raw frames, direct decode is acceptable.

If later raw stream chunks are added, stream replay must use parser.

### decoded.csv replay

Flow:

```text
decoded.csv
  -> DecodedCsvReader
  -> DecodedSample
  -> PlotBuffer / GUI
```

## Replay Timing

Default replay rate:

```text
100 Hz
```

Support:

* pause;
* continue;
* stop;
* 0.25x;
* 0.5x;
* 1x;
* 2x;
* 5x.

Replay worker must not block GUI.

## Replay Health Status

During replay, health panel should show:

* replay mode;
* source file;
* playback speed;
* current sample index;
* approximate replay FPS/sample rate;
* pause/running state.

## Error Handling

Recorder must handle:

* path does not exist;
* no write permission;
* file already open;
* disk full;
* queue overflow;
* stop during write;
* metadata write failure.

Replay must handle:

* file not found;
* invalid raw magic;
* unsupported raw version;
* truncated raw record;
* CSV missing required columns;
* numeric conversion failure;
* pause/stop during playback.

## Tests

Required tests:

* raw file write/read round trip;
* decoded CSV write/read round trip;
* metadata includes required keys;
* recorder start/stop creates three files;
* replay raw emits expected samples;
* replay csv emits expected samples;
* invalid raw file fails clearly;
* missing CSV columns fail clearly.

## Completion Criteria

Before committing:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_recorder.py tests/test_replay.py
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check pydisplay/io
```

Then commit:

```bash
git add .
git commit -m "implement recording and replay workers"
```
