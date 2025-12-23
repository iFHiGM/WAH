# Analysis of Repetitive Behavior

## Diagnosis
The system exhibits a **Self-Sustaining Feedback Loop** inherent in the event-driven architecture defined in `system/main.py`.

## Mechanism
1. **Trigger**: When an Intent is executed (e.g., `chat.reply`), `handle_reflex` returns an observation string.
2. **Event**: This observation is published to the `EventBus` as `EventType.BRAIN_OBSERVATION`.
3. **Reaction**: In `life_loop`, receiving a `BRAIN_OBSERVATION` triggers a check:
   ```python
   if memory.active_objective:
       # ...
       intents = brain.think(snapshot, None, memory.active_objective)
   ```
4. **Loop**: If the `active_objective` is not cleared, the Brain receives the observation of its own previous action and is immediately asked to "Continue with current objective".
5. **Result**: Without explicit termination logic, the Brain interprets "Continue" as a directive to repeat the action or perform the next step immediately, leading to rapid-fire repetition (e.g., multiple greetings or endless investigation loops).

## Evidence
- **Logs**: `wah.log` shows millisecond-level cycles of `ACT` -> `Reflex` -> `Brain Solver` -> `ACT`.
- **Code**: `system/main.py` explicitly links Observation events to `brain.think` whenever an objective exists.

## Solution
To prevent loops, the Brain **MUST** explicitly use `system.clear_objective()` immediately upon completing the intended task. The system relies on the intelligence of the kernel to break the loop.