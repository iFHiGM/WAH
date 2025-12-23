from abc import ABC, abstractmethod
from .schema import ContextSnapshot

class BaseSensor(ABC):
    """定义如何抓取环境 (BaseSensor)"""
    
    @abstractmethod
    def sense(self) -> dict:
        """执行感知动作，返回感知到的数据片段"""
        pass

class GitSensor(BaseSensor):
    """感知 Git 仓库状态的传感器"""
    def sense(self) -> dict:
        import subprocess
        try:
            status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.STDOUT).decode().strip()
            return {"git_status": status, "has_changes": len(status) > 0}
        except Exception as e:
            return {"git_error": str(e)}

class IntentSensor(BaseSensor):
    """从外部文件读取意图指令的传感器"""
    def __init__(self, command_file: str = "intent.txt"):
        self.command_file = command_file

    def sense(self) -> dict:
        import os
        import time
        if os.path.exists(self.command_file):
            try:
                with open(self.command_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    # 重命名文件以归档，防止重复执行
                    timestamp = int(time.time())
                    os.rename(self.command_file, f"{self.command_file}.{timestamp}.done")
                    return {"user_command": content}
            except Exception as e:
                return {"command_error": str(e)}
        return {}
