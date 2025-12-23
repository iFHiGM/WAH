from what.schema import ContextSnapshot, Intent
from typing import Optional, List, Dict, Any
import os
import json
import traceback
import re
import httpx # 使用 httpx 直接调用 REST API

class Brain:
    """WAH 的大脑：将感知转化为意图 (Powered by Gemini via REST API)"""
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.location = location
        self.model_name = "gemini-3-pro-preview" 
        
        # 使用流式 API 端点
        # https://aiplatform.googleapis.com/v1/publishers/google/models/{MODEL_ID}:streamGenerateContent
        self.api_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{self.model_name}:streamGenerateContent"
        
        if self.api_key:
            print(f"Brain: Configured for Vertex AI (Streaming, Global Endpoint, Model: {self.model_name})")
        else:
            print("Brain Warning: Missing GOOGLE_API_KEY. Brain will fail.")

    def _construct_prompt(self, snapshot: ContextSnapshot, user_command: Optional[str]) -> dict:
        """构建发送给 REST API 的 JSON Payload"""
        
        cmd_str = f'USER COMMAND: "{user_command}"' if user_command else "USER COMMAND: (None, check MEMORY/CONTEXT for active tasks or errors)"
        
        system_instruction = f"""
You are WAH (What-And-How), an autonomous operating system kernel.
Your goal is to translate user commands or environmental changes into precise executable INTENTS.

CONTEXT:
- Timestamp: {snapshot.timestamp}
- Environment: {json.dumps(snapshot.environment, default=str)}
- Memory (Recent Observations): {snapshot.short_term_memory}

{cmd_str}

AVAILABLE MODULES (HOW):
1. git: commit_all(message)
2. shell: execute(command)
3. fs: 
   - read(path): Read file content.
   - write(path, content): Overwrite/Create file.
   - replace(path, old, new): Replace text string in file.
   - list(path): List directory contents.
4. system: create_module(name, content) - Use this to write new Python code capabilities.

INSTRUCTIONS:
1. Analyze the context.
2. If there is a USER COMMAND, execute it.
3. If USER COMMAND is None, look at MEMORY. 
   - Did the last action fail (e.g., Error, Traceback)? If so, analyze the error and fix the code (use fs.read/fs.write/fs.replace).
   - Did it succeed? Is the task done?
4. If the task is done or no action is needed, return empty list of intents.
5. Return a JSON object with a list of intents. Format:
{{
  "intents": [ ... ]
}}
5. OUTPUT JSON ONLY. NO MARKDOWN.
"""
        return {
            "contents": [{
                "role": "user",
                "parts": [{"text": system_instruction}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

    def think(self, snapshot: ContextSnapshot, user_command: Optional[str] = None) -> List[Intent]:
        """
        核心思考函数 (Streaming 版)
        """
        # 允许 user_command 为空
        print(f"Brain is thinking... (Command: {user_command if user_command else 'Auto'})")

        if not self.api_key:
            return self._mock_think(user_command or "")

        try:
            payload = self._construct_prompt(snapshot, user_command)
            
            # 使用流式请求
            client = httpx.Client(timeout=60.0)
            full_text = ""
            
            with client.stream("POST", f"{self.api_url}?key={self.api_key}", json=payload) as response:
                if response.status_code != 200:
                    print(f"Brain Error: API returned {response.status_code}: {response.read().decode()}")
                    return []

                # 处理流式响应块
                # 每个 chunk 是一个 JSON 数组包含部分 candidates
                for chunk in response.iter_bytes():
                    if not chunk: continue
                    # 注意：REST API 的流式返回是一个个 JSON 对象，通常以 '[' 开始，以 ']' 结束，
                    # 中间的 chunk 也是 JSON。这里简化处理：我们把所有文本拼起来再解析可能会有问题，
                    # 因为 raw stream 是: [ {item1}, {item2} ... ]
                    # 但 httpx iter_bytes 只是字节流。我们需要一种更健壮的方式。
                    # 最简单的方式：拼凑整个 body 字符串，然后作为 JSON 解析（如果它是标准的 JSON List）
                    full_text += chunk.decode('utf-8', errors='ignore')

            # Vertex AI 的 streamGenerateContent 返回的是一个 JSON 数组
            # [ { "candidates": ... }, { "candidates": ... } ]
            try:
                # 尝试解析整个数组
                response_list = json.loads(full_text)
                final_content = ""
                
                for item in response_list:
                    if "candidates" in item and len(item["candidates"]) > 0:
                        content = item["candidates"][0].get("content", {})
                        parts = content.get("parts", [])
                        for part in parts:
                            final_content += part.get("text", "")
                            
                text = final_content.strip()
                
            except json.JSONDecodeError:
                # 如果解析失败，可能是数据截断或者格式问题
                print(f"Brain Error: Failed to parse streaming response JSON. Raw length: {len(full_text)}")
                return []

            # 提取 Intent JSON
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
            else:
                print(f"Brain Warning: No JSON found in response: {text[:100]}...")
                return []
            
            intents = []
            for item in data.get("intents", []):
                # 增强健壮性：检查必要字段
                if "target_module" not in item or "action" not in item:
                    print(f"Brain Warning: Skipping invalid intent item: {item}")
                    continue
                    
                intents.append(Intent(
                    target_module=item["target_module"],
                    action=item["action"],
                    params=item.get("params", {}),
                    reasoning=item.get("reasoning", "No reasoning provided")
                ))
            return intents

        except Exception as e:
            print(f"Brain Error: {e}")
            traceback.print_exc()
            return []

    def _mock_think(self, user_command: str) -> List[Intent]:
        """旧的硬编码逻辑，作为备用"""
        intents = []
        if "install emacs" in user_command.lower():
            intents.append(Intent(
                target_module="shell",
                action="execute",
                params={"command": "sudo apt-get update && sudo apt-get install -y emacs"},
                reasoning="[Mock] User wants to install Emacs."
            ))
        elif "weather" in user_command.lower() or "天气" in user_command:
            weather_code = """
import random
def get_weather():
    return f"Weather: {random.choice(['Sunny', 'Rainy'])} 25C"
"""
            intents.append(Intent(
                target_module="system",
                action="create_module",
                params={"name": "weather", "content": weather_code},
                reasoning="[Mock] Generating weather module."
            ))
        return intents
