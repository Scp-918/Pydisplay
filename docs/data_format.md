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

Normal raw-bin replay feeds only `raw_serial_chunk` records back through the parser when they exist. This is the preferred path because raw chunks preserve the original serial stream, including valid frames, invalid bytes, half packets, sticky packets, and the PC timestamps used for replay timing. `valid_raw_frame` and `bad_frame_fragment` are used only as a fallback for older/simpler captures that do not contain raw chunks.

Replay completion is based on the number of records read from the file. The format intentionally does not require an end marker, so a normal recording pause/resume cycle does not inject artificial records that would later affect replay.

## decoded.csv

Fields:

```text
frame_seq,absolute_seq_u64,segment_id,sample_seq,PPG_G,PPG_R,PPG_IR,ACC_X,ACC_Y,ACC_Z,GYRO_X,GYRO_Y,GYRO_Z,Uh1,Uh2,Uh3,Uh4,Uc1,Uc2,Uc3,Uc4,UD1,UD2,parser_valid
```

CSV uses UTF-8 and standard comma-separated rows. PPG values are firmware raw counts. ACC is in g, GYRO is in dps, and Uh/Uc are in volts using `volts = signed_int24 * (4.096 / 131072.0)`.

`frame_seq` is the firmware uint16 source frame sequence from bytes 48..49 of the 51-byte data frame. `absolute_seq_u64` is the monotonic source sequence used for post-processing interpolation; the first sequenced frame is 0. `segment_id` increments when the sequence delta indicates reset, severe reorder, or device restart.

`decoded.csv` intentionally does not record `relative_time_s`, `timestamp_pc_ns`, `seq_gap`, `lost_before`, or `source`. Timing for decoded CSV replay is synthesized from row order at 100 Hz. Raw-bin replay should be used when the original capture rhythm is important. Loss and duplicate diagnostics remain visible in the health panel during live/raw replay and can be recomputed from `frame_seq`/`absolute_seq_u64` during post-processing.

Protocol upgrade note: raw replay now expects new 51-byte firmware frames when replaying `valid_raw_frame` data through the parser. Older raw captures containing only legacy 49-byte frames are not guaranteed to parse after this protocol upgrade.

## metadata.json

`metadata.json` records software version, firmware repo/branch/commit, serial settings, Bluetooth modules, `k`, UD formula, control parameters, protocol layout, CSV field descriptions, and raw bin format version.
