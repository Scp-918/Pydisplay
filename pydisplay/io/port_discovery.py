"""Serial port discovery."""

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
    """Return available serial ports without requiring hardware in tests."""

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
