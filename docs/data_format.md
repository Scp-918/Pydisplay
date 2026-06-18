# Pydisplay Data Format

## raw_frames.bin

All integer fields are little-endian.

File header, 32 bytes:

| Field | Type | Value |
|---|---|---|
| magic | 9 bytes | `PYDISPRAW` |
| format_version | uint16 | `1` |
| created_unix_ns | uint64 | Unix timestamp in ns |
| header_length | uint32 | `32` |
| reserved | 9 bytes | zero-filled |

Record header:

| Field | Type | Description |
|---|---|---|
| record_type | uint8 | `1=raw_serial_chunk`, `2=valid_raw_frame`, `3=bad_frame_fragment` |
| timestamp_ns | uint64 | PC timestamp in ns |
| payload_length | uint32 | payload bytes |
| payload | bytes | raw bytes |

Normal GUI raw-bin replay first reads `raw_serial_chunk` records, extracts valid firmware frames with the real parser, then replays those complete raw frames through the parser/decoder path on a reconstructed 100 Hz frame clock. This is necessary because serial-read chunk timestamps are not sample timestamps: a chunk can contain only part of a frame or multiple frames. The frame clock uses `frame_seq` deltas, so confirmed sequence gaps leave corresponding time gaps. The original chunk-timestamp mode remains available in code for diagnostics; `valid_raw_frame` records are used as a fallback when no parseable raw chunks exist.

Replay completion is based on the number of records read from the file. The format intentionally does not require an end marker, so a normal recording pause/resume cycle does not inject artificial records that would later affect replay.

## decoded.csv

Fields:

```text
frame_seq,absolute_seq_u64,segment_id,sample_seq,
adc_ch1_slot0..adc_ch1_slot5,
adc_ch2_slot0..adc_ch2_slot5,
adc_ch3_slot0..adc_ch3_slot5,
adc_ch4_slot0..adc_ch4_slot5,
parser_valid
```

CSV uses UTF-8 and standard comma-separated rows. ADC slot values are signed AD4007 raw codes decoded by firmware and transmitted as int24 little-endian values. The debug UI and CSV do not convert these values to voltage.

`frame_seq` is the firmware uint16 source frame sequence from bytes 96..97 of the 99-byte data frame. `absolute_seq_u64` is the monotonic source sequence used for post-processing interpolation; the first sequenced frame is 0. `segment_id` increments when the sequence delta indicates reset, severe reorder, or device restart.

`decoded.csv` intentionally does not record `relative_time_s`, `timestamp_pc_ns`, `seq_gap`, `lost_before`, or `source`. Timing for decoded CSV replay is synthesized from row order at 100 Hz. Raw-bin replay should be used when the original capture rhythm is important. Loss and duplicate diagnostics remain visible in the health panel during live/raw replay and can be recomputed from `frame_seq`/`absolute_seq_u64` during post-processing.

Protocol upgrade note: raw replay now expects new 99-byte debugADC firmware frames when replaying `valid_raw_frame` data through the parser. Older raw captures containing legacy 49-byte or 51-byte frames are not guaranteed to parse after this protocol upgrade.

## metadata.json

`metadata.json` records software version, firmware repo/branch/commit, serial settings, Bluetooth modules, debugADC decode mode, control parameters, protocol layout, CSV field descriptions, and raw bin format version.
