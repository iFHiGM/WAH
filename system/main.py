import time
import sys
import os

# Add root to path (Insert at 0 to prioritize local override)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    if "--test" in sys.argv:
        print("🌱 SYSTEM: Running self-test...")
        try:
            # 1. Smoke Test: Try to instantiate core components
            print(".. Checking Infrastructure")
            bus = EventBus()
            print(".. Checking Memory")
            memory = Memory()
            print(".. Checking Brain")
            brain = Brain()
            print("✅ SYSTEM: Self-test passed (Core components initialized).")
            sys.exit(0)
        except Exception as e:
            print(f"❌ SYSTEM: Self-test failed: {e}", file=sys.stderr)
            sys.exit(1)

    print("WAH Kernel Starting... (Tail 'wah.log' for debug info)")
    logger.info("WAH Kernel Session Started")
    
    # 1. Infrastructure
    bus = EventBus()
    memory = Memory()
    brain = Brain() 

    # --- TRAUMA REFLECTION ---
    if os.path.exists(Config.TRAUMA_LOG):
        try:
            with open(Config.TRAUMA_LOG, "r", encoding='utf-8') as f:
                last_trauma = f.readlines()[-1] # Get latest
            memory.add_observation(f"SYSTEM_TRAUMA: Last evolution attempt failed. Details: {last_trauma}")
            # Do NOT remove log yet; let Brain decide when it's learned
            logger.warning("Trauma detected and injected into memory.")
        except:
            pass
    
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
            # --- HOT RELOAD CHECK (Evolution Request) ---
            if Config.RELOAD_SIGNAL:
                logger.info("KERNEL: Reload Signal Detected. Initiating Evolution.")
                print("SYSTEM: Evolution sequence initiated...")
                try:
                    memory.dump_state()
                    sys.stdout.flush()
                    sys.stderr.flush()
                    # Exit with code 100 to signal wah.py to swap directories
                    sys.exit(100)
                except SystemExit:
                    raise
                except Exception as e:
                    logger.error(f"Evolution Exit Failed: {e}")
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
                user_command = None
                if event.type == EventType.USER_COMMAND:
                    user_command = event.payload

                intents = brain.think(snapshot, user_command, memory.active_objective)
                for intent in intents:
                    # Execute Reflex
                    obs = handle_reflex(intent)
                    if obs:
                        bus.put(Event.observation(obs))
                        
    except KeyboardInterrupt:
        print("\nWAH Kernel Stopping...")
        try:
            memory.dump_state()
            print("SYSTEM: Memory state saved.")
        except Exception as e:
            logger.error(f"Failed to save state on shutdown: {e}")
        logger.info("WAH Kernel Stopped by User")

if __name__ == "__main__":
    life_loop()
