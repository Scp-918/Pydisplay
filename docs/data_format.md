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
relative_time_s,timestamp_pc_ns,frame_seq,sample_seq,PPG_G,PPG_R,PPG_IR,ACC_X,ACC_Y,ACC_Z,GYRO_X,GYRO_Y,GYRO_Z,Uh1,Uh2,Uh3,Uh4,Uc1,Uc2,Uc3,Uc4,UD1,UD2,parser_valid,source
```

CSV uses UTF-8 and standard comma-separated rows. PPG values are firmware raw counts. ACC is in g, GYRO is in dps, and Uh/Uc are in volts using `volts = signed_int24 * (4.096 / 131072.0)`.

## metadata.json

`metadata.json` records software version, firmware repo/branch/commit, serial settings, Bluetooth modules, `k`, UD formula, control parameters, protocol layout, CSV field descriptions, and raw bin format version.
