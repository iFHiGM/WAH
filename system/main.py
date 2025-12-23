import time
import sys
import os

# Add root to path
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
    
    # CLI Sensor
    sensors.append(TerminalInputSensor(bus))
    
    for s in sensors:
        s.start()

    # 3. Main Loop (Consumer)
    try:
        while True:
            # Wait for event
            event = bus.get(timeout=5.0) 
            
            if not event:
                # IDLE CHECK
                if not memory.active_objective:
                    if os.path.exists(Config.LESSONS_FILE):
                        try:
                            if os.path.getsize(Config.LESSONS_FILE) > 10:
                                logger.info("KERNEL: System Idle. Detected unlearned lessons. Triggering Self-Reflection.")
                                event = Event(priority=10, type=EventType.IDLE, payload=f"{Config.LESSONS_FILE} available", source="system")
                        except:
                            pass
                
                if not event: continue

            logger.debug(f"KERNEL: Consuming Event {event.type.name} (Priority {event.priority}) Source: {event.source}")
            
            # --- HOT RELOAD HANDLER ---
            should_reload = False
            if event.type == EventType.USER_COMMAND:
                if isinstance(event.payload, str) and event.payload.strip().lower() == "reload":
                    should_reload = True
            
            if should_reload:
                logger.info("HOT RELOAD TRIGGERED. Dumping memory and restarting...")
                memory.dump_context()
                
                # Restart process
                python = sys.executable
                os.execl(python, python, *sys.argv)
            
            # 4. Context Building
            snapshot = ContextSnapshot(
                timestamp=time.time(),
                event=event,
                memory_summary=f"Objective: {memory.active_objective} | Obs: {len(memory.short_term_observations)}",
                active_objective=memory.active_objective
            )
            memory.save_snapshot(snapshot)
            
            # 5. Brain Processing (Think)
            intent = brain.think(memory, event)
            
            if intent:
                logger.info(f"INTENT: {intent.target_module}.{intent.action}")
                
                # 6. Reflex/Action (Act)
                observation = handle_reflex(intent)
                
                # 7. Feedback Loop
                if observation:
                    memory.add_observation(observation)
                    
                    # Check for reload intent from Brain
                    if intent.target_module == "system" and intent.action == "reload":
                         logger.info("Brain requested RELOAD.")
                         memory.dump_context()
                         python = sys.executable
                         os.execl(python, python, *sys.argv)

    except KeyboardInterrupt:
        print("\nStopping WAH Kernel...")
        logger.info("WAH Kernel Stopped by User")
