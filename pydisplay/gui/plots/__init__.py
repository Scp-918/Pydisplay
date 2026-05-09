"""绘图支持子包。

包含 ring buffer、曲线配置和 PyQtGraph 曲线管理器。
"""

from .ring_buffer import SampleRingBuffer

__all__ = ["SampleRingBuffer"]
