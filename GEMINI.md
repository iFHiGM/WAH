# WAH (What-And-How) Project Context

## 1. Status: Phase 3 (Self-Learning Kernel)
*   **Era**: The Creation (Self-Programming verified, Lisp Bridge pending).
*   **Governance**: User confirmation required for major state transitions.

## 2. Architecture & Capabilities

### The Phoenix Protocol (Self-Evolution Architecture)
*   **The Body (`wah.py`)**: Immutable Watchdog (PID 1).
    *   **Role**: Process Manager & Isolation.
    *   **Responsibility**: Launches `system/main.py`. If it crashes, restarts it. If it signals evolution (Exit 100), tests `system_incubator/` and atomically promotes it if successful.
*   **The Soul (`system/`)**: Intelligent Kernel.
    *   **Role**: Business Logic & Evolution Driver.
    *   **Responsibility**: Modifies code in `system_incubator/`, signals evolution, and reflects on `trauma.log` (crash reports) to learn from failed mutations.
*   **The Womb (`system_incubator/`)**: Staging Area.
    *   **Role**: Test Flight.
    *   **Mechanism**: New code must survive a "Trial of Life" (test mode) here before replacing The Soul.

### The Brain (Stateless Cognition)
*   **Models**: 
    *   **Heavy**: `gemini-3-pro-preview` / `gemini-2.5-pro` (Verified).
    *   **Fast**: `gemini-3-flash-preview` / `gemini-2.5-flash` (Verified).
*   **Context Strategy**: 
    *   **Stateless**: No server-side session history.
    *   **Context Window**: Managed client-side by `system/memory.py`.
    *   **Persistence**: 
        *   `Active Objective` stored in `.wah/active_objective`.
        *   Resilient to restarts and crashes.

### The Subconscious (Idle Architecture)
*   **Idle Detection**: System detects inactivity (5s timeout).
*   **Self-Reflection**: Checks `.wah/lessons_learned.org` during idle time.
*   **Auto-Evolution**: Can trigger internal `SYSTEM_INTERNAL` commands to digest lessons and patch code autonomously.
*   **Circuit Breaker**: Prevents infinite loops when tasks are completed.

### The Reflex (Protected Limbs)
*   `how/fs.py`: **Hard-coded protection** for `GENESIS.org` and `README.org`. Attempts to modify them will raise `PermissionError`.
*   **Runtime Storage**: All temporary state files are confined to `.wah/`.

## 3. Usage
```bash
./wah.py
# wah> ...
# tail -f wah.log
```

## 4. Conventions
*   **Immutable**: `GENESIS.org`, `README.org` (Enforced by Code).
*   **Dynamic**: `PLAN.org`, `GEMINI.md`.