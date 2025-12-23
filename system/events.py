from dataclasses import dataclass, field
from typing import Any, Dict
import time
from enum import Enum, auto

class EventType(Enum):
    USER_COMMAND = auto()    # User Input
    FILE_CHANGE = auto()     # FS Change
    SYSTEM_ERROR = auto()    # Error
    BRAIN_OBSERVATION = auto() # Brain Output
    TICK = auto()            # Heartbeat
    IDLE = auto()            # Idle
    SYSTEM_CONTROL = auto()  # Reload/Shutdown

@dataclass(order=True)
class Event:
    priority: int
    type: EventType = field(compare=False)
    payload: Any = field(compare=False)
    source: str = field(compare=False, default="system")
    timestamp: float = field(compare=False, default_factory=time.time)

    @staticmethod
    def user(command: str) -> 'Event':
        return Event(priority=100, type=EventType.USER_COMMAND, payload=command, source="user")

    @staticmethod
    def file_change(path: str, change_type: str) -> 'Event':
        return Event(priority=50, type=EventType.FILE_CHANGE, payload={"path": path, "change": change_type}, source="fs")
    
    @staticmethod
    def error(msg: str) -> 'Event':
        return Event(priority=999, type=EventType.SYSTEM_ERROR, payload=msg, source="kernel")
    
    @staticmethod
    def observation(content: str) -> 'Event':
        return Event(priority=80, type=EventType.BRAIN_OBSERVATION, payload=content, source="reflex")
