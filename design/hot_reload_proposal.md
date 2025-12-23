# Hot Reload Proposal: Graceful Process Restart

## Problem
Python's `importlib.reload` is notoriously unstable for complex applications involving:
- Active Threads (Sensors)
- Event Loops
- Singletons (EventBus, Memory)

Reloading modules often leaves old object references alive, leading to subtle bugs (e.g., two EventBuses, old sensors feeding new logic).

## Solution: Process Replacement (`os.execv`)
Instead of reloading modules in-memory, we will replace the entire running process with a new instance of itself. This guarantees a clean state while preserving the "session" via external persistence.

## Implementation Plan

### 1. Event Trigger
- **Event**: `EventType.SYSTEM_CONTROL` (or new `RELOAD`)
- **Payload**: `"RELOAD"`

### 2. Handling in `system/main.py`
Modify the `life_loop` to handle the reload request:

```python
elif event.type == EventType.SYSTEM_CONTROL and event.payload == "RELOAD":
    logger.info("SYSTEM: Initiating Hot Reload...")
    
    # 1. Cleanup
    for s in sensors:
        s.stop()
        s.join(timeout=1.0)
    
    # 2. Persist State
    # (Memory.active_objective is already on disk)
    # (Optional: Dump short-term memory to .wah/memory_dump.json to restore context)
    
    # 3. Restart
    python = sys.executable
    os.execl(python, python, *sys.argv)
```

### 3. State Persistence
- Ensure `Memory` loads `active_objective` on startup (Already implemented).
- **Enhancement**: Serialize `short_term_observations` to disk before reload and load them back on startup. This preserves the "Stream of Consciousness" so the bot remembers *why* it reloaded.

## Pros/Cons
- **Pros**: 100% Clean state, handles code changes in `main.py` and `wah.py`, no memory leaks.
- **Cons**: Slight downtime (approx 1-2s), loses in-memory variables not saved to disk.
