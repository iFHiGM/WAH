# Proposal: Safe Hot Reload via Supervisor Pattern

## 1. The Problem
Currently, WAH runs as a single Python process. Modifying core files (like `system/main.py` or `system/brain.py`) requires a manual restart because Python caches imported modules. `importlib.reload` is risky for complex stateful systems.

## 2. The Solution: Supervisor Architecture
We separate the **Runner** (Supervisor) from the **Kernel** (Worker).

### Architecture
1. **Supervisor (`wah.py`)**: 
   - A lightweight wrapper that runs the Kernel as a subprocess.
   - Monitors the exit code of the Kernel.
2. **Kernel (`system/main.py`)**: 
   - The actual logic (Brain, Senses, Reflex).
   - Can terminate itself with specific exit codes to signal the Supervisor.

### Protocol (Exit Codes)
- **0**: Shutdown (User requested stop).
- **1**: Crash (Supervisor logs error, waits 5s, then restarts).
- **42**: **Hot Reload** (Supervisor restarts Kernel immediately).

## 3. State Persistence ("Hibernation")
To make the reload "seamless", the Kernel must preserve its short-term memory.

- **On Reload (Exit 42)**: 
  - `Memory` serializes `short_term_observations` and `snapshots` to `.wah/hibernation.pkl`.
- **On Startup**:
  - `Memory` checks for `.wah/hibernation.pkl`.
  - If found, it restores the state and deletes the file.
  - This creates an illusion of continuous consciousness.

## 4. Implementation Plan
1. **Modify `wah.py`**: Convert it into the Supervisor loop.
2. **Update `system/main.py`**: Ensure it runs correctly as a module (`python -m system.main`).
3. **Update `system/memory.py`**: Add `hibernate()` and `wakeup()` methods.
4. **Update `system/reflex.py`**: Add a handler for the `system.reload` intent that triggers `sys.exit(42)`.

## 5. Safety Mechanisms
- **Boot Loop Detection**: If the Kernel crashes within 5 seconds of starting more than 3 times, the Supervisor stops to prevent log spam.
