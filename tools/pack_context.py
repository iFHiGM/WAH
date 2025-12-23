import os

# 定义要忽略的目录和文件
IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', 'dist', 'build', '.idea', '.vscode'}
IGNORE_FILES = {'.DS_Store', 'package-lock.json', 'yarn.lock'}
# 定义要读取的文件后缀
TARGET_EXTS = {'.py', '.md', '.org', '.sh', '.json', '.yaml', '.txt'}

def pack_project(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"# WAH PROJECT CONTEXT DUMP\n")
        out.write(f"# 此文件由脚本自动生成，用于同步给 AI 协作者\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # 修改 dirs 列表以原地过滤遍历目录
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                _, ext = os.path.splitext(file)
                if ext not in TARGET_EXTS: continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                
                # 排除输出文件本身
                if file_path == os.path.abspath(output_file): continue

                out.write(f"='='= FILE START: {rel_path} ='='=\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"[Error reading file: {e}]")
                out.write(f"\n='='= FILE END: {rel_path} ='='=\n\n")

if __name__ == "__main__":
    pack_project('.', 'WAH_FULL_CONTEXT.txt')
    print("✅ 项目代码已打包至 WAH_FULL_CONTEXT.txt，请将此文件投喂给 Gemini。")