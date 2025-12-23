# Investigation Report: Repetitive Behavior

## Diagnosis
The repetitive behavior (loops) observed in the system is caused by the **Feedback Loop mechanism** in `system/main.py`, combined with **State Stagnation** in the Brain's decision-making process.

## Mechanism of the Loop
1. **Trigger**: The system is designed to be autonomous. In `system/main.py`, when a `BRAIN_OBSERVATION` event is processed (which occurs after *any* reflex action), the system checks if there is an `active_objective`.
2. **Auto-Think**: If an objective exists and the event queue is empty, the system immediately triggers `brain.think()` to decide the next step based on the new observation.
3. **Cycle**: `Think` -> `Intent` -> `Action` -> `Observation` -> `Think`.

## Specific Causes of Repetition
### 1. Error Loops (State Stagnation)
- **Observation**: The logs show repeated failures to read `wah.log` (e.g., `tail: cannot open 'wah.log'`).
- **Cause**: The Brain attempted an action, received a failure observation, but failed to update its strategy immediately (e.g., didn't realize the path was `.wah/wah.log` until later). Because the objective was still "Investigate", the Auto-Think mechanism triggered again, and the Brain, seeing the same need, repeated the same (or similar) invalid action.
- **Evidence**: Timestamps `04:17:17` to `04:18:05` show repeated file access attempts and "Shell command is empty" errors.

### 2. Confirmation Loops (Self-Excitation)
- **Observation**: The "Chinese Greeting" loop (`[04:11:50]`, `[04:11:57]`).
- **Cause**: The Brain replied to the user. The `Chat Reply` observation triggered a new `Think`. The Brain, seeing the objective "Verify Chinese" was technically still active, decided to "confirm" the verification by replying again.
- **Resolution**: This loop only broke when the Brain finally decided to issue `system.clear_objective`.

## Conclusion
The system is functioning as designed (continuous autonomous loop), but it is susceptible to looping when the Brain fails to:
1. Recognize a failure state and pivot strategy.
2. Recognize a success state and clear the objective.

## Recommendation
- **Short Term**: Ensure the Brain explicitly clears objectives upon completion.
- **Long Term**: Implement a "Boredom" or "Loop Detection" mechanism in `system/main.py` to pause execution if the same intent is generated repeatedly or if observations don't change significantly.