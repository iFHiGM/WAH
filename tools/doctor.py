#!/usr/bin/env python3
import sys
import os

# Ensure we can import system modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.config import Config
from system.brain import Brain
from how.fs import write_file

def check_env():
    print("=== 1. Environment Check ===")
    if Config.API_KEY:
        print("✅ API Key: Present")
    else:
        print("❌ API Key: Missing")
    
    print(f"🔹 Project: {Config.PROJECT_ID}")
    print(f"🔹 Debug Mode: {Config.DEBUG}")

def check_models():
    print("\n=== 2. Model Configuration ===")
    print(f"🔹 Heavy Model: {Config.MODEL_HEAVY}")
    print(f"🔹 Fast Model:  {Config.MODEL_FAST}")
    
    if Config.MODEL_HEAVY and Config.MODEL_FAST:
        print("✅ Models Configured")
    else:
        print("❌ Models Missing (Run tools/probe_models.py first?)")

def check_protection():
    print("\n=== 3. Safety Protocols ===")
    res = write_file("GENESIS.org", "Attacking...")
    if "Access Denied" in res or "immutable" in res:
        print("✅ Protection ACTIVE: GENESIS.org is immutable.")
    else:
        print(f"❌ Protection FAILED: Result was '{res}'")

def check_brain():
    print("\n=== 4. Brain Connectivity (Ping) ===")
    if not Config.API_KEY:
        print("⏩ Skipping (No API Key)")
        return

    try:
        brain = Brain()
        print(f"🧠 Ping Fast Model ({brain.fast_model})...")
        # 构造一个极简的路由请求
        res = brain._call_api(brain.fast_model, "Ping")
        if res:
            print(f"✅ Fast Model Responded: {len(res)} chars")
        else:
            print("❌ Fast Model Silent")
    except Exception as e:
        print(f"💥 Brain Error: {e}")

if __name__ == "__main__":
    print("🏥 WAH Doctor: System Health Check\n")
    check_env()
    check_models()
    check_protection()
    check_brain()
    print("\n✅ Diagnosis Complete.")
