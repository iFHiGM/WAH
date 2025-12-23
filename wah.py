#!/usr/bin/env python3
import sys
import os

# 将当前目录加入 path，确保能找到 system, what, how
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from system.main import life_loop

if __name__ == "__main__":
    # 可以在这里处理命令行参数，比如 --debug 或 --model
    try:
        life_loop()
    except KeyboardInterrupt:
        pass
