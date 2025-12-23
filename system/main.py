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
            if event.type == EventType.USER_COMMAND:
                cmd = event.payload.strip().lower()
                if cmd == "reload":
                    logger.info("KERNEL: Hot Reload Triggered by User.")
                    print("Initiating Hot Reload...")
                    memory.dump_state()
                    
                    # Restart process
                    # We use os.execv to replace the current process with a new one
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
            
            # 4. Context Building
            snapshot = ContextSnapshot(
                timestamp=event.timestamp,
                event_type=event.type.name,
                event_payload=str(event.payload),
                active_objective=memory.active_objective,
                recent_observations=memory.get_recent_observations()
            )
            memory.save_snapshot(snapshot)
            
            # 5. Brain Processing (Think)
            intent = brain.think(memory.active_objective, snapshot, memory.short_term_observations)
            
            if intent:
                logger.info(f"BRAIN: Intent generated -> {intent.action} on {intent.target_module}")
                
                # 6. Reflex (Act)
                observation = handle_reflex(intent)
                
                # 7. Feedback (Learn/Memorize)
                if observation:
                    print(f">> {observation}")
                    memory.add_observation(observation)
                    
                    # If intent was to set objective, update memory
                    if intent.target_module == "system" and intent.action == "set_objective":
                        memory.set_objective(intent.params.get("goal"))
                    elif intent.target_module == "system" and intent.action == "clear_objective":
                        memory.clear_objective()

    except KeyboardInterrupt:
        print("\nStopping WAH Kernel...")
        logger.info("WAH Kernel Stopped by User")