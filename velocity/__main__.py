"""允许通过 python -m velocity 运行命令行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
