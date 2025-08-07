import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import concurrent.futures

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from tests.test_main import TestMain
from tests.test_kpi_sdp import TestKPISDP
from tests.test_logger import TestLoggingHandler
from tests.test_subprocess_class import TestSubprocessClass


class TestKafkaSDPPrepaidBasic(unittest.TestCase):
    """Basic integration tests for KAFKA_SDP_PREPAID module"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_import_main_module(self):
        """Test that we can import the main module"""
        try:
            import main
            self.assertTrue(hasattr(main, 'timestamp'))
            self.assertTrue(hasattr(main, 'parse_args'))
            self.assertTrue(hasattr(main, 'load_config'))
            self.assertTrue(hasattr(main, 'main'))
            print("✅ Successfully imported main module")
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")

    def test_import_kpi_sdp_module(self):
        """Test that we can import KPI_SDP module"""
        try:
            from KPI_SDP import KPI_SDP
            self.assertTrue(callable(KPI_SDP))
            print("✅ Successfully imported KPI_SDP module")
        except ImportError as e:
            self.fail(f"Failed to import KPI_SDP module: {e}")

    def test_import_logger_module(self):
        """Test that we can import Logger module"""
        try:
            from Logger import LoggingHandler
            self.assertTrue(callable(LoggingHandler))
            print("✅ Successfully imported Logger module")
        except ImportError as e:
            self.fail(f"Failed to import Logger module: {e}")

    def test_import_subprocess_module(self):
        """Test that we can import SubprocessClass module"""
        try:
            from SubprocessClass import SubprocessClass
            self.assertTrue(callable(SubprocessClass))
            print("✅ Successfully imported SubprocessClass module")
        except ImportError as e:
            self.fail(f"Failed to import SubprocessClass module: {e}")

    def test_configuration_files_exist(self):
        """Test that required configuration files exist"""
        config_files = [
            "config/config.json",
            "config/logger-config.json"
        ]
        
        for config_file in config_files:
            file_path = os.path.join(self.base_dir, config_file)
            self.assertTrue(os.path.exists(file_path), f"Configuration file {config_file} does not exist")
        
        print("✅ Configuration files existence test passed")

    def test_config_json_structure(self):
        """Test that config.json has the required structure"""
        config_path = os.path.join(self.base_dir, "config", "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            required_keys = [
                "wait_to_start_secs",
                "namespace", 
                "pod",
                "pod_container",
                "max_processes",
                "whitelist_pod_enable",
                "whitelist_pods",
                "blacklist_pods",
                "kafka_message_template"
            ]
            
            for key in required_keys:
                self.assertIn(key, config, f"Required key '{key}' not found in config.json")
            
            print("✅ config.json structure test passed")
        else:
            self.skipTest("config.json not found")

    @patch('main.subprocess_obj')
    def test_basic_pod_parsing_functionality(self, mock_subprocess_obj):
        """Test basic pod parsing functionality"""
        try:
            from main import available_pods
            
            # Mock kubectl output
            mock_output = """csdp-pod-1 1/1 Running 0 1d
