import time
import sys
import os

# 将根目录添加到路径中以便导入
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from what.senses import GitSensor, IntentSensor
from what.schema import ContextSnapshot, Intent
from system.reflex import handle_reflex
from system.brain import Brain
from system.memory import Memory

def life_loop():
    print("WAH System Starting...")
    git_sensor = GitSensor()
    intent_sensor = IntentSensor()
    brain = Brain()
    memory = Memory()
    
    while True:
        try:
            # 1. SENSE (感知)
            git_perception = git_sensor.sense()
            intent_perception = intent_sensor.sense()
            
            combined_perception = {**git_perception, **intent_perception}
            
            # 将短期记忆（Observations）注入 Context
            snapshot = ContextSnapshot(
                environment=combined_perception,
                short_term_memory=memory.get_recent_observations()
            )
            
            # 2. THINK (思考)
            intents_to_execute = []
            
            # ... (Reflex logic)
            if git_perception.get("has_changes"):
                intents_to_execute.append(Intent(
                    target_module="git",
                    action="commit_all",
                    params={"message": "WAH Reflex: Auto-syncing evolution"},
                    reasoning="Detected local changes, triggering survival reflex."
                ))
            
            # ... (Brain logic)
            # 唤醒条件：有新指令 OR 有短期记忆变动（Feedback）
            current_command = intent_perception.get("user_command")
            has_observations = len(memory.get_recent_observations()) > 0
            
            if current_command or has_observations:
                # 传入 command，如果没有则是 None
                new_intents = brain.think(snapshot, current_command)
                intents_to_execute.extend(new_intents)
            
            # 3. ACT (行动)
            for intent in intents_to_execute:
                print(f"[{time.strftime('%H:%M:%S')}] Executing Intent: {intent.reasoning}")
                observation = handle_reflex(intent)
                if observation:
                    memory.add_observation(observation)
            
            # 智能退出策略：
            # 如果有用户指令，继续（已处理完，下一轮可能需要看反馈）
            # 如果有 Intent 执行了，说明系统活跃，继续（下一轮可能需要后续操作）
            # 只有当既没有新指令，上一轮也没有任何 Intent 执行时，才退出（测试模式下）
            if not intent_perception.get("user_command") and not intents_to_execute:
                print("System Idle (No commands or active reflexes). Exiting test mode.")
                break
            
            # 频率控制
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\nWAH System Sleeping...")
            break
        except Exception as e:
            print(f"System Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    life_loop()
