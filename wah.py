#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import shutil
import json
from datetime import datetime

# --- PHOENIX PROTOCOL: LEVEL 0 (THE BODY) ---
# This file is the immutable Supervisor.
# It does NOT think. It does NOT fix code.
# It only manages the lifecycle of the Soul (system/) and the Embryo (system_incubator/).

WAH_HOME = ".wah"
SYSTEM_DIR = "system"
INCUBATOR_DIR = "system_incubator"
BACKUP_DIR = "system_last_good"
TRAUMA_LOG = os.path.join(WAH_HOME, "trauma.log")
EXIT_EVOLUTION = 100  # Magic code for "I want to evolve"

def ensure_dirs():
    if not os.path.exists(WAH_HOME):
        os.makedirs(WAH_HOME)

def log_trauma(source, exit_code, stderr_content):
    """Records the cause of death for the next Soul to analyze."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "exit_code": exit_code,
        "stderr": stderr_content[-4000:] if stderr_content else "No stderr captured"
    }
    try:
        with open(TRAUMA_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
        print(f"💀 BODY: Trauma recorded to {TRAUMA_LOG}")
    except Exception as e:
        print(f"💀 BODY: Failed to log trauma: {e}")

def run_kernel(target_dir, args=[]):
    """
    Runs the kernel in a separate process (ISOLATION).
    Returns (exit_code, stderr_content).
    """
    entry_point = os.path.join(target_dir, "main.py")
    if not os.path.exists(entry_point):
        return -1, f"Entry point not found: {entry_point}"

    cmd = [sys.executable, entry_point] + args
    
    err_file = os.path.join(WAH_HOME, f"stderr_{os.getpid()}.tmp")
    
    print(f"🌱 BODY: Pulse -> {target_dir} {' '.join(args)}")
    
    start_time = time.time()
    try:
        with open(err_file, "w") as f_err:
            proc = subprocess.Popen(
                cmd,
                stderr=f_err,       # Capture stderr
                stdout=None,        # Inherit stdout
                stdin=None,         # Inherit stdin
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            proc.wait()
            
        exit_code = proc.returncode
        
        stderr_content = ""
        if exit_code != 0:
            if os.path.exists(err_file):
                with open(err_file, "r", encoding='utf-8', errors='replace') as f:
                    stderr_content = f.read()
            # Suppress crash log printing if it's an intentional evolution exit
            if exit_code != EXIT_EVOLUTION:
                print(f"\n🔥 CRASH LOG:\n{stderr_content}")
                
    except KeyboardInterrupt:
        print("\n🛑 BODY: User Interrupt.")
        exit_code = 0
        stderr_content = ""
    except Exception as e:
        exit_code = -1
        stderr_content = str(e)
    finally:
        if os.path.exists(err_file):
            try:
                os.remove(err_file)
            except: pass

    return exit_code, stderr_content

def main():
    ensure_dirs()
    print("=== THE PHOENIX PROTOCOL (v2.1: Swap-Test) ===")
    
    while True:
        # --- PHASE 1: RUN STABLE SOUL ---
        exit_code, stderr = run_kernel(SYSTEM_DIR)
        
        # --- PHASE 2: DECIDE FATE ---
        if exit_code == 0:
            print("💤 BODY: Soul Sleep. (System Stopped)")
            break
            
        elif exit_code == EXIT_EVOLUTION:
            print(f"🥚 BODY: Evolution Request Received.")
            
            if not os.path.exists(INCUBATOR_DIR):
                print("⚠️ BODY: No incubator found! Restarting Stable.")
                continue
            
            # --- PHASE 3: THE SWAP-TEST ---
            print("🧪 BODY: Swapping system for Trial...")
            
            # Clean previous backup
            if os.path.exists(BACKUP_DIR):
                shutil.rmtree(BACKUP_DIR)

            try:
                # 1. Stable -> Backup
                os.rename(SYSTEM_DIR, BACKUP_DIR)
                # 2. Incubator -> Stable (The Candidate becomes The System)
                os.rename(INCUBATOR_DIR, SYSTEM_DIR)
            except OSError as e:
                print(f"💥 BODY: Swap failed: {e}. Attempting rollback...")
                if os.path.exists(BACKUP_DIR) and not os.path.exists(SYSTEM_DIR):
                    os.rename(BACKUP_DIR, SYSTEM_DIR)
                continue

            print("⚔️ BODY: Starting The Trial (in-place)...")
            test_code, test_err = run_kernel(SYSTEM_DIR, ["--test"])
            
            if test_code == 0:
                # --- PHASE 4: COMMIT ---
                print("✨ BODY: Trial Passed. Evolution Confirmed.")
                # We stay as 'system'. The old system is in 'system_last_good'.
            else:
                # --- PHASE 5: REVERT ---
                print(f"🔥 BODY: Trial Failed (Exit {test_code}). Reverting...")
                log_trauma("evolution_trial", test_code, test_err)
                
                # Move the bad candidate back to incubator (so Soul can inspect it)
                if os.path.exists(INCUBATOR_DIR):
                    shutil.rmtree(INCUBATOR_DIR)
                os.rename(SYSTEM_DIR, INCUBATOR_DIR)
                
                # Restore Backup -> System
                os.rename(BACKUP_DIR, SYSTEM_DIR)
                
        else:
            # --- PHASE 6: RESURRECTION ---
            print(f"💥 BODY: Soul Crashed (Exit {exit_code}).")
            log_trauma("stable_crash", exit_code, stderr)
            print("🚑 BODY: Reviving Stable Soul in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    main()