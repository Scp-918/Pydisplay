"""Serial and BLE I/O helpers."""

from .port_discovery import PortInfo, list_serial_ports
from .serial_manager import SerialManager, SerialState
from .serial_reader import RawChunk, SerialReader
from .serial_writer import SerialWriter, WriteResult

__all__ = [
    "PortInfo",
    "RawChunk",
    "SerialManager",
    "SerialReader",
    "SerialState",
    "SerialWriter",
    "WriteResult",
    "list_serial_ports",
]
