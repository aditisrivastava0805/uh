import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMainModuleFunctions(unittest.TestCase):
    """Test cases for main.py module functions that can be safely tested"""

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

    def test_timestamp_functionality(self):
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
        
        print("✅ timestamp functionality test passed")

    @patch('sys.argv', ['main.py', 'test_config.json'])
    def test_parse_args_basic(self):
        """Test parse_args with basic arguments"""
        from main import parse_args
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_config.json')
        self.assertFalse(wait)
        self.assertFalse(test)
        
        print("✅ parse_args basic test passed")

    @patch('sys.argv', ['main.py', 'test_config.json', '--wait', '--test'])
    def test_parse_args_with_flags(self):
        """Test parse_args with optional flags"""
        from main import parse_args
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_config.json')
        self.assertTrue(wait)
        self.assertTrue(test)
        
        print("✅ parse_args with flags test passed")

    @patch('os.path.isdir', return_value=False)
    @patch('os.makedirs')
    def test_make_dir_new_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir creates new directory"""
        from main import make_dir
        make_dir("/test/path")
        
        mock_isdir.assert_called_once_with("/test/path")
        mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
        
        print("✅ make_dir new directory test passed")

    @patch('os.path.isdir', return_value=True)
    @patch('os.makedirs')
    def test_make_dir_existing_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir with existing directory"""
        from main import make_dir
        make_dir("/existing/path")
        
        mock_isdir.assert_called_once_with("/existing/path")
        mock_makedirs.assert_not_called()
        
        print("✅ make_dir existing directory test passed")

    def test_eval_value_without_command(self):
        """Test eval_value without command prefix"""
        from main import eval_value
        result = eval_value("simple-value")
        
        self.assertEqual(result, "simple-value")
        
        print("✅ eval_value without command test passed")

    @patch('main.logger')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_basic(self, mock_file, mock_logger):
        """Test load_config function with mocked logger"""
        mock_file.return_value.read.return_value = json.dumps(self.sample_config)
        
        # Mock the eval_value function to avoid subprocess issues
        with patch('main.eval_value') as mock_eval_value:
            mock_eval_value.return_value = "test-namespace"
            
            from main import load_config
            result = load_config("test_config.json")
            
            wait_to_start_secs, namespace, pod, kafka_data_source_template, whitelist_pod_enable, whitelist_pods, max_processes, pod_container, blacklist_pods = result
            
            self.assertEqual(wait_to_start_secs, 100)
            self.assertEqual(namespace, "test-namespace")
            self.assertEqual(pod, "sdp")
            self.assertEqual(max_processes, 3)
            self.assertEqual(pod_container, "sdp")
        
        print("✅ load_config basic test passed")

    @patch('time.sleep')
    @patch('main.logger')
    def test_wait_to_start(self, mock_logger, mock_sleep):
        """Test wait_to_start function with mocked logger"""
        from main import wait_to_start
        wait_to_start(30)
        
        mock_sleep.assert_called_once_with(30)
        
        print("✅ wait_to_start test passed")

    @patch('main.ARCHIVE_DIR', '/test/archive')
    @patch('main.HOSTNAME', 'test-host')
    def test_make_kafka_data_source_file_path(self):
        """Test make_kafka_data_source_file_path function"""
        with patch('main.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20230101120000"
            
            from main import make_kafka_data_source_file_path
            result = make_kafka_data_source_file_path("test-pod")
            
            expected_path = os.path.join('/test/archive', 'test-host_test-pod_KPI.txt.20230101120000')
            # Normalize path separators for cross-platform testing
            expected_path = expected_path.replace('\\', '/')
            result = result.replace('\\', '/')
            
            self.assertEqual(result, expected_path)
        
        print("✅ make_kafka_data_source_file_path test passed")

    def test_module_file_structure(self):
        """Test that main module has expected structure"""
        import main
        
        expected_functions = [
            'timestamp', 'parse_args', 'make_dir', 'eval_value'
        ]
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(main, func_name), f"Missing function: {func_name}")
        
        print("✅ Module file structure test passed")

    def test_configuration_directory_structure(self):
        """Test configuration directory exists"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(script_dir, 'config')
        
        self.assertTrue(os.path.exists(config_dir), f"Config directory should exist at {config_dir}")
        
        print("✅ Configuration directory structure test passed")


if __name__ == '__main__':
    print("=" * 70)
    print("Running KAFKA_SDP_PREPAID Comprehensive Tests (Error-Free Version)")
    print("=" * 70)
    unittest.main(verbosity=2)
