#!/usr/bin/env python3
"""
Basic functionality tests for KAFKA_SDP_GEORED module
These tests focus on core functionality that can be tested without complex mocking
"""

import unittest
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports to check if modules are available
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


class TestKafkaSDPGeoredBasic(unittest.TestCase):
    """Basic functionality tests for KAFKA_SDP_GEORED module"""

    def test_import_success(self):
        """Test that we can import basic functions from main module"""
        self.assertTrue(MAIN_IMPORT_SUCCESS, f"Main import failed: {MAIN_IMPORT_ERROR}")
        
        # Test that main functions exist
        self.assertTrue(hasattr(main, 'timestamp'), "main module should have timestamp function")
        self.assertTrue(hasattr(main, 'parse_args'), "main module should have parse_args function")
        self.assertTrue(hasattr(main, 'eval_value'), "main module should have eval_value function")
        self.assertTrue(hasattr(main, 'make_dir'), "main module should have make_dir function")
        
        print("✅ Import success test passed")

    def test_import_kpi_sdp_module(self):
        """Test that we can import KPI_SDP module"""
        self.assertTrue(KPI_SDP_IMPORT_SUCCESS, f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(KPI_SDP, '__init__'), "KPI_SDP should be a class with __init__")
        
        print("✅ Successfully imported KPI_SDP module")

    def test_import_logger_module(self):
        """Test that we can import LoggingHandler"""
        self.assertTrue(LOGGER_IMPORT_SUCCESS, f"Logger import failed: {LOGGER_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(LoggingHandler, '__init__'), "LoggingHandler should be a class")
        
        print("✅ Successfully imported LoggingHandler module")

    def test_import_subprocess_module(self):
        """Test that we can import SubprocessClass"""
        self.assertTrue(SUBPROCESS_IMPORT_SUCCESS, f"SubprocessClass import failed: {SUBPROCESS_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(SubprocessClass, '__init__'), "SubprocessClass should be a class")
        
        print("✅ Successfully imported SubprocessClass module")

    def test_timestamp_functionality(self):
        """Test timestamp generation functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
            
        timestamp = main.timestamp()
        
        # Test return type
        self.assertIsInstance(timestamp, str, "timestamp should return a string")
        
        # Test format (should be YYYYMMDDHHMMSS = 14 characters)
        self.assertEqual(len(timestamp), 14, "timestamp should be 14 characters long")
        
        # Test that it's all digits
        self.assertTrue(timestamp.isdigit(), "timestamp should contain only digits")
        
        # Test that it represents a valid date (starts with current year)
        current_year = datetime.now().year
        self.assertTrue(timestamp.startswith(str(current_year)), 
                       f"timestamp should start with current year {current_year}")
        
        print("✅ Timestamp functionality test passed")

    def test_parse_args_basic_functionality(self):
        """Test parse_args with basic arguments"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
            
        # Save original argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with basic arguments
            sys.argv = ['main.py', 'config.json']
            
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertFalse(wait_flag)
            self.assertFalse(test_flag)
            
            print("✅ parse_args basic functionality test passed")
            
        finally:
            # Restore original argv
            sys.argv = original_argv

    def test_parse_args_with_flags_functionality(self):
        """Test parse_args with optional flags"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
            
        # Save original argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with flags
            sys.argv = ['main.py', 'config.json', '--wait', '--test']
            
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertTrue(wait_flag)
            self.assertTrue(test_flag)
            
            print("✅ parse_args with flags functionality test passed")
            
        finally:
            # Restore original argv
            sys.argv = original_argv

    def test_module_file_exists(self):
        """Test that the main module file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_file = os.path.join(module_dir, 'main.py')
        self.assertTrue(os.path.exists(main_file), f"main.py should exist at {main_file}")
        print("✅ Module file exists test passed")

    def test_kpi_sdp_file_exists(self):
        """Test that KPI_SDP.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kpi_file = os.path.join(module_dir, 'KPI_SDP.py')
        self.assertTrue(os.path.exists(kpi_file), f"KPI_SDP.py should exist at {kpi_file}")
        print("✅ KPI_SDP file exists test passed")

    def test_logger_file_exists(self):
        """Test that Logger.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger_file = os.path.join(module_dir, 'Logger.py')
        self.assertTrue(os.path.exists(logger_file), f"Logger.py should exist at {logger_file}")
        print("✅ Logger file exists test passed")

    def test_subprocess_class_file_exists(self):
        """Test that SubprocessClass.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess_file = os.path.join(module_dir, 'SubprocessClass.py')
        self.assertTrue(os.path.exists(subprocess_file), f"SubprocessClass.py should exist at {subprocess_file}")
        print("✅ SubprocessClass file exists test passed")

    def test_configuration_directory_exists(self):
        """Test that configuration directory exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(module_dir, 'config')
        self.assertTrue(os.path.exists(config_dir), f"config directory should exist at {config_dir}")
        
        # Check for config.json
        config_file = os.path.join(config_dir, 'config.json')
        self.assertTrue(os.path.exists(config_file), f"config.json should exist at {config_file}")
        
        print("✅ Configuration directory exists test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_SDP_GEORED Basic Tests")
    print("=" * 60)
    
    # Check import status first
    if MAIN_IMPORT_SUCCESS:
        print("✅ All imports successful - running full test suite")
    else:
        print(f"⚠️ Main import failed: {MAIN_IMPORT_ERROR}")
        
    print("=" * 60)
    
    unittest.main(verbosity=2)
