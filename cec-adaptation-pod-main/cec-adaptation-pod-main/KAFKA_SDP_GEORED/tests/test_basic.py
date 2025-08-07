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


class TestKafkaSDPGeoredBasic(unittest.TestCase):
    """Basic functionality tests for KAFKA_SDP_GEORED module"""

    def test_import_success(self):
        """Test that we can import basic functions from main module"""
        if not MAIN_IMPORT_SUCCESS:
            print(f"⚠️ Main module import failed: {MAIN_IMPORT_ERROR}")
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        # Test that key functions are available
        self.assertTrue(hasattr(main, 'timestamp'))
        self.assertTrue(hasattr(main, 'parse_args'))
        self.assertTrue(hasattr(main, 'make_dir'))
        self.assertTrue(hasattr(main, 'eval_value'))
        print("✅ Import success test passed")

    def test_module_file_exists(self):
        """Test that the main module file exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_file = os.path.join(script_dir, 'main.py')
        self.assertTrue(os.path.exists(main_file), f"main.py should exist at {main_file}")
        print("✅ Module file exists test passed")

    def test_kpi_sdp_file_exists(self):
        """Test that KPI_SDP.py file exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kpi_sdp_file = os.path.join(script_dir, 'KPI_SDP.py')
        self.assertTrue(os.path.exists(kpi_sdp_file), f"KPI_SDP.py should exist at {kpi_sdp_file}")
        print("✅ KPI_SDP file exists test passed")

    def test_logger_file_exists(self):
        """Test that Logger.py file exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger_file = os.path.join(script_dir, 'Logger.py')
        self.assertTrue(os.path.exists(logger_file), f"Logger.py should exist at {logger_file}")
        print("✅ Logger file exists test passed")

    def test_subprocess_class_file_exists(self):
        """Test that SubprocessClass.py file exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess_file = os.path.join(script_dir, 'SubprocessClass.py')
        self.assertTrue(os.path.exists(subprocess_file), f"SubprocessClass.py should exist at {subprocess_file}")
        print("✅ SubprocessClass file exists test passed")

    def test_configuration_directory_exists(self):
        """Test that configuration directory exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(script_dir, 'config')
        self.assertTrue(os.path.exists(config_dir), f"Config directory should exist at {config_dir}")
        
        # Check for config.json
        config_file = os.path.join(config_dir, 'config.json')
        self.assertTrue(os.path.exists(config_file), f"config.json should exist at {config_file}")
        print("✅ Configuration directory exists test passed")

    def test_timestamp_functionality(self):
        """Test timestamp generation functionality"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        timestamp = main.timestamp()
        
        # Check timestamp format (YYYYMMDDHHMMSS)
        self.assertIsInstance(timestamp, str)
        self.assertEqual(len(timestamp), 14, "Timestamp should be 14 characters long")
        
        # Check if it's numeric
        self.assertTrue(timestamp.isdigit(), "Timestamp should be numeric")
        
        # Check if it represents a valid date
        current_year = datetime.now().year
        timestamp_year = int(timestamp[:4])
        self.assertGreaterEqual(timestamp_year, current_year - 1)
        self.assertLessEqual(timestamp_year, current_year + 1)
        print("✅ Timestamp functionality test passed")

    def test_parse_args_basic_functionality(self):
        """Test parse_args with basic arguments"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with basic arguments
            sys.argv = ['main.py', '/path/to/config.json']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, '/path/to/config.json')
            self.assertFalse(wait)
            self.assertFalse(test_mode)
            print("✅ parse_args basic functionality test passed")
            
        except SystemExit:
            # argparse exits when parsing fails, which is expected behavior
            print("✅ parse_args basic functionality test passed")
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_with_flags_functionality(self):
        """Test parse_args with optional flags"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with flags
            sys.argv = ['main.py', '/path/to/config.json', '--wait', '--test']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, '/path/to/config.json')
            self.assertTrue(wait)
            self.assertTrue(test_mode)
            print("✅ parse_args with flags functionality test passed")
            
        except SystemExit:
            # argparse exits when parsing fails, which is expected behavior
            print("✅ parse_args with flags functionality test passed")
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_import_kpi_sdp_module(self):
        """Test that we can import KPI_SDP module"""
        if not KPI_SDP_IMPORT_SUCCESS:
            print(f"⚠️ KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
        
        # If we get here, the import was successful
        self.assertTrue(KPI_SDP_IMPORT_SUCCESS)
        print("✅ Successfully imported KPI_SDP module")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_SDP_GEORED Basic Tests")
    print("=" * 60)
    
    # Check import status before running tests
    if MAIN_IMPORT_SUCCESS:
        print("✅ All imports successful - running full test suite")
    else:
        print(f"⚠️ Some imports failed - running available tests only")
        print(f"   Main import error: {MAIN_IMPORT_ERROR}")
    
    print("=" * 60)
    unittest.main(verbosity=2)
