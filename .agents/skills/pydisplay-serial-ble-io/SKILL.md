---
name: pydisplay-serial-ble-io
description: Use this skill when implementing Pydisplay serial port discovery, HJ380 BLE serial connection, SerialReader worker, reconnect logic, serial error handling, serial write commands, or fake serial device support.
---

# Pydisplay Serial BLE IO Skill

## Purpose

Use this skill for serial and BLE-link-facing work:

- list serial ports;
- open serial port;
- close serial port;
- reconnect;
- detect port occupation;
- detect HJ380 unplug;
- detect BLE disconnection;
- read continuous bytes;
- write command bytes;
- expose serial status;
- support test mode with fake device or virtual serial if available.

## Hardware Context

Data path:

```text
STM32G474 -> HJ131 BLE module -> HJ380 BLE module -> PC serial port
```

Python receives data through a serial port exposed by HJ380.

Required GUI features:

* select port;
* select baudrate;
* open;
* close;
* reconnect;
* clear status;
* explicit error message.

## Required Modules

Expected files:

```text
pydisplay/
  io/
    serial_port.py
    serial_reader.py

  simulator/
    fake_device.py
    fake_frames.py
    virtual_serial.py

  gui/widgets/
    serial_panel.py
```

## Threading Rule

The GUI thread must never block on serial IO.

Serial reading must run in:

* a `QThread` worker; or
* a Python thread that communicates with Qt through signal/slot or queue.

The serial worker owns the serial object.

If another module needs to send command bytes, it should send a request to the serial worker or use a thread-safe writer method.

## SerialReader Responsibilities

SerialReader must:

* open port with selected baudrate;
* read bytes continuously;
* emit bytes chunks or parsed samples depending on architecture;
* catch serial exceptions;
* support stop request;
* close port cleanly;
* expose connection state;
* expose bytes/s;
* expose input buffer byte count if available;
* report last exception;
* avoid busy spinning;
* handle zero-byte reads without freezing.

## Recommended Connection States

Use explicit state names:

```text
DISCONNECTED
CONNECTING
CONNECTED
RECONNECTING
DISCONNECTING
ERROR
```

Optional:

```text
PORT_NOT_FOUND
PORT_BUSY
DEVICE_REMOVED
BLE_DISCONNECTED
```

## Error Handling

Handle at least:

* port not found;
* permission denied;
* port occupied;
* open failure;
* read timeout;
* device unplugged;
* BLE disconnect;
* write failure;
* close during read;
* reconnect failure.

GUI must remain responsive in all cases.

## Reconnect Logic

Reconnect should:

1. stop current reader if still alive;
2. close old serial object;
3. wait briefly if needed;
4. rescan ports;
5. reopen configured port if present;
6. update GUI state;
7. report failure clearly.

Do not implement infinite aggressive reconnect loops in GUI thread.

If automatic reconnect is implemented, use bounded retry interval and visible status.

## Serial Write Command Requirements

When GUI sends a control command:

1. validate input in control panel or command builder;
2. build command bytes in `protocol.command`;
3. send through SerialReader/SerialWriter;
4. catch write exception;
5. report success/failure;
6. if ACK is supported, wait asynchronously and show ACK timeout or NACK.

Do not block GUI while waiting for ACK.

## Fake Device and Virtual Serial

Optional test support:

* generate simulated decoded samples for UI;
* generate simulated raw protocol frames only after real protocol is confirmed;
* support virtual serial if practical on Windows;
* if virtual serial is not available, use an in-process fake source or file replay.

Failure of virtual serial setup must not block the main project.

## Health Metrics to Expose

Serial layer should expose:

* bytes per second;
* serial input waiting bytes;
* connection state;
* last successful read time;
* last error;
* reconnect count;
* write command count;
* write error count.

## Tests

Add tests where possible:

* port list function does not crash;
* fake serial source emits bytes;
* serial worker can start/stop with fake backend;
* write failure produces status;
* reconnect path does not deadlock.

Do not require physical HJ380 hardware for automated tests.

## Completion Criteria

Before committing:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check pydisplay/io pydisplay/simulator
```

Then commit:

```bash
git add .
git commit -m "implement serial BLE IO worker and fake source support"
```