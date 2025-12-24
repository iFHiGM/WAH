import sys
import os
import shutil
import time
import unittest
from contextlib import contextmanager

# Add root to path so we can import wah
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import wah

class TestPhoenixProtocol(unittest.TestCase):
    
    def setUp(self):
        # Setup temporary directories for testing
        self.test_dir = "tests/phoenix_sandbox"
        self.stable_dir = os.path.join(self.test_dir, "system")
        self.incubator_dir = os.path.join(self.test_dir, "system_incubator")
        self.backup_dir = os.path.join(self.test_dir, "system_last_good")
        self.log_file = os.path.join(self.test_dir, "trauma.log")
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.stable_dir)
        os.makedirs(self.test_dir + "/.wah") # For logs

        # Mock global config in wah module for paths
        wah.WAH_HOME = self.test_dir + "/.wah"
        wah.SYSTEM_DIR = self.stable_dir
        wah.INCUBATOR_DIR = self.incubator_dir
        wah.BACKUP_DIR = self.backup_dir
        wah.TRAUMA_LOG = self.log_file

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_mock_kernel(self, directory, content, filename="main.py"):
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, filename), "w") as f:
            f.write(content)

    def test_run_kernel_success(self):
        """Test that a healthy kernel exits 0."""
        code = """
import sys
print("Healthy Kernel")
sys.exit(0)
"""
        self.create_mock_kernel(self.stable_dir, code)
        exit_code, stderr = wah.run_kernel(self.stable_dir)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")

    def test_run_kernel_crash(self):
        """Test that a broken kernel returns non-zero and captures stderr."""
        code = """
import sys
raise ValueError("Intentional Crash")
"""
        self.create_mock_kernel(self.stable_dir, code)
        exit_code, stderr = wah.run_kernel(self.stable_dir)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Intentional Crash", stderr)

    def test_run_kernel_syntax_error(self):
        """Test that SyntaxError is caught (Dead on Arrival)."""
        code = "def broken_code(:" # Missing paren
        self.create_mock_kernel(self.stable_dir, code)
        exit_code, stderr = wah.run_kernel(self.stable_dir)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("SyntaxError", stderr)

    def test_atomic_promote(self):
        """Test directory swapping logic."""
        # Setup: Stable has v1, Incubator has v2
        self.create_mock_kernel(self.stable_dir, "print('v1')")
        self.create_mock_kernel(self.incubator_dir, "print('v2')")
        
        # Verify initial state
        self.assertTrue(os.path.exists(self.stable_dir))
        
        # Execute Promotion
        success = wah.atomic_promote()
        
        self.assertTrue(success)
        
        # Verify Stable is now v2
        with open(os.path.join(self.stable_dir, "main.py")) as f:
            content = f.read()
            self.assertIn("v2", content)
            
        # Verify Backup is v1
        self.assertTrue(os.path.exists(self.backup_dir))
        with open(os.path.join(self.backup_dir, "main.py")) as f:
            content = f.read()
            self.assertIn("v1", content)

    def test_trauma_logging(self):
        """Test error logging."""
        wah.log_trauma("test_src", 99, "Error details")
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file) as f:
            log_content = f.read()
            self.assertIn("test_src", log_content)
            self.assertIn("99", log_content)

if __name__ == '__main__':
    unittest.main()