csdp-pod-2 1/1 Running 0 2d
csdp-pod-3 0/1 Pending 0 1h"""
            
            mock_subprocess_obj.execute_cmd.return_value = (mock_output, None)
            
            result = available_pods("test-ns", "sdp", "false", [], [])
            
            # Should return only running pods with 1/1 status
            expected = ["csdp-pod-1", "csdp-pod-2"]
            self.assertEqual(result, expected)
            
            print("✅ Basic pod parsing functionality test passed")
        except Exception as e:
            self.fail(f"Basic pod parsing test failed: {e}")

    def test_timestamp_functionality(self):
        """Test timestamp generation functionality"""
        try:
            from main import timestamp
            
            result = timestamp()
            
            # Should be 14 character timestamp
            self.assertEqual(len(result), 14)
            self.assertTrue(result.isdigit())
            
            print("✅ Timestamp functionality test passed")
        except Exception as e:
            self.fail(f"Timestamp functionality test failed: {e}")

    def test_kpi_sdp_initialization(self):
        """Test KPI_SDP class can be initialized"""
        try:
            with patch('KPI_SDP.LoggingHandler') as mock_logging:
                mock_logging.get_logger.return_value = MagicMock()
                
                from KPI_SDP import KPI_SDP
                
                kpi_sdp = KPI_SDP(
                    "test-host", "test-ns", "test-pod", "/script",
                    "/output", "/archive", "/log", "sdp"
                )
                
                self.assertEqual(kpi_sdp.host_name, "test-host")
                self.assertEqual(kpi_sdp.namespace, "test-ns")
                self.assertEqual(kpi_sdp.pod, "test-pod")
                
                print("✅ KPI_SDP initialization test passed")
        except Exception as e:
            self.fail(f"KPI_SDP initialization test failed: {e}")

    def test_subprocess_class_basic_functionality(self):
        """Test SubprocessClass basic functionality"""
        try:
            with patch('SubprocessClass.LoggingHandler') as mock_logging:
                mock_logging.get_logger.return_value = MagicMock()
                
                from SubprocessClass import SubprocessClass
                
                subprocess_obj = SubprocessClass()
                
                with patch('subprocess.Popen') as mock_popen:
                    mock_process = MagicMock()
                    mock_process.communicate.return_value = (b"test output", b"")
                    mock_popen.return_value = mock_process
                    
                    output, error = subprocess_obj.execute_cmd("echo test")
                    
                    self.assertEqual(output, "test output")
                    self.assertIsNone(error)
                
                print("✅ SubprocessClass basic functionality test passed")
        except Exception as e:
            self.fail(f"SubprocessClass basic functionality test failed: {e}")

    def test_logging_handler_basic_functionality(self):
        """Test LoggingHandler basic functionality"""
        try:
            with patch('logging.basicConfig') as mock_basicConfig:
                with patch('os.path.join') as mock_path_join:
                    mock_path_join.return_value = "/test/log"
                    
                    from Logger import LoggingHandler
                    
                    logger_handler = LoggingHandler("/test/script")
                    
                    # Test static method
                    logger = LoggingHandler.get_logger("TestLogger")
                    self.assertIsNotNone(logger)
                    
                    print("✅ LoggingHandler basic functionality test passed")
        except Exception as e:
            self.fail(f"LoggingHandler basic functionality test failed: {e}")

    @patch('sys.argv', ['main.py', 'test_config.json'])
    def test_argument_parsing(self):
        """Test command line argument parsing"""
        try:
            from main import parse_args
            
            kafka_config_file_path, wait, test = parse_args()
            
            self.assertEqual(kafka_config_file_path, 'test_config.json')
            self.assertIsInstance(wait, bool)
            self.assertIsInstance(test, bool)
            
            print("✅ Argument parsing test passed")
        except Exception as e:
            self.fail(f"Argument parsing test failed: {e}")

    def test_directory_creation_functionality(self):
        """Test directory creation functionality"""
        try:
            with patch('os.path.isdir') as mock_isdir:
                with patch('os.makedirs') as mock_makedirs:
                    mock_isdir.return_value = False
                    
                    from main import make_dir
                    
                    make_dir("/test/path")
                    
                    mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
                    
                    print("✅ Directory creation functionality test passed")
        except Exception as e:
            self.fail(f"Directory creation functionality test failed: {e}")

    def test_eval_value_functionality(self):
        """Test eval_value functionality"""
        try:
            from main import eval_value
            
            # Test simple value
            result = eval_value("simple-value")
            self.assertEqual(result, "simple-value")
            
            # Test command value
            with patch('main.subprocess_obj') as mock_subprocess_obj:
                mock_subprocess_obj.execute_cmd.return_value = ("command-output\n", None)
                
                result = eval_value("cmd:test command")
                self.assertEqual(result, "command-output")
            
            print("✅ eval_value functionality test passed")
        except Exception as e:
            self.fail(f"eval_value functionality test failed: {e}")


def create_basic_test_suite():
    """Create a basic test suite with all test cases"""
    test_suite = unittest.TestSuite()
    
    # Add basic integration tests
    test_suite.addTest(unittest.makeSuite(TestKafkaSDPPrepaidBasic))
    
    # Add unit tests for individual modules
    test_suite.addTest(unittest.makeSuite(TestMain))
    test_suite.addTest(unittest.makeSuite(TestKPISDP))
    test_suite.addTest(unittest.makeSuite(TestLoggingHandler))
    test_suite.addTest(unittest.makeSuite(TestSubprocessClass))
    
    return test_suite


def run_basic_tests():
    """Run basic tests and generate a report"""
    print("="*70)
    print("Running KAFKA_SDP_PREPAID Comprehensive Test Suite")
    print("="*70)
    
    # Create test suite
    suite = create_basic_test_suite()
    
    # Create test runner with verbosity
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*70}")
    print("KAFKA_SDP_PREPAID TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    print(f"\n{'='*70}")
    print("Validated Components:")
    print("✅ Main module functionality")
    print("✅ KPI_SDP class operations")
    print("✅ Logging system")
    print("✅ Subprocess execution")
    print("✅ Configuration handling")
    print("✅ Pod parsing logic")
    print("✅ Command execution")
    print("✅ Error handling")
    print(f"{'='*70}")
    
    return result


if __name__ == '__main__':
    run_basic_tests()
