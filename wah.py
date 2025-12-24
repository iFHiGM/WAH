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
    
    # We pipe stderr to a file so we can read it if it crashes,
    # but we don't pipe stdout so the user can interact with the shell normally.
    err_file = os.path.join(WAH_HOME, f"stderr_{os.getpid()}.tmp")
    
    print(f"🌱 BODY: Pulse -> {target_dir} {' '.join(args)}")
    
    start_time = time.time()
    try:
        with open(err_file, "w") as f_err:
            # Popen allows us to wait and get the exit code
            proc = subprocess.Popen(
                cmd,
                stderr=f_err,       # Capture stderr to file
                stdout=None,        # Inherit stdout (Interactive Shell works)
                stdin=None,         # Inherit stdin (Keyboard works)
                cwd=os.getcwd(),    # Run from project root
                env=os.environ.copy()
            )
            proc.wait()
            
        exit_code = proc.returncode
        
        # Read stderr only if needed
        stderr_content = ""
        if exit_code != 0:
            if os.path.exists(err_file):
                with open(err_file, "r", encoding='utf-8', errors='replace') as f:
                    stderr_content = f.read()
            # If it crashed, print stderr to console too so user sees it
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
            except:
                pass

    duration = time.time() - start_time
    return exit_code, stderr_content

def atomic_promote():
    """
    The Evolution Step.
    Swaps system_incubator -> system.
    """
    print("🧬 BODY: Evolution Approved. Initiating DNA Swap...")
    
    try:
        # 1. Backup Stable (if exists)
        if os.path.exists(SYSTEM_DIR):
            if os.path.exists(BACKUP_DIR):
                shutil.rmtree(BACKUP_DIR)
            # Use copytree for backup (safer than move)
            shutil.copytree(SYSTEM_DIR, BACKUP_DIR)
        
        # 2. Remove Stable
        shutil.rmtree(SYSTEM_DIR)
        
        # 3. Promote Incubator
        # We rename the directory. This is usually atomic on POSIX.
        os.rename(INCUBATOR_DIR, SYSTEM_DIR)
        
        print("🦋 BODY: Metamorphosis Complete.")
        return True
    except Exception as e:
        print(f"💥 BODY: Critical Failure during promotion: {e}")
        # Try to restore from backup
        if os.path.exists(BACKUP_DIR) and not os.path.exists(SYSTEM_DIR):
            print("🚑 BODY: Restoring from backup...")
            shutil.copytree(BACKUP_DIR, SYSTEM_DIR)
        return False

def main():
    ensure_dirs()
    
    print("=== THE PHOENIX PROTOCOL (v2.0) ===")
    
    while True:
        # --- PHASE 1: RUN STABLE SOUL ---
        exit_code, stderr = run_kernel(SYSTEM_DIR)
        
        # --- PHASE 2: DECIDE FATE ---
        if exit_code == 0:
            print("💤 BODY: Soul Sleep. (System Stopped)")
            break
            
        elif exit_code == EXIT_EVOLUTION:
            print(f"🥚 BODY: Evolution Request Received (Exit {EXIT_EVOLUTION}).")
            
            if not os.path.exists(INCUBATOR_DIR):
                print("⚠️ BODY: Evolution requested but no incubator found! Restarting Stable.")
                continue
                
            # --- PHASE 3: THE TRIAL ---
            print("⚔️ BODY: Starting The Trial (Test Mode)...")
            # We assume Level 1 accepts '--test' to run self-checks and exit(0) on success
            test_code, test_err = run_kernel(INCUBATOR_DIR, ["--test"])
            
            if test_code == 0:
                # --- PHASE 4: PROMOTION ---
                if atomic_promote():
                    print("✨ BODY: Restarting with new Soul...")
                    continue
                else:
                    print("💀 BODY: Promotion failed. Reverting to old Soul.")
            else:
                # --- PHASE 5: REJECTION ---
                print(f"🔥 BODY: The Trial Failed (Exit {test_code}).")
                log_trauma("incubator_trial", test_code, test_err)
                print("♻️ BODY: Reverting to Stable Soul.")
                # We do NOT promote. We restart the loop, which runs SYSTEM_DIR (Stable).
                
        else:
            # --- PHASE 6: RESURRECTION ---
            print(f"💥 BODY: Soul Crashed (Exit {exit_code}).")
            log_trauma("stable_crash", exit_code, stderr)
            print("🚑 BODY: Reviving Stable Soul in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    main()
