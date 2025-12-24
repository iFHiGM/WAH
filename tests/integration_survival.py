import sys
import os
import shutil
import time
import unittest
from contextlib import contextmanager

# Add root to path so we can import wah
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import wah

class TestPhoenixIntegration(unittest.TestCase):
    
    def setUp(self):
        self.sandbox_dir = "tests/phoenix_sandbox_env"
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
        os.makedirs(self.sandbox_dir)
        
        # We need to copy 'system' to 'tests/phoenix_sandbox_env/system'
        # Also copy 'how', 'what', 'system/config.py' dependencies if needed
        # But 'system' is self-contained mostly, except for 'how' and 'what'.
        # To be safe, let's copy the whole repo structure minus .git and .venv
        
        for item in ["system", "how", "what", "wah.py"]:
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(self.sandbox_dir, item))
            else:
                shutil.copy(item, os.path.join(self.sandbox_dir, item))
        
        os.makedirs(os.path.join(self.sandbox_dir, ".wah"))
        
        # Create a fake .env if needed (config loader handles missing env)

    def tearDown(self):
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

    def test_broken_brain_initialization(self):
        """
        Scenario: New Brain has a bug in __init__.
        We simulate the SWAP by placing the broken code in 'system/' inside the sandbox.
        """
        print("\n--- Integration Test: Broken Brain Init ---")
        
        target_system = os.path.join(self.sandbox_dir, "system")
        brain_path = os.path.join(target_system, "brain.py")
        
        with open(brain_path, "r") as f:
            content = f.read()
        
        # Inject error into __init__
        # We append it after "self.api_key = Config.API_KEY"
        # Be careful with indentation
        target = 'self.api_key = Config.API_KEY'
        poison = '\n        raise ValueError("Simulated Brain Damage")' 
        new_content = content.replace(target, target + poison)
        
        with open(brain_path, "w") as f:
            f.write(new_content)
            
        # Run Trial
        print(f"Testing sandbox system at {target_system}...")
        # We must set CWD to sandbox dir so relative imports work if any
        cwd = os.getcwd()
        os.chdir(self.sandbox_dir)
        try:
            # We use wah.run_kernel but pointing to local system
            # Note: wah.run_kernel uses sys.executable which is correct.
            exit_code, stderr = wah.run_kernel("system", ["--test"])
        finally:
            os.chdir(cwd)
        
        print(f"Exit Code: {exit_code}")
        # print(f"Stderr: {stderr}")
        
        self.assertNotEqual(exit_code, 0, "Broken Brain should fail test!")
        self.assertIn("Simulated Brain Damage", stderr)

    def test_valid_evolution(self):
        print("\n--- Integration Test: Valid Evolution ---")
        
        cwd = os.getcwd()
        os.chdir(self.sandbox_dir)
        try:
            exit_code, stderr = wah.run_kernel("system", ["--test"])
        finally:
            os.chdir(cwd)
        
        self.assertEqual(exit_code, 0, "Valid system should pass test!")
        # Success output goes to stdout which we don't capture here, so just check exit code.

if __name__ == '__main__':
    unittest.main()