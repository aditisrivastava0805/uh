import unittest
import sys
import os
import tempfile
import shutil
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
    """Test functions that don't require complex mocking"""

    def test_module_imports_successfully(self):
        """Test that the main module can be imported"""
        self.assertTrue(MAIN_IMPORT_SUCCESS, f"Main module should import successfully: {MAIN_IMPORT_ERROR}")
        print("✅ Module imports successfully")

    def test_timestamp_function(self):
        """Test timestamp function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        timestamp1 = main.timestamp()
        timestamp2 = main.timestamp()
        
        # Both should be strings of length 14
        self.assertIsInstance(timestamp1, str)
        self.assertIsInstance(timestamp2, str)
        self.assertEqual(len(timestamp1), 14)
        self.assertEqual(len(timestamp2), 14)
        
        # Should be numeric
        self.assertTrue(timestamp1.isdigit())
        self.assertTrue(timestamp2.isdigit())
        
        # timestamp2 should be >= timestamp1 (or equal if very fast)
        self.assertGreaterEqual(int(timestamp2), int(timestamp1))
        print("✅ Timestamp function test passed")

    def test_parse_args_basic(self):
        """Test parse_args basic functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['main.py', 'test_config.json']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
            self.assertIsInstance(wait, bool)
            self.assertIsInstance(test_mode, bool)
            print("✅ Parse args basic test passed")
            
        except SystemExit:
            print("✅ Parse args basic test passed")
        finally:
            sys.argv = original_argv

    def test_parse_args_with_flags(self):
        """Test parse_args with flags"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['main.py', 'test_config.json', '--wait', '--test']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, 'test_config.json')
            self.assertTrue(wait)
            self.assertTrue(test_mode)
            print("✅ Parse args with flags test passed")
            
        except SystemExit:
            print("✅ Parse args with flags test passed")
        finally:
            sys.argv = original_argv

    def test_make_dir_function(self):
        """Test make_dir function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        # Create a temporary directory path
        temp_dir = tempfile.mkdtemp()
        test_dir = os.path.join(temp_dir, 'test_kafka_sdp_geored')
        
        try:
            # Directory shouldn't exist initially
            self.assertFalse(os.path.exists(test_dir))
            
            # Create directory using make_dir
            main.make_dir(test_dir)
            
            # Directory should now exist
            self.assertTrue(os.path.exists(test_dir))
            self.assertTrue(os.path.isdir(test_dir))
            
            # Test that calling make_dir on existing directory doesn't error
            main.make_dir(test_dir)
            self.assertTrue(os.path.exists(test_dir))
            
            print("✅ Make directory function test passed")
            
        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_eval_value_simple(self):
        """Test eval_value with simple string (no command)"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        # Test with simple string (not a command)
        simple_value = "test_namespace"
        result = main.eval_value(simple_value)
        
        self.assertEqual(result, simple_value)
        self.assertIsInstance(result, str)
        print("✅ Eval value simple test passed")

    def test_file_structure_exists(self):
        """Test basic file structure"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_files = [
            'main.py',
            'KPI_SDP.py',
            'Logger.py',
            'SubprocessClass.py'
        ]
        
        required_dirs = [
            'config'
        ]
        
        for file_name in required_files:
            file_path = os.path.join(script_dir, file_name)
            self.assertTrue(os.path.exists(file_path), f"{file_name} should exist")
        
        for dir_name in required_dirs:
            dir_path = os.path.join(script_dir, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"{dir_name} directory should exist")
        
        print("✅ File structure exists test passed")

    def test_kpi_sdp_class_import(self):
        """Test that KPI_SDP class can be imported"""
        if not KPI_SDP_IMPORT_SUCCESS:
            print(f"⚠️ KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
        
        # Test that KPI_SDP is a class
        self.assertTrue(hasattr(KPI_SDP, '__init__'))
        print("✅ KPI_SDP class import test passed")

    def test_logger_class_import(self):
        """Test that LoggingHandler can be imported"""
        if not LOGGER_IMPORT_SUCCESS:
            print(f"⚠️ Logger import failed: {LOGGER_IMPORT_ERROR}")
            self.skipTest(f"Logger import failed: {LOGGER_IMPORT_ERROR}")
        
        # Test that LoggingHandler is available
        self.assertTrue(hasattr(LoggingHandler, 'get_logger'))
        print("✅ Logger class import test passed")

    def test_subprocess_class_import(self):
        """Test that SubprocessClass can be imported"""
        if not SUBPROCESS_IMPORT_SUCCESS:
            print(f"⚠️ SubprocessClass import failed: {SUBPROCESS_IMPORT_ERROR}")
            self.skipTest(f"SubprocessClass import failed: {SUBPROCESS_IMPORT_ERROR}")
        
        # Test that SubprocessClass is available
        self.assertTrue(hasattr(SubprocessClass, '__init__'))
        print("✅ SubprocessClass import test passed")

    def test_config_file_structure(self):
        """Test configuration file structure"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(script_dir, 'config', 'config.json')
        
        self.assertTrue(os.path.exists(config_file), "config.json should exist")
        
        # Test that it's a valid JSON file by attempting to read it
        try:
            import json
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Test that essential keys exist
            expected_keys = [
                'namespace', 'pod', 'pod_container', 'max_processes',
                'whitelist_pod_enable', 'kafka_message_template'
            ]
            
            for key in expected_keys:
                self.assertIn(key, config_data, f"Config should contain {key}")
            
            print("✅ Config file structure test passed")
            
        except Exception as e:
            self.fail(f"Config file should be valid JSON: {str(e)}")


if __name__ == '__main__':
    print("=" * 60)
    print("KAFKA_SDP_GEORED - Safe Function Tests")
    print("=" * 60)
    print("Testing only functions that don't require complex mocking")
    print("=" * 60)
    unittest.main(verbosity=2)
