"""串口与 BLE 透明串口 I/O 子包。

注意：这里处理的是电脑端 HJ380 映射出来的 COM 口。
它不直接访问 STM32，也不直接访问 HJ131。
"""

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
