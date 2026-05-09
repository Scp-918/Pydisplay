from __future__ import annotations

import sys
from pathlib import Path

# 允许用户直接运行 `python scripts\run_app.py`，不要求先安装成包。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydisplay.app import main


if __name__ == "__main__":
    raise SystemExit(main())
