"""串口发现模块。

GUI 点击“刷新串口”时会调用这里。
它只负责列出当前系统中的 COM 口，不打开串口、不读写数据。

测试时可以传入假的 `comports()` 函数，因此不需要真实 HJ380 硬件。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import logging


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PortInfo:
    device: str
    description: str
    hwid: str
    manufacturer: str | None = None
    serial_number: str | None = None

    @property
    def display_name(self) -> str:
        if self.description:
            return f"{self.device} - {self.description}"
        return self.device


def list_serial_ports(comports: Callable[[], Iterable[object]] | None = None) -> list[PortInfo]:
    """返回当前可用串口列表。

    `comports` 参数用于测试注入；正常运行时使用 pyserial 的 list_ports。
    如果 pyserial 不可用或枚举失败，返回空列表并写日志，而不是让 GUI 崩溃。
    """

    provider = comports or _pyserial_comports
    try:
        ports = provider()
    except Exception:
        LOGGER.exception("Failed to list serial ports")
        return []

    return [
        PortInfo(
            device=str(getattr(port, "device", "")),
            description=str(getattr(port, "description", "")),
            hwid=str(getattr(port, "hwid", "")),
            manufacturer=getattr(port, "manufacturer", None),
            serial_number=getattr(port, "serial_number", None),
        )
        for port in ports
    ]


def _pyserial_comports() -> Iterable[object]:
    try:
        from serial.tools import list_ports
    except ImportError:
        LOGGER.warning("pyserial is not available; serial port list is empty")
        return []
    return list_ports.comports()
