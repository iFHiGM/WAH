import threading
import time
import os
import subprocess
from system.bus import EventBus
from system.events import Event

class Sensor(threading.Thread):
    def __init__(self, bus: EventBus, interval: float = 1.0):
        super().__init__(daemon=True)
        self.bus = bus
        self.interval = interval
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            self.sense()
            time.sleep(self.interval)

    def sense(self):
        pass

    def stop(self):
        self.stop_event.set()

class GitSensor(Sensor):
    """主动轮询 Git 状态"""
    def __init__(self, bus: EventBus, interval: float = 5.0):
        super().__init__(bus, interval)
        self._last_status = ""

    def sense(self):
        try:
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                stderr=subprocess.STDOUT
            ).decode().strip()
            
            if status != self._last_status:
                if status: # 只有当非空时（有变动）且变动不同时才触发
                    self.bus.put(Event.file_change(path="repo", change_type="modified"))
                self._last_status = status
        except Exception as e:
            # 避免报错刷屏，可以限制频率，这里暂忽略
            pass

class FileIntentSensor(Sensor):
    """监听 intent.txt (兼容旧脚本测试)"""
    def __init__(self, bus: EventBus, interval: float = 1.0, file_path: str = "intent.txt"):
        super().__init__(bus, interval)
        self.file_path = file_path

    def sense(self):
        if os.path.exists(self.file_path):
            try:
                content = ""
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    # 重命名归档
                    timestamp = int(time.time())
                    os.rename(self.file_path, f"{self.file_path}.{timestamp}.done")
                    
                    self.bus.put(Event.user(content))
            except Exception as e:
                pass

class TerminalInputSensor(Sensor):
    """真正的 CLI 交互 (阻塞式，不使用 interval)"""
    def run(self):
        import sys
        
        # 强制 UTF-8 编码，防止中文输入报错
        try:
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f"Warning: Failed to set UTF-8 encoding: {e}")

        print("WAH Interactive Shell Ready. Type your command:")
        
        while not self.stop_event.is_set():
            try:
                # 使用 sys.stdin 直接读取，允许更灵活的错误处理
                # 注意：这在某些非交互式 shell 中可能会行为不同，但 input() 也是如此
                if not sys.stdin.isatty():
                    # 如果不是 TTY，可能是管道输入，读完即退出
                    line = sys.stdin.read()
                    if line.strip():
                        self.bus.put(Event.user(line.strip()))
                    break
                
                # 打印提示符 (sys.stdout.write 避免缓冲问题)
                sys.stdout.write("wah> ")
                sys.stdout.flush()
                
                line = sys.stdin.readline()
                if not line: # EOF
                    break
                    
                cmd = line.strip()
                if cmd:
                    self.bus.put(Event.user(cmd))
                    
            except UnicodeDecodeError:
                print("Input Error: Invalid encoding. Please use UTF-8.")
            except Exception as e:
                print(f"Input Error: {e}")
