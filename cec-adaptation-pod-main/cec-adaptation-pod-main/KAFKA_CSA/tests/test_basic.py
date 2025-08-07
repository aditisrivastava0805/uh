#!/usr/bin/env python3
"""
Basic functionality tests for KAFKA_CSA module
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
    from KPI_CSA import KPI_CSA
    KPI_CSA_IMPORT_SUCCESS = True
    KPI_CSA_IMPORT_ERROR = None
except Exception as e:
    KPI_CSA_IMPORT_SUCCESS = False
    KPI_CSA_IMPORT_ERROR = str(e)

try:
    from KPI_Helper import banner, files_newer_that_mins, delete_files_older_than_days
    KPI_HELPER_IMPORT_SUCCESS = True
    KPI_HELPER_IMPORT_ERROR = None
except Exception as e:
    KPI_HELPER_IMPORT_SUCCESS = False
    KPI_HELPER_IMPORT_ERROR = str(e)

try:
    from SubprocessClass import SubprocessClass
    SUBPROCESS_IMPORT_SUCCESS = True
    SUBPROCESS_IMPORT_ERROR = None
except Exception as e:
    SUBPROCESS_IMPORT_SUCCESS = False
    SUBPROCESS_IMPORT_ERROR = str(e)

try:
    from JsonReaderClass import JsonReaderClass
    JSON_READER_IMPORT_SUCCESS = True
    JSON_READER_IMPORT_ERROR = None
except Exception as e:
    JSON_READER_IMPORT_SUCCESS = False
    JSON_READER_IMPORT_ERROR = str(e)


class TestKafkaCSABasic(unittest.TestCase):
    """Basic functionality tests for KAFKA_CSA module"""

    def test_import_success(self):
        """Test that we can import basic functions from main module"""
        self.assertTrue(MAIN_IMPORT_SUCCESS, f"Main import failed: {MAIN_IMPORT_ERROR}")
        
        # Test that main functions exist
        self.assertTrue(hasattr(main, 'timestamp'), "main module should have timestamp function")
        self.assertTrue(hasattr(main, 'parse_args'), "main module should have parse_args function")
        self.assertTrue(hasattr(main, 'load_config'), "main module should have load_config function")
        self.assertTrue(hasattr(main, 'setup'), "main module should have setup function")
        
        print("✅ Import success test passed")

    def test_import_kpi_csa_module(self):
        """Test that we can import KPI_CSA module"""
        self.assertTrue(KPI_CSA_IMPORT_SUCCESS, f"KPI_CSA import failed: {KPI_CSA_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(KPI_CSA, '__init__'), "KPI_CSA should be a class with __init__")
        
        print("✅ Successfully imported KPI_CSA module")

    def test_import_kpi_helper_module(self):
        """Test that we can import KPI_Helper functions"""
        self.assertTrue(KPI_HELPER_IMPORT_SUCCESS, f"KPI_Helper import failed: {KPI_HELPER_IMPORT_ERROR}")
        
        # Test that helper functions exist
        self.assertTrue(callable(banner), "banner should be callable")
        self.assertTrue(callable(files_newer_that_mins), "files_newer_that_mins should be callable")
        self.assertTrue(callable(delete_files_older_than_days), "delete_files_older_than_days should be callable")
        
        print("✅ Successfully imported KPI_Helper functions")

    def test_import_subprocess_module(self):
        """Test that we can import SubprocessClass"""
        self.assertTrue(SUBPROCESS_IMPORT_SUCCESS, f"SubprocessClass import failed: {SUBPROCESS_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(SubprocessClass, '__init__'), "SubprocessClass should be a class")
        
        print("✅ Successfully imported SubprocessClass module")

    def test_import_json_reader_module(self):
        """Test that we can import JsonReaderClass"""
        self.assertTrue(JSON_READER_IMPORT_SUCCESS, f"JsonReaderClass import failed: {JSON_READER_IMPORT_ERROR}")
        
        # Test that it's a class
        self.assertTrue(hasattr(JsonReaderClass, '__init__'), "JsonReaderClass should be a class")
        
        print("✅ Successfully imported JsonReaderClass module")

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
            # Test with basic arguments (CSA needs two config files)
            sys.argv = ['main.py', 'config.json', 'kafka_config.json']
            
            config_path, kafka_config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertEqual(kafka_config_path, 'kafka_config.json')
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
            sys.argv = ['main.py', 'config.json', 'kafka_config.json', '--wait', '--test']
            
            config_path, kafka_config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertEqual(kafka_config_path, 'kafka_config.json')
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

    def test_kpi_csa_file_exists(self):
        """Test that KPI_CSA.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kpi_file = os.path.join(module_dir, 'KPI_CSA.py')
        self.assertTrue(os.path.exists(kpi_file), f"KPI_CSA.py should exist at {kpi_file}")
        print("✅ KPI_CSA file exists test passed")

    def test_kpi_helper_file_exists(self):
        """Test that KPI_Helper.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        helper_file = os.path.join(module_dir, 'KPI_Helper.py')
        self.assertTrue(os.path.exists(helper_file), f"KPI_Helper.py should exist at {helper_file}")
        print("✅ KPI_Helper file exists test passed")

    def test_subprocess_class_file_exists(self):
        """Test that SubprocessClass.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess_file = os.path.join(module_dir, 'SubprocessClass.py')
        self.assertTrue(os.path.exists(subprocess_file), f"SubprocessClass.py should exist at {subprocess_file}")
        print("✅ SubprocessClass file exists test passed")

    def test_json_reader_file_exists(self):
        """Test that JsonReaderClass.py file exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_reader_file = os.path.join(module_dir, 'JsonReaderClass.py')
        self.assertTrue(os.path.exists(json_reader_file), f"JsonReaderClass.py should exist at {json_reader_file}")
        print("✅ JsonReaderClass file exists test passed")

    def test_configuration_directory_exists(self):
        """Test that configuration directory exists"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(module_dir, 'config')
        self.assertTrue(os.path.exists(config_dir), f"config directory should exist at {config_dir}")
        
        # Check for config.json
        config_file = os.path.join(config_dir, 'config.json')
        self.assertTrue(os.path.exists(config_file), f"config.json should exist at {config_file}")
        
        print("✅ Configuration directory exists test passed")

    def test_measCollec_xsl_file_exists(self):
        """Test that measCollec.xsl file exists (CSA-specific)"""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xsl_file = os.path.join(module_dir, 'measCollec.xsl')
        self.assertTrue(os.path.exists(xsl_file), f"measCollec.xsl should exist at {xsl_file}")
        print("✅ measCollec.xsl file exists test passed")

    def test_csa_specific_functions(self):
        """Test CSA-specific functions exist"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
            
        # Test CSA-specific functions
        csa_functions = [
            'fetch_hostname', 'available_pods', 'make_kafka_data_source_file_path', 
            'setup', 'wait_to_start', 'setup_logging'
        ]
        
        for func_name in csa_functions:
            self.assertTrue(hasattr(main, func_name), 
                          f"main module should have {func_name} function")
        
        print("✅ CSA-specific functions test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_CSA Basic Tests")
    print("=" * 60)
    
    # Check import status first
    if MAIN_IMPORT_SUCCESS:
        print("✅ All imports successful - running full test suite")
    else:
        print(f"⚠️ Main import failed: {MAIN_IMPORT_ERROR}")
        
    print("=" * 60)
    
    unittest.main(verbosity=2)
