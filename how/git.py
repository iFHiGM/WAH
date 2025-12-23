from . import shell

def commit_all(message: str = "Auto-commit by WAH Reflex"):
    """提交所有更改"""
    shell.execute("git add .")
    return shell.execute(f'git commit -m "{message}"')

def get_status():
    """获取 Git 状态"""
    return shell.execute("git status --porcelain")
