from typing import List, Optional, Dict
from what.schema import ContextSnapshot
from system.config import Config
import time
import os
import json
from system.logger import get_logger

logger = get_logger()

class Memory:
    """
    Memory (Hippocampus)
    Responsible for storing Short-Term Memory (Observations) and Context Snapshots.
    """
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.snapshots: List[ContextSnapshot] = []
        self.short_term_observations: List[str] = [] 
        self.active_objective: Optional[str] = None
        self._load_objective()
        self._restore_state()

    def _load_objective(self):
        """Load active objective from disk if exists."""
        if os.path.exists(Config.OBJECTIVE_FILE):
            try:
                with open(Config.OBJECTIVE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.active_objective = content
            except Exception:
                pass

    def set_objective(self, objective: str):
        self.active_objective = objective
        try:
            with open(Config.OBJECTIVE_FILE, 'w', encoding='utf-8') as f:
                f.write(objective)
        except Exception:
            pass

    def clear_objective(self):
        self.active_objective = None
        if os.path.exists(Config.OBJECTIVE_FILE):
            try:
                os.remove(Config.OBJECTIVE_FILE)
            except Exception:
                pass

    def save_snapshot(self, snapshot: ContextSnapshot):
        self.snapshots.append(snapshot)
        if len(self.snapshots) > 40:
            self.snapshots.pop(0)

    def add_observation(self, observation: str):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        entry = f"[{timestamp}] {observation}"
        self.short_term_observations.append(entry)
        if len(self.short_term_observations) > self.capacity:
            self.short_term_observations.pop(0)

    def get_context(self) -> Dict:
        return {
            "objective": self.active_objective,
            "recent_observations": self.short_term_observations[-15:],
            "history_count": len(self.short_term_observations)
        }

    def _restore_state(self):
        """Restore short-term memory from dump if exists (after hot reload)."""
        dump_file = getattr(Config, 'MEMORY_DUMP_FILE', os.path.join(Config.WAH_HOME, 'memory_dump.json'))
        if os.path.exists(dump_file):
            try:
                with open(dump_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.short_term_observations = data.get("short_term_observations", [])
                os.remove(dump_file)
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                self.short_term_observations.append(f"[{timestamp}] SYSTEM: Memory restored after Hot Reload.")
                logger.info("Memory restored from dump.")
            except Exception as e:
                logger.error(f"Failed to restore memory: {e}")

    def dump_state(self):
        """Persist short-term memory to disk before hot reload."""
        dump_file = getattr(Config, 'MEMORY_DUMP_FILE', os.path.join(Config.WAH_HOME, 'memory_dump.json'))
        try:
            data = {
                "short_term_observations": self.short_term_observations
            }
            with open(dump_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            logger.info(f"Memory state dumped to {dump_file}")
        except Exception as e:
            logger.error(f"Failed to dump memory state: {e}")
