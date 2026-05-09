"""Pydisplay 顶层包。

这里暴露最基础的包信息。业务模块分散在 protocol、io、recorder、
replay、gui、services 等子包中。
"""

from .version import __version__

__all__ = ["__version__"]
