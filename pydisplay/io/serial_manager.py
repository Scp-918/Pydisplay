"""串口生命周期管理。

SerialManager 统一负责：
- 打开串口；
- 关闭串口；
- 重连；
- 创建 SerialReader 和 SerialWriter；
- 保存当前状态；
- 把错误通过回调交给 GUI/health monitor。

GUI 不直接持有 pyserial.Serial 对象，避免界面代码和底层 I/O 耦合。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import logging
import time

from .port_discovery import PortInfo, list_serial_ports
from .serial_reader import RawChunk, SerialReader
from .serial_writer import SerialErrorKind, SerialWriter, WriteResult
from pydisplay.protocol.models import ControlMetadata


LOGGER = logging.getLogger(__name__)


class SerialState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass(slots=True)
class SerialStatus:
    state: SerialState = SerialState.DISCONNECTED
    port: str | None = None
    baudrate: int | None = None
    last_error: str | None = None
    error_kind: SerialErrorKind | None = None


SerialFactory = Callable[..., object]


class SerialManager:
    """管理一个串口连接及其 reader/writer。"""

    def __init__(
        self,
        *,
        serial_factory: SerialFactory | None = None,
        on_chunk: Callable[[RawChunk], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_state_changed: Callable[[SerialStatus], None] | None = None,
    ) -> None:
        self._serial_factory = serial_factory
        self._on_chunk = on_chunk or (lambda chunk: None)
        self._on_error = on_error
        self._on_state_changed = on_state_changed
        self.status = SerialStatus()
        self.serial_obj: object | None = None
        self.reader: SerialReader | None = None
        self.writer = SerialWriter(None)

    @property
    def state(self) -> SerialState:
        return self.status.state

    def list_ports(self) -> list[PortInfo]:
        return list_serial_ports()

    def open(self, port: str, baudrate: int, *, start_reader: bool = True) -> None:
        """打开串口。

        `start_reader=False` 主要用于无硬件测试，只验证 open/close 状态。
        """
        self.close()
        self._set_state(SerialState.CONNECTING, port=port, baudrate=baudrate, error=None)
        try:
            factory = self._serial_factory or _default_serial_factory()
            self.serial_obj = factory(port=port, baudrate=baudrate, timeout=0.05, write_timeout=0.2)
            self.writer = SerialWriter(self.serial_obj)
            self.reader = SerialReader(
                self.serial_obj,
                port=port,
                on_chunk=self._on_chunk,
                on_error=self._handle_reader_error,
            )
            if start_reader:
                self.reader.start()
            self._set_state(SerialState.CONNECTED, port=port, baudrate=baudrate, error=None)
            LOGGER.info("Serial connected: %s @ %s", port, baudrate)
        except Exception as exc:
            self.serial_obj = None
            self.reader = None
            self.writer = SerialWriter(None)
            LOGGER.exception("Serial open failed: %s @ %s", port, baudrate)
            self._set_state(SerialState.ERROR, port=port, baudrate=baudrate, error=str(exc), kind=_classify_open_exception(exc))
            if self._on_error:
                self._on_error(exc)

    def close(self) -> None:
        if self.status.state == SerialState.DISCONNECTED and self.serial_obj is None:
            return
        port = self.status.port
        baudrate = self.status.baudrate
        self._set_state(SerialState.DISCONNECTING, port=port, baudrate=baudrate, error=None)
        try:
            if self.reader:
                self.reader.stop()
            if self.serial_obj and hasattr(self.serial_obj, "close"):
                self.serial_obj.close()
        except Exception as exc:
            LOGGER.exception("Serial close failed")
            self._set_state(SerialState.ERROR, port=port, baudrate=baudrate, error=str(exc), kind=SerialErrorKind.UNKNOWN)
            if self._on_error:
                self._on_error(exc)
            return
        finally:
            self.reader = None
            self.serial_obj = None
            self.writer = SerialWriter(None)
        self._set_state(SerialState.DISCONNECTED, port=port, baudrate=baudrate, error=None)

    def reconnect(self, *, delay_s: float = 0.2) -> None:
        """按“关闭 -> 等待 -> 重新打开”的顺序重连。"""
        if not self.status.port or not self.status.baudrate:
            self._set_state(SerialState.ERROR, error="no previous serial port to reconnect", kind=SerialErrorKind.PORT_NOT_FOUND)
            return
        port = self.status.port
        baudrate = self.status.baudrate
        self._set_state(SerialState.RECONNECTING, port=port, baudrate=baudrate, error=None)
        self.close()
        time.sleep(delay_s)
        self.open(port, baudrate)

    def is_connected(self) -> bool:
        return self.state == SerialState.CONNECTED and bool(self.serial_obj and getattr(self.serial_obj, "is_open", False))

    def write(self, data: bytes) -> WriteResult:
        return self.writer.write(data)

    def write_control(self, metadata: ControlMetadata) -> WriteResult:
        return self.writer.write_control(metadata)

    def _handle_reader_error(self, exc: Exception) -> None:
        self._set_state(SerialState.ERROR, error=str(exc), kind=SerialErrorKind.DEVICE_REMOVED)
        if self._on_error:
            self._on_error(exc)

    def _set_state(
        self,
        state: SerialState,
        *,
        port: str | None = None,
        baudrate: int | None = None,
        error: str | None = None,
        kind: SerialErrorKind | None = None,
    ) -> None:
        self.status = SerialStatus(
            state=state,
            port=port if port is not None else self.status.port,
            baudrate=baudrate if baudrate is not None else self.status.baudrate,
            last_error=error,
            error_kind=kind,
        )
        if self._on_state_changed:
            self._on_state_changed(self.status)


def _default_serial_factory() -> SerialFactory:
    """延迟导入 pyserial，避免导入 pydisplay.io 时就要求依赖存在。"""
    try:
        from serial import Serial
    except ImportError as exc:
        raise RuntimeError("pyserial is not available; activate Pydisplay_env") from exc
    return Serial


def _classify_open_exception(exc: Exception) -> SerialErrorKind:
    if isinstance(exc, FileNotFoundError):
        return SerialErrorKind.PORT_NOT_FOUND
    if isinstance(exc, PermissionError):
        return SerialErrorKind.PERMISSION_DENIED
    text = str(exc).lower()
    if "access is denied" in text or "permission" in text:
        return SerialErrorKind.PERMISSION_DENIED
    if "busy" in text or "in use" in text:
        return SerialErrorKind.PORT_BUSY
    if "could not open port" in text or "not found" in text:
        return SerialErrorKind.PORT_NOT_FOUND
    return SerialErrorKind.UNKNOWN
