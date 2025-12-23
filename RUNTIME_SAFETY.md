# Runtime Safety & Rollback Procedures

## 1. Code Rollback Strategy
Since the WAH kernel operates on a Git-based filesystem, rolling back buggy code is straightforward but requires caution to preserve context.

### Procedures:
- **Identify the Faulty Commit**: Check `wah.log` or `git log` to find the commit that introduced the instability.
- **Safe Revert (Recommended)**: Use `git revert HEAD` to create a new commit that undoes the changes. This preserves the history of the error and the fix.
- **Hard Reset (Emergency Only)**: Use `git reset --hard <commit_hash>` only if the recent history is irrelevant or corrupted. **Warning**: This erases recent memory/observations stored in files if not committed.

## 2. Handling Runtime Crashes
Runtime crashes can occur due to syntax errors in dynamically generated code or resource exhaustion.

### Mitigation Strategies:
- **Memory Persistence**: The `Memory` module is designed to dump its state (Short-Term Memory) to `memory_dump.json` upon detecting a reload signal or graceful termination. On restart, it checks for this file to restore context.
- **Exception Isolation**: The `Reflex` loop wraps execution in try/except blocks. If a tool fails, it logs the error rather than crashing the kernel.
- **Hot Reloading**: Instead of a full crash, the system supports reloading specific modules (e.g., `system.config`) to apply fixes without losing the process state.

### Recovery Steps:
1. Check `wah.log` for the stack trace.
2. If the crash is due to a specific file (e.g., `system/memory.py`), fix the syntax error externally or via a safe-mode script.
3. Restart the kernel. It will attempt to load `memory_dump.json` to resume the session.