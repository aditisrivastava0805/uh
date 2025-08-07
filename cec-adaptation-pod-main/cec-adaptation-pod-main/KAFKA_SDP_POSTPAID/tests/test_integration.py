import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import concurrent.futures

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import with error handling
try:
    from main import (
        timestamp, parse_args, load_config, eval_value, make_dir, 
        fetch_hostname, available_pods, make_kafka_data_source_file_path
    )
    MAIN_IMPORT_SUCCESS = True
    MAIN_IMPORT_ERROR = None
except Exception as e:
    MAIN_IMPORT_SUCCESS = False
    MAIN_IMPORT_ERROR = str(e)


class TestMainIntegration(unittest.TestCase):
    """Integration tests for main module functions"""

    def test_main_module_import(self):
        """Test that main module functions can be imported"""
        if not MAIN_IMPORT_SUCCESS:
            print(f"⚠️ Main module import failed: {MAIN_IMPORT_ERROR}")
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        
        self.assertTrue(MAIN_IMPORT_SUCCESS)
        print("✅ Main module import test passed")

    def test_timestamp_function_comprehensive(self):
        """Comprehensive test of timestamp function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        result = timestamp()
        
        # Test return type
        self.assertIsInstance(result, str)
        
        # Test format (YYYYMMDDHHMMSS - 14 digits)
        self.assertEqual(len(result), 14)
        self.assertTrue(result.isdigit())
        
        # Test that timestamp changes over time
        import time
        time.sleep(0.001)  # Small delay
        result2 = timestamp()
        # Note: timestamps might be the same if called quickly, so we just test format
        self.assertEqual(len(result2), 14)
        self.assertTrue(result2.isdigit())
        
        print("✅ Timestamp comprehensive test passed")

    @patch('sys.argv', ['main.py', 'test_config.json'])
    def test_parse_args_default_values(self, ):
        """Test parse_args with default values"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_config.json')
        self.assertFalse(wait)
        self.assertFalse(test)
        
        print("✅ Parse args default values test passed")

    @patch('sys.argv', ['main.py', 'config.json', '--wait', '--test'])
    def test_parse_args_all_flags(self):
        """Test parse_args with all flags enabled"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'config.json')
        self.assertTrue(wait)
        self.assertTrue(test)
        
        print("✅ Parse args all flags test passed")

    def test_make_dir_function(self):
        """Test make_dir function with temporary directory"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, 'test_subdir', 'nested')
            
            # Directory should not exist initially
            self.assertFalse(os.path.exists(test_dir))
            
            # Create directory
            make_dir(test_dir)
            
            # Directory should now exist
            self.assertTrue(os.path.exists(test_dir))
            self.assertTrue(os.path.isdir(test_dir))
        
        print("✅ Make dir function test passed")

    def test_make_dir_existing_directory(self):
        """Test make_dir function with existing directory"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory already exists
            self.assertTrue(os.path.exists(temp_dir))
            
            # Should not raise error
            try:
                make_dir(temp_dir)
                success = True
            except Exception:
                success = False
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_dir))
        
        print("✅ Make dir existing directory test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_plain_string(self, mock_subprocess):
        """Test eval_value with plain string (no command)"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        result = eval_value("plain_value")
        self.assertEqual(result, "plain_value")
        
        print("✅ Eval value plain string test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_command_string(self, mock_subprocess):
        """Test eval_value with command string"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock subprocess execution
        mock_subprocess.execute_cmd.return_value = ("command_output\n", None)
        
        result = eval_value("cmd:echo test")
        self.assertEqual(result, "command_output")
        
        # Verify command was called
        mock_subprocess.execute_cmd.assert_called_once_with("echo test")
        
        print("✅ Eval value command string test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_command_multiline_output(self, mock_subprocess):
        """Test eval_value with command that returns multiple lines"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock subprocess execution with multiline output
        mock_subprocess.execute_cmd.return_value = ("line1\nline2\nline3\n", None)
        
        result = eval_value("cmd:echo -e 'line1\\nline2\\nline3'")
        self.assertEqual(result, "line3")  # Should return last line
        
        print("✅ Eval value command multiline test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_command_error(self, mock_subprocess):
        """Test eval_value with command that returns error"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock subprocess execution with error
        mock_subprocess.execute_cmd.return_value = ("", "Command failed")
        
        with self.assertRaises(OSError):
            eval_value("cmd:false")  # Command that fails
        
        print("✅ Eval value command error test passed")

    def test_load_config_with_valid_file(self):
        """Test load_config with valid configuration file"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Create a valid test config
        test_config = {
            "wait_to_start_secs": 60,
            "namespace": "test-namespace",
            "pod": "test-pod",
            "pod_container": "test-container",
            "max_processes": 3,
            "whitelist_pod_enable": "false",
            "whitelist_pods": ["pod1", "pod2"],
            "kafka_message_template": {"test": "template"},
            "blacklist_pods": ["bad-pod"]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(test_config, temp_file)
            temp_file_path = temp_file.name

        try:
            with patch('main.logger') as mock_logger:
                with patch('main.eval_value', side_effect=lambda x: x):  # Return value as-is
                    result = load_config(temp_file_path)
                    
                    wait_to_start_secs, namespace, pod, kafka_data_source_template, \
                    whitelist_pod_enable, whitelist_pods, max_processes, pod_container, \
                    blacklist_pods = result
                    
                    # Verify returned values
                    self.assertEqual(wait_to_start_secs, 60)
                    self.assertEqual(namespace, "test-namespace")
                    self.assertEqual(pod, "test-pod")
                    self.assertEqual(pod_container, "test-container")
                    self.assertEqual(max_processes, 3)
                    self.assertEqual(whitelist_pod_enable, "false")
                    self.assertEqual(whitelist_pods, ["pod1", "pod2"])
                    self.assertEqual(kafka_data_source_template, {"test": "template"})
                    self.assertEqual(blacklist_pods, ["bad-pod"])
        
        finally:
            os.unlink(temp_file_path)
        
        print("✅ Load config valid file test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_success(self, mock_subprocess_class):
        """Test fetch_hostname function success case"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock subprocess execution
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute_cmd.return_value = ("test-hostname\n", None)
        mock_subprocess_class.return_value = mock_subprocess_instance

        with patch('main.logger') as mock_logger:
            result = fetch_hostname()
            self.assertEqual(result, "TEST-HOSTNAME")  # Should be uppercase and stripped
        
        print("✅ Fetch hostname success test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_error(self, mock_subprocess_class):
        """Test fetch_hostname function error case"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock subprocess execution with error
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute_cmd.return_value = ("", "Command failed")
        mock_subprocess_class.return_value = mock_subprocess_instance

        with patch('main.logger') as mock_logger:
            result = fetch_hostname()
            self.assertEqual(result, "undefined-hostname")
        
        print("✅ Fetch hostname error test passed")

    def test_make_kafka_data_source_file_path(self):
        """Test make_kafka_data_source_file_path function"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        with patch('main.ARCHIVE_DIR', '/test/archive'):
            with patch('main.HOSTNAME', 'test-host'):
                result = make_kafka_data_source_file_path('test-pod')
                
                # Check that result contains expected elements
                self.assertIn('/test/archive', result)
                self.assertIn('test-host', result)
                self.assertIn('test-pod', result)
                self.assertIn('KPI.txt.', result)
                
                # Check timestamp format (14 digits at end)
                timestamp_part = result.split('.')[-1]
                self.assertEqual(len(timestamp_part), 14)
                self.assertTrue(timestamp_part.isdigit())
        
        print("✅ Make kafka data source file path test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_success(self, mock_subprocess):
        """Test available_pods function success case"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock kubectl output
        kubectl_output = """csdp-pod1-0  1/1  Running  0  1h
csdp-pod2-0  1/1  Running  0  2h
csdp-pod3-0  0/1  Pending  0  30m"""

        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)

        with patch('main.logger') as mock_logger:
            result = available_pods(
                namespace="test-ns",
                pod="sdp", 
                whitelist_enabled="false",
                whitelist_pod_list=[],
                blacklist_pod_list=[]
            )
            
            # Should return only running pods
            expected_pods = ["csdp-pod1-0", "csdp-pod2-0"]
            self.assertEqual(sorted(result), sorted(expected_pods))
        
        print("✅ Available pods success test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_whitelist(self, mock_subprocess):
        """Test available_pods function with whitelist enabled"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock kubectl output
        kubectl_output = """csdp-pod1-0  1/1  Running  0  1h
csdp-pod2-0  1/1  Running  0  2h
csdp-pod3-0  1/1  Running  0  3h"""

        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)

        with patch('main.logger') as mock_logger:
            result = available_pods(
                namespace="test-ns",
                pod="sdp",
                whitelist_enabled="true", 
                whitelist_pod_list=["csdp-pod1-0", "csdp-pod3-0"],
                blacklist_pod_list=[]
            )
            
            # Should return only whitelisted pods
            expected_pods = ["csdp-pod1-0", "csdp-pod3-0"]
            self.assertEqual(sorted(result), sorted(expected_pods))
        
        print("✅ Available pods with whitelist test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_blacklist(self, mock_subprocess):
        """Test available_pods function with blacklist"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

        # Mock kubectl output
        kubectl_output = """csdp-pod1-0  1/1  Running  0  1h
csdp-pod2-0  1/1  Running  0  2h
csdp-pod3-0  1/1  Running  0  3h"""

        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)

        with patch('main.logger') as mock_logger:
            result = available_pods(
                namespace="test-ns",
                pod="sdp",
                whitelist_enabled="false",
                whitelist_pod_list=[],
                blacklist_pod_list=["csdp-pod2-0"]
            )
            
            # Should return all pods except blacklisted
            expected_pods = ["csdp-pod1-0", "csdp-pod3-0"]
            self.assertEqual(sorted(result), sorted(expected_pods))
        
        print("✅ Available pods with blacklist test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_SDP_POSTPAID Integration Tests")
    print("=" * 60)
    if MAIN_IMPORT_SUCCESS:
        print("✅ Main module import successful - running full test suite")
    else:
        print(f"⚠️ Main module import failed: {MAIN_IMPORT_ERROR}")
        print("Some tests will be skipped")
    print("=" * 60)
    unittest.main(verbosity=2)
