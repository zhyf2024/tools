"""把项目根目录加入 sys.path，方便直接 ``uv run pytest``。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
