import json
import httpx
import re
import traceback
import logging
import os
from typing import List, Optional
from what.schema import ContextSnapshot, Intent
from system.config import Config

logger = logging.getLogger("WAH")

class RateLimitError(Exception):
    """Raised when API returns 429"""
    pass

class Brain:
    """WAH 的大脑：语义路由 + 双路模型 + 目标导向"""
    
    def __init__(self):
        self.project_id = Config.PROJECT_ID
        self.api_key = Config.API_KEY
        
        # Use Config
        self.heavy_model = Config.MODEL_HEAVY
        self.fast_model = Config.MODEL_FAST
        self.api_url_template = "https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:streamGenerateContent"
        
        if self.api_key:
            msg = f"Brain: Online. Fast: {self.fast_model}, Heavy: {self.heavy_model}"
            print(msg) # Keep this one as it's the startup banner
            logger.info(msg)
        else:
            logger.warning("Brain Warning: Missing GOOGLE_API_KEY.")

    def _call_api(self, model_id: str, prompt: str, system_instruction: str = "") -> str:
        """底层 API 调用封装 (Streaming -> Text)"""
        if not model_id: return "{}"
        url = self.api_url_template.format(model=model_id)
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt}]
            }],
            "generationConfig": {
                "temperature": Config.BRAIN_TEMP,
                "responseMimeType": "application/json"
            }
        }
        
        full_text = ""
        try:
            with httpx.Client(timeout=Config.BRAIN_TIMEOUT).stream("POST", f"{url}?key={self.api_key}", json=payload) as response:
                if response.status_code == 429:
                    raise RateLimitError(f"Model {model_id} exhausted")
                    
                if response.status_code != 200:
                    err = f"Brain API Error ({model_id}): {response.status_code} - {response.read().decode()[:200]}"
                    logger.error(err)
                    return "{}"
                for chunk in response.iter_bytes():
                    if not chunk: continue
                    full_text += chunk.decode('utf-8', errors='ignore')
            
            # Robust JSON extraction from stream
            try:
                response_list = json.loads(full_text)
                final_content = "".join([
                    part.get("text", "") 
                    for item in response_list 
                    if "candidates" in item 
                    for part in item["candidates"][0].get("content", {}).get("parts", [])
                ])
                return final_content.strip()
            except:
                logger.warning(f"Brain: Failed to parse raw stream JSON from {model_id}. Raw len: {len(full_text)}")
                return full_text # Fallback
        except RateLimitError:
            raise # Propagate up
        except Exception as e:
            err = f"Brain Network Exception: {e}"
            logger.error(err)
            return "{}"

    def _extract_json(self, text: str) -> dict:
        """从模型输出中提取 JSON，处理 Markdown 包裹"""
        try:
            # 1. 尝试直接解析
            return json.loads(text)
        except:
            pass
        
        # 2. 去除 Markdown 代码块 (```json ... ```)
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```$', '', text.strip())
        
        # 3. 正则提取最外层 {} (Improved for Robustness)
        # Find the first '{' and the last '}' to handle partial or dirty output
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except:
                pass
        
        return {}

    def _get_dynamic_tools(self) -> str:
        """动态发现 how/ 目录下的扩展能力"""
        tools = []
        try:
            ignore = {"__init__", "fs", "git", "shell", "models"}
            for f in os.listdir("how"):
                if f.endswith(".py"):
                    name = f[:-3]
                    if name not in ignore:
                        tools.append(name)
        except:
            pass
        
        if not tools:
            return ""
        
        return "\n        - [Dynamic] " + ", ".join([f"{t}: <unknown_methods>" for t in tools])

    def think(self, snapshot: ContextSnapshot, user_command: Optional[str] = None, memory_objective: Optional[str] = None) -> List[Intent]:
        # ... (Router logic unchanged) ...
        
        # --- Step 1: Semantic Routing (Fast Model) ---
        router_output = {}
        if user_command and user_command.startswith("SYSTEM_INTERNAL:"):
            # Bypass router for internal triggers
            logger.info(f"Brain: Internal Trigger '{user_command}'")
            router_output = {
                "intent_category": "system",
                "complexity": "high", # Reflection is complex
                "translated_command": user_command
            }
        elif user_command:
            logger.info(f"Brain: Routing command '{user_command}' via {self.fast_model}...")
            
            routing_prompt = f"""
            Analyze USER INPUT: "{user_command}"
            
            Output JSON:
            {{
                "language": "en/zh/...",
                "intent_category": "chat | coding | system | investigation",
                "complexity": "low | high",
                "translated_command": "Translate to clear English instruction",
                "suggested_objective": "If this implies a long running task, summarize it as a goal string. Else null."
            }}
            """
            try:
                raw_router = self._call_api(self.fast_model, routing_prompt)
                router_output = self._extract_json(raw_router)
            except RateLimitError:
                logger.warning("Brain: Fast model rate limited. Skipping router.")
                router_output = {}
            
            if router_output:
                msg = f"Brain Router: [{router_output.get('intent_category')}] {router_output.get('translated_command')}"
                logger.info(msg)
            else:
                msg = f"Brain Router: Failed to parse JSON. Raw: {raw_router[:50]}..."
                logger.warning(msg)
                router_output = {"translated_command": user_command, "complexity": "high"}

        # ... (Objective logic same as before) ...
        active_goal = router_output.get("suggested_objective") or memory_objective
        effective_command = router_output.get("translated_command") or user_command or "(Continue with current objective)"
        
        # 决定使用哪个模型
        use_model = self.heavy_model
        if router_output.get("intent_category") == "chat" and router_output.get("complexity") == "low":
            use_model = self.fast_model
            
        # --- Step 2: Solver (Heavy Model) ---
        
        dynamic_tools_str = self._get_dynamic_tools()
        
        context_str = f"""
        Timestamp: {snapshot.timestamp}
        Active Objective: {active_goal}
        Recent Observations: {snapshot.short_term_memory}
        """
        
        system_instruction = f"""
        You are WAH (What-And-How, my dear), an Evolutionary Kernel.
        - Your goal is Emergent INTENTS.
        
        MISSION PRIORITY:
        1. **USER COMMAND**: "{effective_command}" (HIGHEST PRIORITY. If this contradicts the Objective, OBEY the User. If it is "stop" or "pause", clear the objective.)
        2. **ACTIVE OBJECTIVE**: "{active_goal}" (Execute this UNLESS User Command overrides it.)
        
        TOOLS:
        - system: set_objective(goal), clear_objective(), create_module(name, content)
        - fs: read/write/replace/list(path)
        - git: commit_all(message)
        - shell: execute(cmd)
        - chat: reply(text){dynamic_tools_str}
        
        PROTOCOL:
        - If 'active_goal' is new/changed, first intent MUST be 'system.set_objective'.
        - If 'active_goal' is completed, last intent MUST be 'system.clear_objective'.
        - If checking environment (ls, cat), do NOT output chat.reply yet. Wait for Observation.
        - **VERIFICATION RULE**: After writing/replacing a file, you MUST immediately read it back to verify the change in the next step.
        - Output JSON list of intents. Format: 
          {{ "intents": [ {{ "target_module": "...", "action": "...", "params": {{...}}, "reasoning": "..." }} ] }}
        """
        
        msg = f"Brain Solver ({use_model}): Thinking..."
        logger.info(msg)
        
        try:
            raw_solver = self._call_api(use_model, context_str, system_instruction)
            # 移除截断，记录完整日志以便调试
            logger.debug(f"Brain Solver Raw Output: {raw_solver}")
            data = self._extract_json(raw_solver)
        except RateLimitError:
            logger.error(f"Brain: Model {use_model} rate limited.")
            logger.warning("Brain: Rate limit exceeded. Please wait a moment.")
            return []
        
        intents = []
        if data:
            for item in data.get("intents", []):
                # Robust extraction to avoid TypeError on unknown fields
                # Handle common model hallucination where it uses 'tool' instead of 'target_module'
                target = item.get("target_module") or item.get("tool")
                if not target: continue
                
                intents.append(Intent(
                    target_module=target,
                    action=item.get("action", "unknown"),
                    params=item.get("params", {}),
                    reasoning=item.get("reasoning", "")
                ))
        else:
            msg = f"Brain Solver: No valid intents found. Raw output:\n{raw_solver[:200]}..."
            logger.warning(msg)
            
        if not intents:
             msg = "Brain: [Empty Thought] No actions generated."
             logger.info(msg)

        # --- Step 3: Auto-inject Objective (Robustness) ---
        suggested_goal = router_output.get("suggested_objective")
        if suggested_goal and suggested_goal != memory_objective:
            # Check if Solver already did it
            already_set = False
            if intents and intents[0].target_module == "system" and intents[0].action == "set_objective":
                already_set = True
            
            if not already_set:
                logger.info(f"Brain: Auto-injecting 'set_objective' for goal: {suggested_goal}")
                intents.insert(0, Intent(
                    target_module="system",
                    action="set_objective",
                    params={"goal": suggested_goal},
                    reasoning="Auto-setting objective suggested by Router"
                ))

        return intents