# Rollback Procedures and Crash Handling Guide

## 1. Code Rollback Procedures

Since WAH operates with a `GitSensor`, the primary mechanism for rolling back buggy code is via Git.

### Procedure:
1. **Identify the Bad Commit**: Check `wah.log` or git history to find the commit causing instability.
2. **Revert**:
   - If the system is still running: Issue a shell command or use git tools to `git revert <commit_hash>`.
   - If the system is down: Manually perform `git revert` or `git reset --hard <previous_hash>` in the terminal.
3. **Verification**: The `GitSensor` will detect the file changes. If Hot Reload is active, it may attempt to reload. If the system was down, restart it.

## 2. Handling Runtime Crashes

### Architecture Safety
- **Global Exception Handling**: The `life_loop` in `system/main.py` is wrapped in a `try...except` block to catch unhandled exceptions, log them, and prevent immediate termination where possible.
- **Reflex Safety**: The `handle_reflex` function validates commands (e.g., checking file existence before execution) to prevent shell-induced crashes.

### Recovery Steps
1. **Check Logs**: Tail `wah.log` to see the stack trace.
2. **Hot Fix**: Apply a fix to the code. The `GitSensor` or `FileIntentSensor` will pick it up.
3. **Restart**: If the kernel panicked and exited, restart the process (e.g., `python3 wah.py`).

## 3. Hot Reload Safety

With the introduction of Hot Reload:
- **State Persistence**: Before reloading, Memory dumps its state to `memory_dump.json`.
- **Restoration**: On restart (or reload completion), Memory restores observations from the dump.
- **Failure Mode**: If a reload introduces a syntax error, the Python process may crash. Upon manual restart, the system will boot fresh but can still recover context from the `memory_dump.json` if it exists.
