"""项目级静态配置。

这里放“多个模块都需要知道”的基础路径和名称，例如：
- 应用名称；
- 主窗口中文标题；
- 工程根目录；
- 日志目录和日志文件路径。

不要在这里放会频繁变化的运行状态，比如当前串口状态或记录状态。
"""

from __future__ import annotations

from pathlib import Path


APP_NAME = "Pydisplay"
WINDOW_TITLE = "Pydisplay 上位机"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "pydisplay.log"
