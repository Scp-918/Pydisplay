"""`python -m pydisplay` 的入口文件。

Python 执行 `-m pydisplay` 时会运行这个文件。
它只转发到 `pydisplay.app.main()`，真正的启动逻辑放在 app.py 中。
"""

from .app import main


if __name__ == "__main__":
    raise SystemExit(main())
