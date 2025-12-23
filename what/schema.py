from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

@dataclass
class ContextSnapshot:
    """系统实时的状态切片 (Context Snapshot)"""
    timestamp: float = field(default_factory=time.time)
    environment: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    short_term_memory: List[str] = field(default_factory=list)

@dataclass
class Intent:
    """系统的意图 (Intent)"""
    target_module: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)
