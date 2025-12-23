import os
import sys
import json
import time

STATE_FILE = "tests/poc_state.json"

def main():
    if os.path.exists(STATE_FILE):
        print("State file found. Reload successful!")
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
        print(f"Previous state: {data}")
        os.remove(STATE_FILE)
        print("Test Passed.")
    else:
        print("First run. Saving state and reloading...")
        state = {"timestamp": time.time(), "message": "Hello from before reload"}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        print(f"Execv-ing... (PID: {os.getpid()})")
        sys.stdout.flush()
        # Restart this script
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()