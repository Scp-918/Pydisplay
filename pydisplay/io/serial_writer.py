"""串口写入模块。

SerialWriter 是一个很薄的保护层：
1. 写入前确认串口已打开；
2. 用锁保护多线程写；
3. 捕获异常并返回 WriteResult；
4. 控制命令必须先经过 protocol.commands 编码。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import threading

from pydisplay.protocol.commands import build_control_command
from pydisplay.protocol.models import ControlMetadata


LOGGER = logging.getLogger(__name__)


class SerialErrorKind(Enum):
    PORT_NOT_FOUND = "port_not_found"
    PORT_BUSY = "port_busy"
    PERMISSION_DENIED = "permission_denied"
    DEVICE_REMOVED = "device_removed"
    BLUETOOTH_DISCONNECTED = "bluetooth_disconnected"
    READ_TIMEOUT = "read_timeout"
    WRITE_FAILED = "write_failed"
    NOT_CONNECTED = "not_connected"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class WriteResult:
    success: bool
    bytes_written: int = 0
    error_message: str = ""
    error_kind: SerialErrorKind | None = None


class SerialWriter:
    """线程安全的串口写入包装器。"""

    def __init__(self, serial_obj: object | None) -> None:
        self.serial_obj = serial_obj
        self._lock = threading.Lock()
        self.write_error_count = 0

    def write(self, data: bytes, *, flush: bool = True) -> WriteResult:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if self.serial_obj is None or not bool(getattr(self.serial_obj, "is_open", False)):
            return WriteResult(False, 0, "serial port is not connected", SerialErrorKind.NOT_CONNECTED)

        try:
            with self._lock:
                written = int(self.serial_obj.write(bytes(data)))
                if flush and hasattr(self.serial_obj, "flush"):
                    self.serial_obj.flush()
            return WriteResult(True, written)
        except Exception as exc:
            self.write_error_count += 1
            LOGGER.exception("Serial write failed")
            return WriteResult(False, 0, str(exc), _classify_write_exception(exc))

    def write_control(self, metadata: ControlMetadata) -> WriteResult:
        # 这里强制经过 build_control_command，避免 GUI 层直接拼 bytes。
        command = build_control_command(metadata)
        return self.write(command.data)


def _classify_write_exception(exc: Exception) -> SerialErrorKind:
    if isinstance(exc, PermissionError):
        return SerialErrorKind.PERMISSION_DENIED
    if isinstance(exc, TimeoutError):
        return SerialErrorKind.READ_TIMEOUT
    return SerialErrorKind.WRITE_FAILED
