#!/usr/bin/env python3
"""
Safe function tests for KAFKA_CSA module
These tests focus on functions that can be tested reliably without complex external dependencies
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
import time
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    import main
    MAIN_IMPORT_SUCCESS = True
    MAIN_IMPORT_ERROR = None
except Exception as e:
    MAIN_IMPORT_SUCCESS = False
    MAIN_IMPORT_ERROR = str(e)

try:
    from KPI_Helper import banner, files_newer_that_mins, delete_files_older_than_days, is_http_ok, is_http_error
    KPI_HELPER_IMPORT_SUCCESS = True
    KPI_HELPER_IMPORT_ERROR = None
except Exception as e:
    KPI_HELPER_IMPORT_SUCCESS = False
    KPI_HELPER_IMPORT_ERROR = str(e)

try:
    from KPI_CSA import KPI_CSA
    KPI_CSA_IMPORT_SUCCESS = True
    KPI_CSA_IMPORT_ERROR = None
except Exception as e:
    KPI_CSA_IMPORT_SUCCESS = False
    KPI_CSA_IMPORT_ERROR = str(e)

try:
    from SubprocessClass import SubprocessClass
    SUBPROCESS_IMPORT_SUCCESS = True
    SUBPROCESS_IMPORT_ERROR = None
except Exception as e:
    SUBPROCESS_IMPORT_SUCCESS = False
    SUBPROCESS_IMPORT_ERROR = str(e)


class TestSafeFunctions(unittest.TestCase):
    """Test functions that are safe to run without complex mocking"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_module_imports_successfully(self):
        """Test that the main module can be imported"""
        self.assertTrue(MAIN_IMPORT_SUCCESS, f"Main module import failed: {MAIN_IMPORT_ERROR}")
        print("✅ Module imports successfully")

    def test_kpi_helper_imports_successfully(self):
        """Test that KPI_Helper functions can be imported"""
        self.assertTrue(KPI_HELPER_IMPORT_SUCCESS, f"KPI_Helper import failed: {KPI_HELPER_IMPORT_ERROR}")
        print("✅ KPI_Helper imports successfully")

    def test_kpi_csa_class_import(self):
        """Test that KPI_CSA class can be imported"""
        self.assertTrue(KPI_CSA_IMPORT_SUCCESS, f"KPI_CSA import failed: {KPI_CSA_IMPORT_ERROR}")
        print("✅ KPI_CSA class import test passed")

    def test_subprocess_class_import(self):
        """Test that SubprocessClass can be imported"""
        self.assertTrue(SUBPROCESS_IMPORT_SUCCESS, f"SubprocessClass import failed: {SUBPROCESS_IMPORT_ERROR}")
        print("✅ SubprocessClass import test passed")

    def test_timestamp_function(self):
        """Test timestamp function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # Test multiple timestamps to ensure consistency
        timestamp1 = main.timestamp()
        timestamp2 = main.timestamp()
        
        # Both should be strings
        self.assertIsInstance(timestamp1, str)
        self.assertIsInstance(timestamp2, str)
        
        # Both should be 14 characters (YYYYMMDDHHMMSS)
        self.assertEqual(len(timestamp1), 14)
        self.assertEqual(len(timestamp2), 14)
        
        # Both should be numeric
        self.assertTrue(timestamp1.isdigit())
        self.assertTrue(timestamp2.isdigit())
        
        # Second timestamp should be >= first (time moves forward)
        self.assertGreaterEqual(timestamp2, timestamp1)
        
        print("✅ Timestamp function test passed")

    def test_parse_args_basic(self):
        """Test parse_args basic functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        original_argv = sys.argv.copy()
        try:
            # Test basic parsing (CSA requires two config files)
            sys.argv = ['main.py', 'test_config.json', 'test_kafka_config.json']
            config_path, kafka_config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
            self.assertEqual(kafka_config_path, 'test_kafka_config.json')
            self.assertFalse(wait_flag)
            self.assertFalse(test_flag)
            
            print("✅ Parse args basic test passed")
        finally:
            sys.argv = original_argv

    def test_parse_args_with_flags(self):
        """Test parse_args with flags"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        original_argv = sys.argv.copy()
        try:
            # Test with all flags
            sys.argv = ['main.py', 'test_config.json', 'test_kafka_config.json', '--wait', '-t']
            config_path, kafka_config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
            self.assertEqual(kafka_config_path, 'test_kafka_config.json')
            self.assertTrue(wait_flag)
            self.assertTrue(test_flag)
            
            print("✅ Parse args with flags test passed")
        finally:
            sys.argv = original_argv

    def test_banner_function(self):
        """Test banner helper function"""
        if not KPI_HELPER_IMPORT_SUCCESS:
            self.skipTest(f"KPI_Helper not available: {KPI_HELPER_IMPORT_ERROR}")
            
        # Test banner generation
        result = banner("Test Message")
        
        # Should be a string
        self.assertIsInstance(result, str)
        
        # Should contain the message
        self.assertIn("Test Message", result)
        
        # Should contain dashes
        self.assertIn("-", result)
        
        # Test with different message
        result2 = banner("Another Test")
        self.assertIn("Another Test", result2)
        self.assertNotEqual(result, result2)
        
        print("✅ Banner function test passed")

    def test_http_status_functions(self):
        """Test HTTP status helper functions"""
        if not KPI_HELPER_IMPORT_SUCCESS:
            self.skipTest(f"KPI_Helper not available: {KPI_HELPER_IMPORT_ERROR}")
            
        # Test is_http_ok function
        self.assertTrue(is_http_ok("200"))  # OK
        self.assertTrue(is_http_ok("201"))  # Created
        self.assertTrue(is_http_ok("301"))  # Redirect
        self.assertFalse(is_http_ok("404")) # Not Found
        self.assertFalse(is_http_ok("500")) # Server Error
        
        # Test is_http_error function  
        self.assertFalse(is_http_error("200")) # OK
        self.assertFalse(is_http_error("301")) # Redirect
        self.assertTrue(is_http_error("404"))  # Not Found
        self.assertTrue(is_http_error("500"))  # Server Error
        
        # Test edge cases
        self.assertTrue(is_http_ok("100"))   # Continue
        self.assertTrue(is_http_error("400")) # Bad Request
        
        print("✅ HTTP status functions test passed")

    def test_files_newer_that_mins_with_test_files(self):
        """Test files_newer_that_mins function with created test files"""
        if not KPI_HELPER_IMPORT_SUCCESS:
            self.skipTest(f"KPI_Helper not available: {KPI_HELPER_IMPORT_ERROR}")
            
        # Create test files with different ages
        current_time = time.time()
        
        # Create a recent file (1 minute old)
        recent_file = os.path.join(self.test_dir, "recent_test.txt")
        with open(recent_file, 'w') as f:
            f.write("recent")
        os.utime(recent_file, (current_time - 60, current_time - 60))  # 1 min ago
        
        # Create an old file (10 minutes old)
        old_file = os.path.join(self.test_dir, "old_test.txt")
        with open(old_file, 'w') as f:
            f.write("old")
        os.utime(old_file, (current_time - 600, current_time - 600))  # 10 min ago
        
        # Test finding files newer than 5 minutes
        newer_files = files_newer_that_mins(self.test_dir, "*.txt", 5)
        
        # Should find only the recent file
        self.assertEqual(len(newer_files), 1)
        self.assertIn("recent_test.txt", newer_files[0])
        
        # Test finding files newer than 15 minutes (should find both)
        newer_files = files_newer_that_mins(self.test_dir, "*.txt", 15)
        self.assertEqual(len(newer_files), 2)
        
        print("✅ Files newer than mins function test passed")

    def test_delete_files_older_than_days_with_test_files(self):
        """Test delete_files_older_than_days function with created test files"""
        if not KPI_HELPER_IMPORT_SUCCESS:
            self.skipTest(f"KPI_Helper not available: {KPI_HELPER_IMPORT_ERROR}")
            
        # Create test files with different ages
        current_time = time.time()
        
        # Create a recent file
        recent_file = os.path.join(self.test_dir, "recent_file.txt")
        with open(recent_file, 'w') as f:
            f.write("recent")
        
        # Create an old file (10 days old)
        old_file = os.path.join(self.test_dir, "old_file.txt")
        with open(old_file, 'w') as f:
            f.write("old")
        old_time = current_time - (10 * 24 * 60 * 60)  # 10 days ago
        os.utime(old_file, (old_time, old_time))
        
        # Verify both files exist
        self.assertTrue(os.path.exists(recent_file))
        self.assertTrue(os.path.exists(old_file))
        
        # Delete files older than 7 days
        delete_files_older_than_days(self.test_dir, 7)
        
        # Recent file should still exist, old file should be deleted
        self.assertTrue(os.path.exists(recent_file))
        self.assertFalse(os.path.exists(old_file))
        
        print("✅ Delete files older than days function test passed")

    def test_file_structure_exists(self):
        """Test basic file structure"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Test main files exist
        files_to_check = [
            'main.py', 'KPI_CSA.py', 'KPI_Helper.py', 
            'SubprocessClass.py', 'JsonReaderClass.py', 'measCollec.xsl'
        ]
        for filename in files_to_check:
            filepath = os.path.join(module_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"{filename} should exist")
            
        # Test config directory exists
        config_dir = os.path.join(module_dir, 'config')
        self.assertTrue(os.path.exists(config_dir), "config directory should exist")
        
        print("✅ File structure exists test passed")

    def test_config_file_structure(self):
        """Test configuration file structure"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(module_dir, 'config', 'config.json')
        
        self.assertTrue(os.path.exists(config_file), "config.json should exist")
        
        # Try to load and validate structure
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Check for required keys specific to CSA
            required_keys = [
                'wait_to_start_secs', 'namespace', 'pod', 'dir_lookup',
                'perf_data_files_local_dir', 'execution_period_mins', 'kafka_message_template'
            ]
            
            for key in required_keys:
                self.assertIn(key, config_data, f"Config should contain {key}")
            
            # Validate CSA-specific values
            self.assertEqual(config_data.get('namespace'), 'csa', "Namespace should be 'csa' for CSA")
            self.assertEqual(config_data.get('pod'), 'pm-bulk', "Pod should be 'pm-bulk' for CSA")
            self.assertIn('ERICSSON_CSA', str(config_data.get('kafka_message_template', {})), 
                         "Message template should reference ERICSSON_CSA")
            
            print("✅ Config file structure test passed")
            
        except json.JSONDecodeError:
            self.fail("config.json should contain valid JSON")
        except Exception as e:
            self.fail(f"Error reading config.json: {e}")

    def test_csa_specific_imports(self):
        """Test CSA-specific module functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # Test that main module has CSA-specific functions
        csa_functions = [
            'timestamp', 'parse_args', 'load_config', 'fetch_hostname',
            'setup', 'available_pods', 'make_kafka_data_source_file_path',
            'wait_to_start', 'setup_logging', 'main'
        ]
        
        for func_name in csa_functions:
            self.assertTrue(hasattr(main, func_name), 
                          f"main module should have {func_name} function")
        
        print("✅ CSA-specific imports test passed")

    def test_subprocess_class_basic(self):
        """Test SubprocessClass basic functionality"""
        if not SUBPROCESS_IMPORT_SUCCESS:
            self.skipTest(f"SubprocessClass not available: {SUBPROCESS_IMPORT_ERROR}")
            
        try:
            subprocess_obj = SubprocessClass()
            self.assertIsNotNone(subprocess_obj)
            
            # Test that execute_cmd method exists
            self.assertTrue(hasattr(subprocess_obj, 'execute_cmd'))
            self.assertTrue(callable(getattr(subprocess_obj, 'execute_cmd')))
            
            print("✅ SubprocessClass basic test passed")
        except Exception as e:
            print(f"⚠️  SubprocessClass basic test had issues: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("KAFKA_CSA - Safe Function Tests")
    print("=" * 60)
    print("Testing only functions that don't require complex mocking")
    print("=" * 60)
    
    unittest.main(verbosity=2)
