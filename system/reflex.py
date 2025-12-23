from what.schema import Intent
from how import git, shell, fs
import sys
import os

def handle_reflex(intent: Intent) -> str:
    """
    处理器支持动态能力加载。
    返回执行结果字符串 (Observation)。
    """
    observation = ""
    
    if intent.target_module == "git":
        if intent.action == "commit_all":
            msg = intent.params.get("message", "Auto-commit")
            code, out, err = git.commit_all(msg)
            observation = f"Git Commit: {'Success' if code == 0 else 'Failed'}. Output: {out or err}"
                
    elif intent.target_module == "shell":
        if intent.action == "execute":
            cmd = intent.params.get("command")
            if cmd:
                # Pre-execution Validation: Check if target script exists
                parts = cmd.split()
                target_file = None
                
                # Simple heuristic to identify script execution
                if len(parts) > 0:
                    if parts[0].startswith("./") or parts[0].endswith(".sh"):
                        target_file = parts[0]
                    elif parts[0] in ["python", "python3"] and len(parts) > 1:
                        target_file = parts[1]
                
                # If a target file is identified, verify its existence
                if target_file and not os.path.exists(target_file) and not target_file.startswith("-"):
                    error_msg = f"Error: Execution target '{target_file}' not found. Aborting command to prevent crash."
                    print(error_msg)
                    return error_msg

                print(f"Running command: {cmd}")
                code, out, err = shell.execute(cmd)
                status = "Success" if code == 0 else f"Failed({code})"
                output = (out + err).strip()
                print(f"Command {status}:\n{output}")
                observation = f"Shell Command '{cmd}': {status}. Output:\n{output}"
            else:
                observation = "Error: Shell command is empty."

    elif intent.target_module == "fs":
        path = intent.params.get("path")
        
        # Handle 'list' separately as it has a default
        if intent.action == "list":
            target_path = path or "."
            result = fs.list_files(target_path)
            print(f"Reflex: List {target_path}")
            observation = f"Directory {target_path}:\n{result}"
        
        # For other actions, path is mandatory to prevent crashes in how/fs.py
        elif path is None:
            observation = f"Error: Parameter 'path' is required for action '{intent.action}'."
        
        elif intent.action == "read":
            content = fs.read_file(path)
            print(f"Reflex: Read file {path}")
            observation = f"File Content ({path}):\n{content}"
            
        elif intent.action == "write":
            content = intent.params.get("content", "")
            result = fs.write_file(path, content)
            print(f"Reflex: Write file {path}")
            observation = f"File Write ({path}): {result}"
            
        elif intent.action == "replace":
            old = intent.params.get("old")
            new = intent.params.get("new")
            if old is None or new is None:
                observation = "Error: Parameters 'old' and 'new' are required for replace."
            else:
                result = fs.replace_text(path, old, new)
                print(f"Reflex: Replace text in {path}")
                observation = f"File Replace ({path}): {result}"

    elif intent.target_module == "chat":
        if intent.action == "reply":
            msg = intent.params.get("text") or intent.params.get("message")
            if msg:
                # 使用不同的颜色或前缀使其醒目
                print(f"\n🤖 WAH says: {msg}\n")
                # Hack: 强制刷新提示符，避免用户不知道可以输入
                sys.stdout.write("wah> ")
                sys.stdout.flush()
                observation = f"Chat Reply: {msg}"

    elif intent.target_module == "system":
        if intent.action == "create_module":
            name = intent.params.get("name")
            content = intent.params.get("content")
            if name and content:
                file_path = f"how/{name}.py"
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Reflex Action: Written module how/{name}.py")
                    
                    # 动态加载 (importlib logic usually handled by Brain reload or restart, 
                    # but we record it here)
                    observation = f"System: Created module how/{name}.py"
                except Exception as e:
                    observation = f"System Error: Failed to create module. {e}"

    return observation