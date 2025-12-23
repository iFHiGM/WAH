# Safety and Procedures for Code Rollback & Crash Handling

## 1. Code Rollback Procedures
Rolling back code is the primary defense against bad deployments. 

### A. Safe Rollback (Preferred)
Use `git revert` to create a new commit that inverses the changes. This preserves history.
```bash
git log --oneline  # Identify the bad commit hash
git revert <commit_hash>
```

### B. Hard Rollback (Emergency)
Use `git reset` to move the HEAD pointer back. **Warning**: Destroys history after the target commit.
```bash
git reset --hard <last_stable_commit_hash>
```

## 2. Handling Runtime Crashes

### A. Immediate Response
1. **Check Logs**: `tail -n 50 wah.log` to find the traceback.
2. **Isolate**: If the crash is due to a specific input, stop sending that input.

### B. Recovery Mechanisms
1. **Hot Reload (Soft Recovery)**:
   - If the kernel is still responsive but behaving incorrectly, trigger a reload to refresh code modules without losing memory.
   - Command: `system.reload()`
   - *Prerequisite*: The `system/memory.py` must support state persistence (`dump_state`/`restore_state`).

2. **Cold Restart (Hard Recovery)**:
   - If the process terminates, the supervisor (shell loop or systemd) should restart it.
   - The system should attempt to load `memory_dump.json` or the last `ContextSnapshot` to regain situational awareness.

### C. Prevention
- Always verify `system/reflex.py` and `system/main.py` after modification.
- Use `try/except` blocks in the main event loop to catch uncaught exceptions and log them instead of crashing.