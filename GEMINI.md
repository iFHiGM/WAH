# WAH (What-And-How) Project Context

## 1. Project Overview
**WAH** is an experimental autonomous operating system kernel designed to simulate a digital life form. It is built upon the "What-And-How" philosophy, where the system is divided into **Perception (WHAT)**, **Execution (HOW)**, and **Connection/Cognition (AND/System)**.

The project aims to evolve from a set of static scripts into a self-programming, resilient digital entity that can "sense" its environment (e.g., Git status, user commands) and "act" upon it (e.g., auto-commits, writing its own code).

### Core Philosophy
*   **System as Master**: The Python kernel (`system/`) is the absolute ruler. It runs the physics and life loop.
*   **AI as Worker**: LLMs (Gemini) are "cognitive plug-ins" or "batteries" used to generate Intents when instincts (Reflexes) fail.
*   **Cognitive Crystallization**: The goal is to turn "Thought" (AI reasoning) into "Reflex" (Code/`how` modules).

## 2. Architecture

The codebase follows a strict biological metaphor:

### `what/` (The Senses)
*   **Purpose**: Defines data structures and sensors.
*   **Key Files**:
    *   `schema.py`: Defines `ContextSnapshot` (state) and `Intent` (desire).
    *   `senses.py`: Sensors for the environment (e.g., `GitSensor` for file changes, `IntentSensor` for user commands).

### `how/` (The Limbs)
*   **Purpose**: Atomic execution capabilities.
*   **Key Files**:
    *   `shell.py`: Basic shell execution wrapper.
    *   `git.py`: Git operations.
    *   `lib/`: Directory for dynamically generated capabilities.
*   **Dynamic Nature**: This directory is designed to be populated by the system itself (Self-programming).

### `system/` (The Master / AND)
*   **Purpose**: The central processing unit and life loop.
*   **Key Files**:
    *   `main.py`: The entry point. Runs the `While True` Life Loop (Sense -> Think -> Act).
    *   `brain.py`: The cognitive interface. Connects to **Vertex AI (Gemini-3-Pro)** or falls back to a Mock mode.
    *   `reflex.py`: The spinal cord. Executes `Intents` directly. Supports **Hot-Reloading** of Python modules.
    *   `physics.py`: Safety guardrails (e.g., preventing `rm -rf /`).
    *   `memory.py`: Short-term memory (RAM snapshots).

## 3. Setup & Usage

### Prerequisites
*   Python 3.x
*   (Optional) `google-cloud-aiplatform`: For real AI capabilities.
    ```bash
    pip install google-cloud-aiplatform
    ```
*   (Optional) `GOOGLE_CLOUD_PROJECT`: Environment variable set to your GCP project ID.

### Running the System
Start the life loop:
```bash
python3 system/main.py
```

### Interacting with WAH
WAH listens for "thoughts" or "commands" via the filesystem.
To issue a command:
```bash
echo "I need a weather module" > intent.txt
```
The system will:
1.  Sense the file.
2.  Process it (Mock or AI).
3.  Execute the intent (e.g., write `how/weather.py`).
4.  Rename `intent.txt` to `intent.txt.<timestamp>.done`.

## 4. Development Status

**Current Era**: Phase 3 (The Creation / Self-Programming) -> Entering Phase 4 (The Transmutation / Emacs Bridge).

*   ✅ **Reflex**: Auto-commits git changes.
*   ✅ **Thought**: Parses natural language via `system/brain.py`.
*   ✅ **Creation**: Can generate and hot-load new python modules in `how/`.
*   🚧 **Transmutation**: Integration with Emacs (Lisp bridge) is the next milestone.

## 5. Key Conventions for Contributors (AI Agents)

1.  **Respect the Loop**: Do not block `system/main.py`. It must cycle to "breathe".
2.  **Atomic Actions**: All new capabilities in `how/` should be stateless functions where possible.
3.  **Hot-Swap Friendly**: `system/reflex.py` uses `importlib.reload`. Ensure modules are reloadable.
4.  **Context Packing**: Use `tools/pack_context.py` to generate a full context dump (`WAH_FULL_CONTEXT.txt`) when migrating between chat sessions.
