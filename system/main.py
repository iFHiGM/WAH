import time
import sys
import os
import json

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
            if event.type == EventType.USER_COMMAND:
                cmd = event.payload.strip().lower()
                if cmd == "reload":
                    logger.info("HOT RELOAD TRIGGERED BY USER")
                    print("Initiating Hot Reload...")
                    memory.dump_state()
                    
                    # Restart process
                    # We use sys.executable and sys.argv to restart the script
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
            
            # Update Memory
            if event.type == EventType.USER_COMMAND:
                memory.add_observation(f"USER: {event.payload}")
            elif event.type == EventType.FILE_CHANGE:
                memory.add_observation(f"FILE: {event.payload}")
            elif event.type == EventType.SYSTEM_ERROR:
                memory.add_observation(f"ERROR: {event.payload}")
            elif event.type == EventType.BRAIN_OBSERVATION:
                memory.add_observation(f"BRAIN: {event.payload}")

            # 4. Context Building
            snapshot = ContextSnapshot(
                timestamp=time.time(),
                objective=memory.active_objective,
                short_term_memory=list(memory.short_term_observations),
                event_trigger=event
            )
            memory.save_snapshot(snapshot)

            # 5. Brain Processing (Think)
            # Only think if there is an objective OR it's a direct command OR Idle event
            should_think = (
                memory.active_objective is not None or 
                event.type == EventType.USER_COMMAND or
                event.type == EventType.IDLE
            )
            
            if should_think:
                intent = brain.think(memory, event)
                
                if intent:
                    logger.info(f"Brain Intent: {intent.action} on {intent.target_module}")
                    
                    # Execute Intent (Reflex)
                    observation = handle_reflex(intent)
                    
                    # Feedback Loop
                    if observation:
                        bus.put(Event.observation(observation))
                        
                        # Check for Reload Intent from Brain
                        if intent.target_module == "system" and intent.action == "reload":
                             logger.info("HOT RELOAD TRIGGERED BY BRAIN")
                             print("Initiating Hot Reload (Brain)...")
                             memory.dump_state()
                             python = sys.executable
                             os.execl(python, python, *sys.argv)

    except KeyboardInterrupt:
        print("\nWAH Kernel Stopping...")
        logger.info("WAH Kernel Stopped by User")
    except Exception as e:
        logger.critical(f"WAH Kernel Crashed: {e}", exc_info=True)
        raise