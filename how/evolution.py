import os
import shutil
import sys
from system.config import Config
from system.logger import get_logger

logger = get_logger()

def prepare_incubator():
    """
    Clones the current 'system/' to 'system_incubator/' to begin a mutation cycle.
    ALWAYS call this before staging changes.
    """
    src = "system"
    dst = "system_incubator"
    
    try:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        
        shutil.copytree(src, dst)
        logger.info(f"Evolution: Cloned {src} to {dst}")
        return "Incubator prepared. You can now stage changes."
    except Exception as e:
        return f"Error preparing incubator: {e}"

def stage_change(path: str, content: str):
    """
    Writes a file to the incubator directory.
    Args:
        path: Relative path inside system/ (e.g., 'brain.py')
        content: The full new content of the file.
    """
    if ".." in path or path.startswith("/"):
        return "Error: Invalid path. Must be relative to system/."
        
    target_path = os.path.join("system_incubator", path)
    
    if not os.path.exists("system_incubator"):
        return "Error: Incubator not found. Call 'prepare_incubator' first."
        
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Staged change to {target_path}"
    except Exception as e:
        return f"Error staging change: {e}"

def trigger_evolution():
    """
    Signals the Kernel to exit(100) and let the Watchdog promote the incubator.
    Call this only after all changes are staged.
    """
    if not os.path.exists("system_incubator"):
        return "Error: No incubator to promote."
        
    # We communicate via Config singleton
    Config.RELOAD_SIGNAL = True
    return "Evolution Signal Set. System will restart and test the new code shortly."
