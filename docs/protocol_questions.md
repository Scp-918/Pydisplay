# Protocol Questions

## Status

The blocking protocol questions from the initial analysis are resolved as of 2026-05-10 based on the user's project confirmation, which was also added to `AGENTS.md`.

## Resolved Confirmations

- `adc_data[ch].early_code` maps to `Uc`.
- `adc_data[ch].late_code` maps to `Uh`.
- The 4 ADC channels map in transmitted frame order to experiment channels `1..4`.
- `UD1` uses channel 2: `UD1 = (Uh2 - Uc2) / (k - Uc2)`.
- `UD2` uses channel 3: `UD2 = (Uh3 - Uc3) / (k - Uc3)`.
- AD4007 raw code to voltage uses `VREF = 4.096 V`, no external offset, and the 17-bit full-scale denominator:

```text
temp32 = data[0] + data[1] * 256 + data[2] * 65536
if temp32 >= 8388608:
    temp32 -= 16777216
volts = temp32 * (4.096 / 131072.0)
```

- PPG values should be recorded as firmware output raw counts only.
- The control frame is designed with no ACK/NACK response.

## Remaining Non-Blocking Items

- No firmware protocol version field was found. Metadata should record `protocol_version = null`.
- No calibration table for AD4007 or PPG post-processing was provided. The initial decoder should use the confirmed raw-count and voltage formulas only.

## Implementation Decision

The real parser, decoder, and command encoder may proceed using `docs/protocol_analysis.md` as the source of truth. No simulated protocol constants should be introduced into `pydisplay.protocol`.
