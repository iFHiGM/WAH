import logging
import sys
from system.config import Config

# 全局 Logger 配置
logger = logging.getLogger("WAH")
# 根据 Config 设置日志级别
log_level = logging.DEBUG if Config.DEBUG else logging.INFO
logger.setLevel(log_level)

# 防止重复添加 Handler
if not logger.handlers:
    # File Handler: 始终记录详细信息 (DEBUG) 以便事后分析
    file_handler = logging.FileHandler(Config.LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler: 根据 Config.DEBUG 决定是否输出到屏幕
    # 但为了保持界面清爽，我们通常只在 DEBUG 模式下向控制台输出 LOG，
    # 正常模式下只靠 print 输出 UI 信息。
    if Config.DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('[LOG] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

def get_logger():
    return logger
