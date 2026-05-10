from __future__ import annotations

import time

from pydisplay.io.port_discovery import list_serial_ports
from pydisplay.io.serial_manager import SerialManager, SerialState
from pydisplay.io.serial_reader import SerialReader
from pydisplay.io.serial_writer import SerialWriter
from pydisplay.protocol.models import ControlMetadata


class FakePort:
    device = "COM7"
    description = "HJ380 Bluetooth Serial Port"
    hwid = "BTHENUM"
    manufacturer = "TestVendor"
    serial_number = "ABC123"


class FakeSerial:
    def __init__(self, *, port: str = "COM7", baudrate: int = 460800, chunks: list[bytes] | None = None) -> None:
        self.port = port
        self.baudrate = baudrate
        self.is_open = True
        self._chunks = chunks or []
        self.writes: list[bytes] = []
        self.closed = False

    @property
    def in_waiting(self) -> int:
        return len(self._chunks[0]) if self._chunks else 0

    def read(self, size: int) -> bytes:
        if not self._chunks:
            return b""
        chunk = self._chunks.pop(0)
        return chunk[:size]

    def write(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True
        self.is_open = False


def test_list_serial_ports_maps_pyserial_fields() -> None:
    ports = list_serial_ports(comports=lambda: [FakePort()])

    assert len(ports) == 1
    assert ports[0].device == "COM7"
    assert "HJ380" in ports[0].display_name
    assert ports[0].serial_number == "ABC123"


def test_serial_manager_open_close_with_injected_serial_factory() -> None:
    created: list[FakeSerial] = []

    def factory(**kwargs):
        serial_obj = FakeSerial(port=kwargs["port"], baudrate=kwargs["baudrate"])
        created.append(serial_obj)
        return serial_obj

    manager = SerialManager(serial_factory=factory)

    manager.open("COM7", 460800, start_reader=False)
    assert manager.state == SerialState.CONNECTED
    assert manager.is_connected()

    manager.close()
    assert manager.state == SerialState.DISCONNECTED
    assert created[0].closed is True


def test_serial_manager_can_start_and_pause_receiving() -> None:
    created: list[FakeSerial] = []

    def factory(**kwargs):
        serial_obj = FakeSerial(port=kwargs["port"], baudrate=kwargs["baudrate"])
        created.append(serial_obj)
        return serial_obj

    manager = SerialManager(serial_factory=factory)

    manager.open("COM7", 460800, start_reader=False)
    assert manager.status.receive_paused is True

    manager.start_receiving()
    assert manager.reader is not None
    assert manager.reader.is_alive() is True
    assert manager.status.receive_paused is False

    manager.pause_receiving()
    assert manager.reader.is_paused is True
    assert manager.status.receive_paused is True

    manager.start_receiving()
    assert manager.reader.is_paused is False
    assert manager.status.receive_paused is False

    manager.close()


def test_serial_reader_read_once_emits_raw_chunk() -> None:
    chunks: list[bytes] = []
    reader = SerialReader(FakeSerial(chunks=[b"abc"]), port="COM7", on_chunk=lambda chunk: chunks.append(chunk.data))

    chunk = reader.read_once(timestamp_ns=123)

    assert chunk is not None
    assert chunk.timestamp_ns == 123
    assert chunk.data == b"abc"
    assert chunk.port == "COM7"
    assert chunks == [b"abc"]


def test_serial_reader_pause_resume_stops_background_reads() -> None:
    serial_obj = FakeSerial(chunks=[b"first", b"second"])
    seen: list[bytes] = []

    def on_chunk(chunk) -> None:
        seen.append(chunk.data)
        if len(seen) == 1:
            reader.pause()

    reader = SerialReader(serial_obj, port="COM7", on_chunk=on_chunk, poll_interval_s=0.001)

    reader.start()
    time.sleep(0.02)
    assert seen == [b"first"]
    assert reader.is_paused is True

    reader.resume()
    time.sleep(0.02)
    reader.stop()

    assert seen == [b"first", b"second"]
    assert reader.is_alive() is False


def test_serial_writer_rejects_disconnected_port() -> None:
    serial_obj = FakeSerial()
    serial_obj.is_open = False
    writer = SerialWriter(serial_obj)

    result = writer.write(b"abc")

    assert result.success is False
    assert result.bytes_written == 0
    assert "not connected" in result.error_message.lower()


def test_serial_writer_encodes_control_command_before_write() -> None:
    serial_obj = FakeSerial()
    writer = SerialWriter(serial_obj)

    result = writer.write_control(
        ControlMetadata(
            ppg_mode=0x01,
            ppg_multi_submode=0x01,
            led_green=1,
            led_red=2,
            led_ir=3,
            ppg_adc_range=0x04,
            ppg_pulse_width=0x02,
            gyro_range=0x03,
            accel_range=0x04,
        )
    )

    assert result.success is True
    assert serial_obj.writes == [b"\xAB\xCD\x01\x01\x01\x02\x03\x04\x02\x03\x04\xEF\xFA"]


def test_serial_reader_thread_can_stop_without_hanging() -> None:
    serial_obj = FakeSerial(chunks=[b"abc"])
    seen: list[bytes] = []
    reader = SerialReader(serial_obj, port="COM7", on_chunk=lambda chunk: seen.append(chunk.data), poll_interval_s=0.001)

    reader.start()
    time.sleep(0.01)
    reader.stop()

    assert seen == [b"abc"]
    assert reader.is_alive() is False
