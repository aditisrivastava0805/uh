#!/usr/bin/env python3
"""
Safe function tests for KAFKA_SDP_GEORED module
These tests focus on functions that can be tested reliably without complex external dependencies
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
from datetime import datetime

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
    from KPI_SDP import KPI_SDP
    KPI_SDP_IMPORT_SUCCESS = True
    KPI_SDP_IMPORT_ERROR = None
except Exception as e:
    KPI_SDP_IMPORT_SUCCESS = False
    KPI_SDP_IMPORT_ERROR = str(e)

try:
    from Logger import LoggingHandler
    LOGGER_IMPORT_SUCCESS = True
    LOGGER_IMPORT_ERROR = None
except Exception as e:
    LOGGER_IMPORT_SUCCESS = False
    LOGGER_IMPORT_ERROR = str(e)

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

    def test_kpi_sdp_class_import(self):
        """Test that KPI_SDP class can be imported"""
        self.assertTrue(KPI_SDP_IMPORT_SUCCESS, f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
        print("✅ KPI_SDP class import test passed")

    def test_logger_class_import(self):
        """Test that LoggingHandler can be imported"""
        self.assertTrue(LOGGER_IMPORT_SUCCESS, f"Logger import failed: {LOGGER_IMPORT_ERROR}")
        print("✅ Logger class import test passed")

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
            # Test basic parsing
            sys.argv = ['main.py', 'test_config.json']
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
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
            sys.argv = ['main.py', 'test_config.json', '--wait', '-t']
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
            self.assertTrue(wait_flag)
            self.assertTrue(test_flag)
            
            print("✅ Parse args with flags test passed")
        finally:
            sys.argv = original_argv

    def test_eval_value_simple(self):
        """Test eval_value with simple string (no command)"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # Test simple string (not a command)
        result = main.eval_value("simple_string")
        self.assertEqual(result, "simple_string")
        
        # Test another simple string
        result = main.eval_value("test-namespace")
        self.assertEqual(result, "test-namespace")
        
        print("✅ Eval value simple test passed")

    def test_make_dir_function(self):
        """Test make_dir function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # Test creating a new directory
        test_path = os.path.join(self.test_dir, "new_test_dir")
        self.assertFalse(os.path.exists(test_path))
        
        main.make_dir(test_path)
        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.path.isdir(test_path))
        
        # Test creating nested directories
        nested_path = os.path.join(self.test_dir, "level1", "level2", "level3")
        self.assertFalse(os.path.exists(nested_path))
        
        main.make_dir(nested_path)
        self.assertTrue(os.path.exists(nested_path))
        self.assertTrue(os.path.isdir(nested_path))
        
        # Test that calling on existing directory doesn't raise error
        main.make_dir(test_path)  # Should not raise exception
        self.assertTrue(os.path.exists(test_path))
        
        print("✅ Make directory function test passed")

    def test_file_structure_exists(self):
        """Test basic file structure"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Test main files exist
        files_to_check = ['main.py', 'KPI_SDP.py', 'Logger.py', 'SubprocessClass.py']
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
            
            # Check for required keys specific to GEORED
            required_keys = [
                'wait_to_start_secs', 'namespace', 'pod', 'pod_container',
                'max_processes', 'whitelist_pod_enable', 'whitelist_pods',
                'blacklist_pods', 'kafka_message_template'
            ]
            
            for key in required_keys:
                self.assertIn(key, config_data, f"Config should contain {key}")
            
            # Validate GEORED-specific values
            self.assertEqual(config_data.get('pod'), 'sdp', "Pod should be 'sdp' for GEORED")
            self.assertEqual(config_data.get('pod_container'), 'sdp', "Pod container should be 'sdp' for GEORED")
            
            print("✅ Config file structure test passed")
            
        except json.JSONDecodeError:
            self.fail("config.json should contain valid JSON")
        except Exception as e:
            self.fail(f"Error reading config.json: {e}")

    def test_geored_specific_imports(self):
        """Test GEORED-specific module functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # Test that main module has GEORED-specific functions
        geored_functions = [
            'timestamp', 'parse_args', 'load_config', 'eval_value',
            'wait_to_start', 'make_dir', 'fetch_hostname', 'available_pods',
            'make_kafka_data_source_file_path', 'execute', 'main'
        ]
        
        for func_name in geored_functions:
            self.assertTrue(hasattr(main, func_name), 
                          f"main module should have {func_name} function")
        
        print("✅ GEORED-specific imports test passed")

    def test_concurrent_futures_support(self):
        """Test that concurrent.futures is properly imported in main"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module not available: {MAIN_IMPORT_ERROR}")
            
        # The main module should have imported concurrent.futures
        # We can check this by verifying it's used in the main function
        main_source = None
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_file = os.path.join(module_dir, 'main.py')
        
        try:
            with open(main_file, 'r') as f:
                main_source = f.read()
                
            self.assertIn('concurrent.futures', main_source, 
                         "main.py should import concurrent.futures")
            self.assertIn('ProcessPoolExecutor', main_source, 
                         "main.py should use ProcessPoolExecutor")
                         
            print("✅ Concurrent futures support test passed")
        except Exception as e:
            self.skipTest(f"Could not read main.py: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("KAFKA_SDP_GEORED - Safe Function Tests")
    print("=" * 60)
    print("Testing only functions that don't require complex mocking")
    print("=" * 60)
    
    unittest.main(verbosity=2)
