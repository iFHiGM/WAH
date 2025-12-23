import os
from how.models import get_best_heavy_model, get_best_fast_model

def load_dotenv():
    """Simple .env loader to avoid external dependencies"""
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ[k] = v.strip('"\'')

load_dotenv()

class Config:
    # 基础信息
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # 置 (动态获取)
    MODEL_HEAVY = get_best_heavy_model()
    MODEL_FAST = get_best_fast_model()
    
    # Brain 参数
    BRAIN_TIMEOUT = float(os.getenv("WAH_BRAIN_TIMEOUT", "90.0"))
    BRAIN_TEMP = float(os.getenv("WAH_BRAIN_TEMP", "0.2"))
    
    # 运行时存储
    WAH_HOME = ".wah"
    OBJECTIVE_FILE = os.path.join(WAH_HOME, "active_objective")
    LESSONS_FILE = os.path.join(WAH_HOME, "lessons_learned.org")
    MEMORY_DUMP_FILE = os.path.join(WAH_HOME, "memory_dump.json")
    
    # Runtime Flags
    RELOAD_SIGNAL = False

    # 日志配置
    LOG_FILE = os.path.join(WAH_HOME, "wah.log")
    # 如果环境变量 WAH_DEBUG=true，则开启详细日志
    DEBUG = os.getenv("WAH_DEBUG", "false").lower() == "true"
    
    # 系统常量
    PROTECTED_FILES = {"GENESIS.org", "README.org"}
    MEMORY_CAPACITY = 50
    SNAPSHOT_HISTORY = 20

    @staticmethod
    def ensure_runtime_dir():
        if not os.path.exists(Config.WAH_HOME):
            os.makedirs(Config.WAH_HOME, exist_ok=True)

# 初始化运行时目录
Config.ensure_runtime_dir()

# 单例验证
if not Config.API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in environment.")
