---
name: pydisplay-protocol-parser-state-machine
description: Use this skill when implementing or testing the Pydisplay byte-stream parser, frame synchronization, checksum validation, bad-frame statistics, resync behavior, decoder, or control command packing after firmware protocol analysis is complete.
---

# Pydisplay Protocol Parser State Machine Skill

## Purpose

Use this skill to implement:

- byte stream parser;
- frame synchronization;
- bad frame recovery;
- checksum validation;
- raw frame model;
- decoded sample model;
- command frame packing;
- parser unit tests;
- decoder unit tests;
- command builder unit tests.

Only use this skill after `docs/protocol_analysis.md` confirms the protocol.

If `docs/protocol_analysis.md` is missing, incomplete, or says implementation is blocked, stop parser implementation and switch to protocol analysis first.

## Required Files

Expected modules:

```text
pydisplay/
  core/
    models.py
    constants.py
    exceptions.py

  protocol/
    spec.py
    checksum.py
    parser.py
    decoder.py
    command.py
```

Expected tests:

```text
tests/
  test_parser.py
  test_decoder.py
  test_command.py
```

## Core Rule

The parser must process continuous bytes from a serial stream.

It must support:

* partial frames;
* sticky frames;
* garbage bytes before a frame;
* bad frame in the middle of valid frames;
* checksum failure;
* tail mismatch;
* length mismatch;
* recovery after bad data;
* long-running operation without unbounded buffer growth.

Bad frames must be counted, not allowed to destroy the entire stream.

## State Machine Requirements

Implement a clear state machine. Acceptable states include:

```text
FIND_HEADER_1
FIND_HEADER_2
READ_BODY
READ_TAIL
VERIFY_CHECKSUM
EMIT_FRAME
RESYNC
```

If the protocol has a length field, use:

```text
FIND_HEADER
READ_LENGTH
READ_PAYLOAD
READ_CHECKSUM
READ_TAIL
VERIFY
RESYNC
```

## Parser Statistics

Expose parser statistics through a dataclass, for example `ParserStats`.

It must track:

* total input bytes;
* valid frames;
* bad frames;
* bad frame ratio;
* resync count;
* checksum failures;
* tail failures;
* length failures;
* incomplete frame count;
* current parser buffer size;
* last error message;
* last valid frame timestamp if useful.

## Recovery Rules

When a bad frame is detected:

1. increment the correct error counter;
2. increment bad frame count;
3. search the remaining buffer for the next valid header `0xAA 0xBB`;
4. keep possible partial header bytes;
5. do not clear the whole buffer unless it is impossible to retain useful data;
6. protect against unbounded buffer growth.

## Decoder Requirements

The decoder converts `RawFrame` to `DecodedSample`.

It must:

* follow field order from `protocol/spec.py`;
* follow endianness from `protocol/spec.py`;
* apply scaling from `protocol/spec.py`;
* preserve host timestamp;
* preserve firmware sequence number if present;
* preserve device timestamp if present;
* create host sample index if firmware sample number is unavailable;
* compute UD values using the GUI-provided k value:

```text
UD = (Uh - Uc) / (k - Uc)
```

If denominator is near zero:

* do not crash;
* return NaN or a documented sentinel value;
* increment or expose a decode warning if appropriate.

## Command Builder Requirements

Command builder must support:

* PPG mode;
* LED brightness;
* PPG range;
* pulse width;
* IMU range.

Before packing command bytes:

* validate parameter type;
* validate parameter range;
* validate enum value;
* produce a clear error message if invalid.

Do not invent command IDs. Use only values confirmed in `docs/protocol_analysis.md`.

If ACK / NACK exists, expose the command identifier needed to match response frames.

## Tests Required

Parser tests must include:

* one complete frame;
* multiple frames in one bytes chunk;
* one frame split across multiple inputs;
* garbage before header;
* garbage between frames;
* checksum failure;
* tail failure;
* length failure if applicable;
* bad frame followed by good frame;
* empty bytes input;
* random noise followed by good frame;
* parser buffer size remains bounded.

Decoder tests must include:

* known raw frame to decoded fields;
* k value affects UD;
* denominator near zero;
* missing optional sequence/timestamp behavior;
* signed field handling if relevant;
* scaling factors.

Command tests must include:

* valid command packing;
* invalid enum;
* out-of-range brightness;
* invalid pulse width;
* checksum correctness if command uses checksum.

## Source Traceability

Protocol code comments must include source references, for example:

```text
# Field order confirmed from Core/Src/xxx.c function yyy()
```

Do not use vague comments such as:

```text
# guessed from typical STM32 UART frame
```

## Completion Criteria

Before committing:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_parser.py tests/test_decoder.py tests/test_command.py
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check pydisplay/protocol tests/test_parser.py tests/test_decoder.py tests/test_command.py
```

Then commit:

```bash
git add .
git commit -m "implement protocol parser decoder and command builder"
```