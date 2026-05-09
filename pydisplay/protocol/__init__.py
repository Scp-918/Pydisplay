"""固件协议子包。

包括：
- constants：协议常量；
- parser：流式解析状态机；
- decoder：字段解码和 UD 计算；
- commands：上位机控制命令编码。
"""

from .decoder import decode_frame
from .parser import FrameParser

__all__ = ["FrameParser", "decode_frame"]
