import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMainModule(unittest.TestCase):
    """Test cases for main.py module functions with proper mocking"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_config = {
            "wait_to_start_secs": 100,
            "namespace": "test-namespace",
            "pod": "sdp",
            "pod_container": "sdp", 
            "max_processes": 3,
            "whitelist_pod_enable": "false",
            "whitelist_pods": [],
            "blacklist_pods": [],
            "kafka_message_template": {
                "category": "CORE - IN",
                "platform": "ERICSSON_SDP",
                "source_owner": "Tier2_CC"
            }
        }

    def test_timestamp_format_validation(self):
        """Test timestamp function returns correct format"""
        from main import timestamp
        result = timestamp()
        
        # Check that result is a string
        self.assertIsInstance(result, str)
        
        # Check format YYYYMMDDHHMMSS (14 characters)
        self.assertEqual(len(result), 14)
        
        # Check that it's all digits
        self.assertTrue(result.isdigit())
        
        # Check that it represents a valid datetime
        try:
            datetime.strptime(result, "%Y%m%d%H%M%S")
        except ValueError:
            self.fail("timestamp() did not return valid datetime format")
        
        print("✅ Timestamp format validation test passed")

    @patch('sys.argv', ['main.py', 'test_kafka_config.json'])
    def test_parse_args_basic_arguments(self):
        """Test parse_args with basic arguments"""
        from main import parse_args
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_kafka_config.json')
        self.assertFalse(wait)
        self.assertFalse(test)
        
        print("✅ Parse args basic arguments test passed")

    @patch('sys.argv', ['main.py', 'test_kafka_config.json', '--wait', '--test'])
    def test_parse_args_with_flags(self):
        """Test parse_args with optional flags"""
        from main import parse_args
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_kafka_config.json')
        self.assertTrue(wait)
        self.assertTrue(test)
        
        print("✅ Parse args with flags test passed")

    def test_eval_value_without_command_prefix(self):
        """Test eval_value without command prefix"""
        from main import eval_value
        result = eval_value("simple-value")
        
        self.assertEqual(result, "simple-value")
        
        print("✅ Eval value without command prefix test passed")

    @patch('time.sleep')
    @patch('main.logger')
    def test_wait_to_start_function(self, mock_logger, mock_sleep):
        """Test wait_to_start function with mocked logger"""
        from main import wait_to_start
        wait_to_start(30)
        
        mock_sleep.assert_called_once_with(30)
        
        print("✅ Wait to start function test passed")

    @patch('os.path.isdir', return_value=False)
    @patch('os.makedirs')
    def test_make_dir_creates_new_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir creates new directory"""
        from main import make_dir
        make_dir("/test/path")
        
        mock_isdir.assert_called_once_with("/test/path")
        mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
        
        print("✅ Make dir creates new directory test passed")

    @patch('os.path.isdir', return_value=True)
    @patch('os.makedirs')
    def test_make_dir_existing_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir with existing directory"""
        from main import make_dir
        make_dir("/existing/path")
        
        mock_isdir.assert_called_once_with("/existing/path")
        mock_makedirs.assert_not_called()
        
        print("✅ Make dir existing directory test passed")

    def test_module_has_required_functions(self):
        """Test that main module has all required functions"""
        import main
        
        required_functions = [
            'timestamp', 'parse_args', 'load_config', 'eval_value',
            'wait_to_start', 'make_dir', 'fetch_hostname', 'available_pods',
            'main'
        ]
        
        for func_name in required_functions:
            self.assertTrue(hasattr(main, func_name), f"Missing function: {func_name}")
        
        print("✅ Module has required functions test passed")

    def test_configuration_files_structure(self):
        """Test that required configuration files structure exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check if config directory exists
        config_dir = os.path.join(script_dir, 'config')
        self.assertTrue(os.path.exists(config_dir), f"Config directory does not exist: {config_dir}")
        
        # Check if config.json exists
        config_file = os.path.join(config_dir, 'config.json')
        self.assertTrue(os.path.exists(config_file), f"config.json does not exist: {config_file}")
        
        print("✅ Configuration files structure test passed")

    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file"""
        with patch('main.logger'):
            from main import load_config
            with self.assertRaises(FileNotFoundError):
                load_config("non_existent_config.json")
        
        print("✅ Load config file not found test passed")

    def test_load_config_invalid_json(self):
        """Test load_config with invalid JSON"""
        with patch('main.logger'):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                from main import load_config
                with self.assertRaises(json.JSONDecodeError):
                    load_config("invalid_config.json")
        
        print("✅ Load config invalid JSON test passed")


if __name__ == '__main__':
    print("=" * 70)
    print("Running KAFKA_SDP_POSTPAID Main Module Tests")
    print("=" * 70)
    unittest.main(verbosity=2)
