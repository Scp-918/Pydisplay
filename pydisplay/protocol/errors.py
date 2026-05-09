"""Protocol-specific exceptions."""

from __future__ import annotations


class ProtocolError(Exception):
    """Base class for protocol errors."""


class ProtocolNotConfirmedError(ProtocolError):
    """Raised when a requested protocol detail is not confirmed."""


class FrameDecodeError(ProtocolError):
    """Raised when a parsed frame cannot be decoded."""


class CommandValidationError(ProtocolError, ValueError):
    """Raised when a control command parameter is invalid."""
