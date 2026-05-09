"""服务层子包。

服务层连接协议、串口、记录、回放和 GUI。
它尽量保持纯 Python，便于单元测试。
"""

from .health_monitor import HealthMonitor, HealthSnapshot

__all__ = ["HealthMonitor", "HealthSnapshot"]
