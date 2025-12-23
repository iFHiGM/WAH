import time
import sys
import os

# 将根目录添加到路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.bus import EventBus
from system.events import Event, EventType
from what.senses import GitSensor, FileIntentSensor, TerminalInputSensor
from system.brain import Brain
from system.memory import Memory
from system.config import Config
from what.schema import ContextSnapshot, Intent
from system.reflex import handle_reflex

from system.logger import get_logger
logger = get_logger()

def life_loop():
    print("WAH Kernel Starting... (Tail 'wah.log' for debug info)")
    logger.info("WAH Kernel Session Started")
    
    # 1. Infrastructure
    bus = EventBus()
    memory = Memory()
    brain = Brain() 
    
    # 2. Sensors (Producers)
    sensors = [
        GitSensor(bus),
        FileIntentSensor(bus),
    ]
    
    # 强制开启 CLI 传感器，以便支持管道输入测试
    sensors.append(TerminalInputSensor(bus))
    
    for s in sensors:
        s.start()

    # 3. Main Loop (Consumer)
    try:
        while True:
            # 阻塞等待事件 (带超时以支持空闲检测)
            event = bus.get(timeout=5.0) 
            
            if not event:
                # IDLE CHECK
                if not memory.active_objective:
                    # 仅当有“教训”待消化时才触发 IDLE 事件，避免无意义的 Token 消耗
                    if os.path.exists(Config.LESSONS_FILE):
                        try:
                            if os.path.getsize(Config.LESSONS_FILE) > 10: # Ignore empty/header-only files
                                logger.info("KERNEL: System Idle. Detected unlearned lessons. Triggering Self-Reflection.")
                                event = Event(priority=10, type=EventType.IDLE, payload=f"{Config.LESSONS_FILE} available", source="system")
                        except:
                            pass
                
                if not event: continue

            # 日志记录内部事件
            logger.debug(f"KERNEL: Consuming Event {event.type.name} (Priority {event.priority}) Source: {event.source}")

            if event.type == EventType.USER_COMMAND:
                logger.info(f"USER COMMAND: {event.payload}")
                print(f"Processing command: {event.payload}...")
                
                snapshot = ContextSnapshot(
                    environment={"last_event": "user_command"},
                    short_term_memory=memory.get_recent_observations()
                )
                memory.save_snapshot(snapshot)

                # 传入当前目标
                intents = brain.think(snapshot, event.payload, memory.active_objective)
                execute_intents(intents, bus, memory)

            elif event.type == EventType.IDLE:
                 # 空闲自省模式
                print("WAH: Idle... Checking lessons learned.")
                snapshot = ContextSnapshot(
                    environment={"last_event": "idle_reflection"},
                    short_term_memory=memory.get_recent_observations()
                )
                
                # 构造一个特殊的 Prompt 让 Brain 处理自省
                # 这里我们复用 think，但传入特殊的命令
                intents = brain.think(snapshot, f"SYSTEM_INTERNAL: Perform Self-Reflection based on {Config.LESSONS_FILE}", memory.active_objective)
                execute_intents(intents, bus, memory)

            elif event.type == EventType.BRAIN_OBSERVATION:
                # 检查是否是系统控制指令
                obs = event.payload
                if obs.startswith("SYSTEM_CONTROL:SET_OBJECTIVE:"):
                    goal = obs.replace("SYSTEM_CONTROL:SET_OBJECTIVE:", "")
                    memory.set_objective(goal)
                elif obs == "SYSTEM_CONTROL:CLEAR_OBJECTIVE":
                    memory.clear_objective()
                else:
                    memory.add_observation(obs)
                
                logger.debug(f"OBSERVATION: {obs[:100]}...")
                
                snapshot = ContextSnapshot(
                    environment={"last_event": "observation"},
                    short_term_memory=memory.get_recent_observations()
                )
                memory.save_snapshot(snapshot)

                # 熔断机制：如果没有活跃目标，Observation 仅存入记忆，不触发思考
                # 这防止了任务完成后，Agent 对“任务完成”这个事实本身进行过度反应，导致死循环
                if memory.active_objective:
                    intents = brain.think(snapshot, None, memory.active_objective)
                    execute_intents(intents, bus, memory)
                else:
                    logger.info("KERNEL: No active objective. Observation absorbed without triggering Brain.")

            elif event.type == EventType.FILE_CHANGE:
                msg = f"Environment Change: {event.payload}"
                memory.add_observation(msg)
                logger.info(msg)

            # 标记任务完成
            # bus.task_done() # PriorityQueue 没有 task_done，只有 Queue 有

    except KeyboardInterrupt:
        print("\nWAH Kernel Stopping...")
    finally:
        for s in sensors:
            s.stop()

def execute_intents(intents, bus, memory):
    """执行意图并将结果作为新事件发布"""
    for intent in intents:
        # 如果不是纯聊天的 ACT，记录到日志
        if intent.target_module != "chat":
            logger.info(f"ACT: {intent.reasoning}")
        
        observation = handle_reflex(intent)
        if observation:
            bus.put(Event.observation(observation))

if __name__ == "__main__":
    life_loop()
