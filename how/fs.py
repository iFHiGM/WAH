import os

def read_file(path: str, limit: int = 2000) -> str:
    """读取文件内容，默认限制长度以节省 Token"""
    if not os.path.exists(path):
        return f"Error: File {path} not found."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) > limit:
            return content[:limit] + f"\n... (Truncated, total {len(content)} chars)"
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    """写入（覆盖）文件"""
    try:
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def replace_text(path: str, old: str, new: str) -> str:
    """简单的文本替换"""
    if not os.path.exists(path):
        return f"Error: File {path} not found."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old not in content:
            return f"Error: 'old_string' not found in {path}."
        
        new_content = content.replace(old, new, 1) # 默认只替换一次，防止误伤
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Successfully replaced text in {path}"
    except Exception as e:
        return f"Error replacing text: {e}"

def list_files(path: str = ".") -> str:
    """列出目录内容"""
    if not os.path.exists(path):
        return f"Error: Path {path} not found."
    try:
        items = os.listdir(path)
        # 区分文件和目录
        files = []
        dirs = []
        for item in items:
            if item.startswith('.') or item == '__pycache__': continue
            if os.path.isdir(os.path.join(path, item)):
                dirs.append(item + "/")
            else:
                files.append(item)
        return f"Directory {path}:\n" + "\n".join(dirs + files)
    except Exception as e:
        return f"Error listing directory: {e}"
