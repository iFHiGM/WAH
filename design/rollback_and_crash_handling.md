# Safety Procedures: Code Rollback & Crash Handling

## 1. Code Rollback Procedures

When a deployment introduces critical bugs, immediate rollback is the first line of defense.

### Git-Based Rollback
- **Revert Commit**: `git revert <commit_hash>` (Preferred). Creates a new commit that undoes changes, preserving history.
- **Reset Hard**: `git reset --hard <previous_hash>` (Emergency only). Destructive to history; use only if the branch is not shared or if strictly necessary.
- **Checkout Previous**: `git checkout <previous_tag>` to detach HEAD and run a known good state.

### Strategy
1. **Identify**: Monitor logs (`wah.log`) for `SYSTEM_ERROR` or crash loops.
2. **Isolate**: Stop the running kernel if necessary.
3. **Revert**: Apply the revert via Git.
4. **Verify**: Run tests (`tests/`) to ensure stability.
5. **Redeploy**: Restart the kernel.

## 2. Handling Runtime Crashes

Runtime crashes require a robust architecture to minimize data loss and downtime.

### Self-Healing Mechanisms

#### A. Hot Reload (Implemented)
Instead of a full crash-and-restart cycle, the system can trigger a **Hot Reload**:
1. **Detection**: The system detects a critical error or receives a reload signal.
2. **Persistence**: The `Memory` module dumps the current state (Short-Term Memory, Active Objective) to `memory_dump.json`.
3. **Restart**: The process restarts (or re-imports modules).
4. **Restoration**: On boot, `Memory` checks for `memory_dump.json` and restores the context, maintaining continuity.

#### B. Supervisor Process (Recommended)
Run the kernel under a supervisor (e.g., `supervisord`, `systemd`, or a simple shell loop) that automatically restarts the process if it exits with a non-zero code.

```bash
# Simple Supervisor Loop
while true; do
    python3 -m system.main
    echo "Kernel crashed. Restarting in 5s..."
    sleep 5
done
```

### Best Practices
- **State Persistence**: Always persist critical state (Objectives, Context) to disk (SQLite/JSON) to survive crashes.
- **Graceful Shutdown**: Handle `SIGINT`/`SIGTERM` to flush buffers and close handles.
- **Error Boundaries**: Wrap main loops in `try...except` blocks to catch unhandled exceptions and log them before exiting.
