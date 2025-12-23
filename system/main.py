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
            # --- HOT RELOAD CHECK ---
            if Config.RELOAD_SIGNAL:
                logger.info("KERNEL: Reload Signal Detected. Initiating Hot Reload.")
                print("SYSTEM: Hot Reloading...")
                try:
                    memory.dump_state()
                    sys.stdout.flush()
                    sys.stderr.flush()
                    # Re-execute the current script with the same arguments
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                except Exception as e:
                    logger.error(f"Reload Failed: {e}")
                    Config.RELOAD_SIGNAL = False

            # Wait for event
            event = bus.get(timeout=1.0) 
            
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
            
            # 1. Update Memory
            if event.type == EventType.BRAIN_OBSERVATION:
                memory.add_observation(event.payload)
            elif event.type == EventType.USER_COMMAND:
                memory.add_observation(f"USER: {event.payload}")
            elif event.type == EventType.FILE_CHANGE:
                memory.add_observation(f"FS: {event.payload}")
            elif event.type == EventType.SYSTEM_ERROR:
                memory.add_observation(f"ERROR: {event.payload}")

            # 2. Snapshot
            snapshot = ContextSnapshot(
                environment={"cwd": os.getcwd()},
                system_state={"active_objective": memory.active_objective},
                short_term_memory=memory.short_term_observations[-10:]
            )
            memory.save_snapshot(snapshot)

            # 3. Brain Processing
            if event.type in [EventType.USER_COMMAND, EventType.FILE_CHANGE, EventType.IDLE, EventType.SYSTEM_CONTROL]:
                intents = brain.think(memory)
                for intent in intents:
                    # Execute Reflex
                    obs = handle_reflex(intent)
                    if obs:
                        bus.put(Event.observation(obs))
                        
    except KeyboardInterrupt:
        print("\nWAH Kernel Stopping...")
        logger.info("WAH Kernel Stopped by User")
