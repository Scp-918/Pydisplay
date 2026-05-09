"""Pydisplay 程序启动入口。

这个文件只负责“把应用启动起来”：
1. 解析命令行参数；
2. 初始化日志；
3. 创建 QApplication 和 MainWindow；
4. 根据参数决定进入 GUI 事件循环，还是只做 smoke test 后退出。

注意：这里不放串口读取、协议解析、文件记录等业务逻辑。
这些工作都交给对应模块，避免入口文件变成难维护的大杂烩。
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from .logging_config import configure_logging


LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    # 目前只提供 smoke-test 参数，便于在 CI 或终端中验证 GUI 能否构造。
    parser = argparse.ArgumentParser(description="Pydisplay GUI")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="create the Qt application and main window, print the title, then exit",
    )
    return parser.parse_args(argv)


def create_app(argv: Sequence[str] | None = None):
    """创建 Qt 应用对象和主窗口，但不进入事件循环。

    拆成这个函数是为了测试和 smoke-test：
    - 正常运行时 main() 会调用 window.show() 和 app.exec()；
    - smoke-test 只创建窗口并打印标题，然后立即退出。
    """

    from PySide6.QtWidgets import QApplication

    from .gui.main_window import MainWindow

    qt_argv = list(argv or [])
    app = QApplication.instance() or QApplication(qt_argv)
    window = MainWindow()
    return app, window


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    LOGGER.info("Starting Pydisplay")

    # Qt 只需要程序名作为 argv。业务参数已经由 argparse 处理完。
    app, window = create_app(sys.argv[:1])
    if args.smoke_test:
        print(window.windowTitle())
        return 0

    window.show()
    return int(app.exec())
