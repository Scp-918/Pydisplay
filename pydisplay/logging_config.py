"""日志配置。

程序运行时会同时输出到：
1. 终端控制台；
2. `logs/pydisplay.log` 滚动日志文件。

日志用于排查串口异常、协议异常、记录异常和 GUI 启动问题。
`configure_logging()` 设计成可重复调用，避免测试或二次初始化时重复添加 handler。
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import DEFAULT_LOG_FILE, LOG_DIR


def configure_logging(level: int = logging.INFO) -> None:
    """只初始化一次日志系统。"""

    root = logging.getLogger()
    if root.handlers:
        # 已经配置过日志时直接返回，避免一条日志被重复打印多次。
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        DEFAULT_LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)
