---
name: pydisplay-serial-threading
description: Use when implementing or reviewing serial port connection, HJ380 Bluetooth serial reading, reconnect logic, worker threads, queues, Qt signals, and non-blocking concurrency for the Pydisplay PySide6 upper-computer app.
---

# Pydisplay Serial and Threading Skill

Use this skill when building or changing serial I/O, worker threads, queues, parser dispatch, or command sending in the Pydisplay Python GUI.

The priority is GUI stability: the GUI must not freeze when the serial port is missing, occupied, unplugged, disconnected, slow, noisy, or malformed.

## Scope

This skill covers:

- pyserial connection management.
- HJ380 serial reception.
- Open, close, reconnect.
- Port enumeration.
- Serial exceptions.
- Reader worker thread.
- Optional parser worker.
- Thread-safe command sending.
- Queue backpressure and health metrics.
- Integration with PySide6 signal/slot.

This skill does not define the binary protocol. Use `pydisplay-protocol-audit` first for protocol details.

## Target files

Recommended files:

    src/pydisplay/io/serial_reader.py
    src/pydisplay/io/serial_writer.py
    src/pydisplay/core/metrics.py
    src/pydisplay/core/models.py
    src/pydisplay/protocol/frame_parser.py
    src/pydisplay/protocol/decoder.py
    src/pydisplay/gui/widgets_serial.py
    src/pydisplay/gui/widgets_health.py
    tests/test_serial_reader.py

## Required architecture

Use this flow:

    GUI main thread
      -> Serial control signals
      -> SerialReader worker thread
      -> byte_queue or parser call
      -> Parser / Decoder
      -> decoded queue
      -> GUI plot queue
      -> Recorder queue
      -> Metrics

The GUI main thread may:

- Request connect.
- Request disconnect.
- Request reconnect.
- Send command requests through a thread-safe method.
- Read lightweight status snapshots.
- Update widgets on timers.

The GUI main thread must not:

- Perform blocking serial reads.
- Loop over raw bytes for long periods.
- Write recording files.
- Sleep to wait for serial data.
- Block waiting for thread shutdown without timeout.

## SerialReader responsibilities

Implement a SerialReader worker that supports:

1. Select serial port.
2. Select baudrate.
3. Open port.
4. Close port.
5. Reconnect.
6. Read bytes in a loop using timeout.
7. Detect and report:
   - port not found
   - port occupied
   - permission denied
   - device unplugged
   - Bluetooth disconnect
   - read timeout
   - write failure
8. Expose health metrics:
   - connection state
   - bytes/s
   - serial in_waiting
   - last data time
   - reconnect count
   - last error message
9. Clean shutdown.

Use a small serial timeout, for example 20–100 ms. Do not use infinite blocking reads.

## Connection states

Represent connection state explicitly, for example:

- `DISCONNECTED`
- `CONNECTING`
- `CONNECTED`
- `RECONNECTING`
- `ERROR`
- `STOPPING`

Display states in Chinese in the GUI:

- 未连接
- 正在连接
- 已连接
- 正在重连
- 错误
- 正在停止

## Error handling rules

Catch serial exceptions and convert them to structured status events.

Do not allow unhandled exceptions to terminate the application.

When an exception occurs:

1. Update connection state.
2. Store last error message.
3. Emit a GUI-safe status signal.
4. Stop reading from invalid port.
5. Allow user to reconnect.

For disconnect or device removal:

- Do not spin in a tight loop.
- Use backoff for reconnect attempts if auto-reconnect is implemented.
- Do not block GUI during reconnect.

## Command sending

Command sending must be thread-safe.

Rules:

1. Validate GUI inputs before building command.
2. Use `protocol/commands.py` to build binary command.
3. Do not build command bytes in GUI widget code.
4. Send through the same serial object only under a lock or inside the serial worker thread.
5. Report send result:
   - success
   - port not connected
   - write timeout
   - serial exception
   - invalid parameter
6. If ACK/NACK exists in firmware, implement it only after protocol confirmation.

## Queue rules

Use Queue or Qt signals carefully.

Recommended:

- Raw bytes queue for parser if parser is separate.
- Decoded sample queue for GUI and recorder.
- Recorder queue independent from plot queue.
- Metrics snapshot object for health panel.

Rules:

1. Queue sizes should be bounded or monitored.
2. If queue grows above threshold, show warning.
3. Never silently drop raw data intended for recording.
4. Plot queue may drop old visual samples only if recorder has already received full data.
5. Recorder queue must preserve all samples unless an explicit fatal recording error is shown.

## Parser placement

Acceptable options:

### Option A: SerialReader calls Parser directly

Use if parsing is lightweight and 100 Hz.

    SerialReader thread
      -> parser.feed(bytes)
      -> decoder
      -> queues

### Option B: Separate ParserWorker

Use if serial bursts or parsing becomes heavy.

    SerialReader thread
      -> byte_queue
      -> ParserWorker thread
      -> decoder
      -> queues

Do not parse in GUI thread.

## Health metrics

Update metrics continuously but display them at 1–5 Hz.

Track:

- bytes/s
- valid frame rate
- bad frame rate
- bad frame ratio
- resync count
- serial buffer bytes
- parser buffer bytes
- decoded queue length
- recorder queue length
- plot queue length
- connection state
- recording state
- last error

Do not update QLabel on every frame.

## Shutdown requirements

When the app exits:

1. Disable GUI buttons as needed.
2. Request SerialReader stop.
3. Close serial port.
4. Stop parser worker if present.
5. Stop recorder worker after queues are drained or safely flushed.
6. Join worker threads with timeout.
7. Log any worker that did not stop cleanly.
8. Do not leave zombie threads.

## Testing strategy

When hardware is unavailable:

1. Use a fake serial object.
2. Simulate bytes arriving in chunks.
3. Simulate timeout.
4. Simulate disconnect exception.
5. Simulate occupied port.
6. Simulate write failure.

Tests should verify:

- GUI thread is not used for blocking read.
- Reader can start and stop.
- Exceptions produce status events.
- Reconnect can be requested after error.
- Command send fails gracefully when disconnected.
- Queues receive expected bytes or frames.

Run:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_serial_reader.py -q

## Implementation checklist

Before marking the serial layer complete, confirm:

- [ ] Port enumeration works.
- [ ] Baudrate selection works.
- [ ] Open works.
- [ ] Close works.
- [ ] Reconnect works.
- [ ] Occupied port error is shown.
- [ ] Missing port error is shown.
- [ ] Device unplug does not freeze GUI.
- [ ] Bluetooth disconnect does not freeze GUI.
- [ ] Command write is thread-safe.
- [ ] Metrics are updated.
- [ ] Shutdown leaves no running worker thread.
- [ ] Tests pass.

## Git rule

After serial/threading implementation and tests pass:

    git status
    git add src/pydisplay/io src/pydisplay/core src/pydisplay/gui tests
    git commit -m "add serial worker and threading-safe connection flow"