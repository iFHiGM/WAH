import subprocess
from typing import Tuple

def execute(command: str) -> Tuple[int, str, str]:
    """执行 Shell 命令并返回 (exit_code, stdout, stderr)"""
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr
