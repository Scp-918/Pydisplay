"""协议层异常类型。

使用专门异常的好处：
- GUI 可以把协议错误显示给用户；
- 测试可以明确判断失败原因；
- 串口层、记录层不会把协议错误误认为普通系统错误。
"""

from __future__ import annotations


class ProtocolError(Exception):
    """Base class for protocol errors."""


class ProtocolNotConfirmedError(ProtocolError):
    """Raised when a requested protocol detail is not confirmed."""


class FrameDecodeError(ProtocolError):
    """Raised when a parsed frame cannot be decoded."""


class CommandValidationError(ProtocolError, ValueError):
    """Raised when a control command parameter is invalid."""
