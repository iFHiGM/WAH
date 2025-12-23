# Runtime Safety and Recovery Procedures

This document outlines the protocols for ensuring system stability, rolling back buggy code, and handling runtime crashes within the WAH Kernel environment.

## 1. Code Rollback Procedures

Since the WAH Kernel operates directly on its own source code, maintaining a clean Git history is critical for safety.

### Safety Protocol
- **Pre-Change Commit**: The kernel automatically commits changes before applying new edits. Ensure this protocol is strictly followed to create save points.
- **Verification**: After writing a file, the kernel must read it back to verify integrity.

### Rollback Methods
If a deployment (file write) introduces a bug:

1. **Identify the Last Stable State**:
   ```bash
   git log --oneline -n 10
   ```

2. **Revert (Preferred)**:
   Create a new commit that undoes the changes. This preserves history.
   ```bash
   git revert HEAD
   ```

3. **Hard Reset (Emergency Only)**:
   If the local state is corrupted and history preservation is not a concern for the latest tip:
   ```bash
   git reset --hard <commit_hash>
   ```
   *Warning: This discards all uncommitted changes.*

## 2. Handling Runtime Crashes

Runtime crashes can occur due to syntax errors, logic bugs, or resource exhaustion.

### The Hot Reload Mechanism
WAH implements a Self-Correction/Hot Reload mechanism to handle recoverable errors without losing context.

1. **Trigger**: A `RELOAD_SIGNAL` in `system.config` or a specific `Intent` can trigger a reload.
2. **State Persistence**: Before shutting down, the `Memory` module dumps short-term observations to `memory_dump.json`.
3. **Restoration**: On restart, `Memory` checks for this dump and restores the context, allowing the kernel to "remember" why it crashed or reloaded.

### Recovery from Fatal Crashes
If the kernel crashes completely (process exit):

1. **Analyze Logs**:
   Check `wah.log` for the traceback.
   ```bash
   tail -n 50 .wah/wah.log
   ```

2. **Fix or Revert**:
   - If the error is obvious (e.g., SyntaxError), fix the file using an external editor or a recovery script.
   - If the cause is complex, perform a Git Rollback (see Section 1).

3. **Manual Restart**:
   Execute the entry point script.
   ```bash
   python wah.py
   ```

### Infinite Loops
If the kernel becomes unresponsive:
1. Send `SIGINT` (Ctrl+C) to the running process.
2. The `EventBus` and `Brain` should handle the interruption gracefully, but if not, force kill and restart.
