from what.schema import Intent
from how import git, shell

import importlib
import sys
import os
from how import git, shell, fs

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
                print(f"Running command: {cmd}")
                code, out, err = shell.execute(cmd)
                status = "Success" if code == 0 else f"Failed({code})"
                output = (out + err).strip()
                print(f"Command {status}:\n{output}")
                observation = f"Shell Command '{cmd}': {status}. Output:\n{output}"

    elif intent.target_module == "fs":
        path = intent.params.get("path")
        if intent.action == "read":
            content = fs.read_file(path)
            print(f"Reflex: Read file {path}")
            observation = f"File Content ({path}):\n{content}"
        elif intent.action == "write":
            content = intent.params.get("content")
            result = fs.write_file(path, content)
            print(f"Reflex: Write file {path}")
            observation = f"File Write ({path}): {result}"
        elif intent.action == "replace":
            old = intent.params.get("old")
            new = intent.params.get("new")
            result = fs.replace_text(path, old, new)
            print(f"Reflex: Replace text in {path}")
            observation = f"File Replace ({path}): {result}"
        elif intent.action == "list":
            result = fs.list_files(path or ".")
            print(f"Reflex: List files in {path}")
            observation = result

    elif intent.target_module == "system":
        if intent.action == "create_module":
            # ... (Existing logic)
            name = intent.params.get("name")
            content = intent.params.get("content")
            if name and content:
                file_path = f"how/{name}.py"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Reflex Action: Written module how/{name}.py")
                
                module_name = f"how.{name}"
                try:
                    if module_name in sys.modules:
                        print(f"Reflex: Reloading existing module {module_name}...")
                        importlib.reload(sys.modules[module_name])
                    else:
                        print(f"Reflex: Importing new module {module_name}...")
                        importlib.import_module(module_name)
                    observation = f"System: Created and loaded module {module_name}"
                except Exception as e:
                    observation = f"System: Created module {module_name} but failed to load: {e}"
    
    return observation
