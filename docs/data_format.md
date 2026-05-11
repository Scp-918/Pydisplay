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

## decoded.csv

Fields:

```text
relative_time_s,timestamp_pc_ns,frame_seq,absolute_seq_u64,seq_gap,lost_before,segment_id,sample_seq,PPG_G,PPG_R,PPG_IR,ACC_X,ACC_Y,ACC_Z,GYRO_X,GYRO_Y,GYRO_Z,Uh1,Uh2,Uh3,Uh4,Uc1,Uc2,Uc3,Uc4,UD1,UD2,parser_valid,source
```

CSV uses UTF-8 and standard comma-separated rows. PPG values are firmware raw counts. ACC is in g, GYRO is in dps, and Uh/Uc are in volts using `volts = signed_int24 * (4.096 / 131072.0)`.

`frame_seq` is the firmware uint16 source frame sequence from bytes 48..49 of the 51-byte data frame. `absolute_seq_u64` is the monotonic source sequence used for post-processing interpolation; the first sequenced frame is 0. `seq_gap` is the uint16 modular delta from the previous firmware sequence and is 0 for the first frame. `lost_before` is the estimated number of missing firmware frames immediately before this row. `segment_id` increments when the sequence delta indicates reset, severe reorder, or device restart.

Protocol upgrade note: raw replay now expects new 51-byte firmware frames when replaying `valid_raw_frame` data through the parser. Older raw captures containing only legacy 49-byte frames are not guaranteed to parse after this protocol upgrade.

## metadata.json

`metadata.json` records software version, firmware repo/branch/commit, serial settings, Bluetooth modules, `k`, UD formula, control parameters, protocol layout, CSV field descriptions, and raw bin format version.
