import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from main import (
    timestamp, 
    parse_args, 
    load_config, 
    eval_value, 
    wait_to_start, 
    make_dir, 
    fetch_hostname, 
    available_pods,
    make_kafka_data_source_file_path,
    execute,
    main
)


class TestMain(unittest.TestCase):
    """Test cases for main.py module"""

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

    def test_timestamp(self):
        """Test timestamp function returns correct format"""
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
        
        print("✅ timestamp test passed")

    @patch('sys.argv', ['main.py', 'test_kafka_config.json'])
    def test_parse_args_basic(self):
        """Test parse_args with basic arguments"""
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_kafka_config.json')
        self.assertFalse(wait)
        self.assertFalse(test)
        
        print("✅ parse_args basic test passed")

    @patch('sys.argv', ['main.py', 'test_kafka_config.json', '--wait', '--test'])
    def test_parse_args_with_flags(self):
        """Test parse_args with optional flags"""
        kafka_config_file_path, wait, test = parse_args()
        
        self.assertEqual(kafka_config_file_path, 'test_kafka_config.json')
        self.assertTrue(wait)
        self.assertTrue(test)
        
        print("✅ parse_args with flags test passed")    @patch('builtins.open', new_callable=mock_open)
    @patch('main.logger')
    def test_load_config(self, mock_logger, mock_file):
        """Test load_config function"""
        mock_file.return_value.read.return_value = json.dumps(self.sample_config)
        
        with patch('main.eval_value') as mock_eval_value:
            mock_eval_value.return_value = "test-namespace"
            
            result = load_config("test_config.json")
            
            wait_to_start_secs, namespace, pod, kafka_data_source_template, whitelist_pod_enable, whitelist_pods, max_processes, pod_container, blacklist_pods = result
            
            self.assertEqual(wait_to_start_secs, 100)
            self.assertEqual(namespace, "test-namespace")
            self.assertEqual(pod, "sdp")
            self.assertEqual(max_processes, 3)
            self.assertEqual(pod_container, "sdp")
        
        print("✅ load_config test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_command(self, mock_subprocess_obj):
        """Test eval_value with command prefix"""
        mock_subprocess_obj.execute_cmd.return_value = ("test-output\n", None)
        
        result = eval_value("cmd:kubectl get ns")
        
        self.assertEqual(result, "test-output")
        mock_subprocess_obj.execute_cmd.assert_called_once_with("kubectl get ns")
        
        print("✅ eval_value with command test passed")

    def test_eval_value_without_command(self):
        """Test eval_value without command prefix"""
        result = eval_value("simple-value")
        
        self.assertEqual(result, "simple-value")
        
        print("✅ eval_value without command test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_error(self, mock_subprocess_obj):
        """Test eval_value with command error"""
        mock_subprocess_obj.execute_cmd.return_value = (None, "Command failed")
        
        with self.assertRaises(OSError):
            eval_value("cmd:invalid command")
        
        print("✅ eval_value with error test passed")

    @patch('time.sleep')
    def test_wait_to_start(self, mock_sleep):
        """Test wait_to_start function"""
        wait_to_start(30)
        
        mock_sleep.assert_called_once_with(30)
        
        print("✅ wait_to_start test passed")

    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_make_dir_new_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir creates new directory"""
        mock_isdir.return_value = False
        
        make_dir("/test/path")
        
        mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
        
        print("✅ make_dir new directory test passed")

    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_make_dir_existing_directory(self, mock_makedirs, mock_isdir):
        """Test make_dir with existing directory"""
        mock_isdir.return_value = True
        
        make_dir("/test/path")
        
        mock_makedirs.assert_not_called()
        
        print("✅ make_dir existing directory test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_success(self, mock_subprocess_class):
        """Test fetch_hostname success"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("test-hostname\n", None)
        
        result = fetch_hostname()
        
        self.assertEqual(result, "TEST-HOSTNAME")
        
        print("✅ fetch_hostname success test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_error(self, mock_subprocess_class):
        """Test fetch_hostname with error"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = (None, "Command failed")
        
        result = fetch_hostname()
        
        self.assertEqual(result, "undefined-hostname")
        
        print("✅ fetch_hostname error test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_success(self, mock_subprocess_obj):
        """Test available_pods function with successful pod retrieval"""
        mock_output = """csdp-pod-1 1/1 Running 0 1d
csdp-pod-2 1/1 Running 0 2d
csdp-pod-3 0/1 Pending 0 1h"""
        
        mock_subprocess_obj.execute_cmd.return_value = (mock_output, None)
        
        result = available_pods("test-ns", "sdp", "false", [], [])
        
        # Only running pods with 1/1 status should be included
        expected = ["csdp-pod-1", "csdp-pod-2"]
        self.assertEqual(result, expected)
        
        print("✅ available_pods success test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_whitelist(self, mock_subprocess_obj):
        """Test available_pods function with whitelist enabled"""
        mock_output = """csdp-pod-1 1/1 Running 0 1d
csdp-pod-2 1/1 Running 0 2d
csdp-pod-3 1/1 Running 0 3d"""
        
        mock_subprocess_obj.execute_cmd.return_value = (mock_output, None)
        
        whitelist = ["csdp-pod-1", "csdp-pod-3"]
        result = available_pods("test-ns", "sdp", "true", whitelist, [])
        
        # Only whitelisted pods should be included
        expected = ["csdp-pod-1", "csdp-pod-3"]
        self.assertEqual(result, expected)
        
        print("✅ available_pods with whitelist test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_blacklist(self, mock_subprocess_obj):
        """Test available_pods function with blacklist"""
        mock_output = """csdp-pod-1 1/1 Running 0 1d
csdp-pod-2 1/1 Running 0 2d
csdp-pod-3 1/1 Running 0 3d"""
        
        mock_subprocess_obj.execute_cmd.return_value = (mock_output, None)
        
        blacklist = ["csdp-pod-2"]
        result = available_pods("test-ns", "sdp", "false", [], blacklist)
        
        # Blacklisted pods should be excluded
        expected = ["csdp-pod-1", "csdp-pod-3"]
        self.assertEqual(result, expected)
        
        print("✅ available_pods with blacklist test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_error(self, mock_subprocess_obj):
        """Test available_pods function with command error"""
        mock_subprocess_obj.execute_cmd.return_value = (None, "Command failed")
        
        result = available_pods("test-ns", "sdp", "false", [], [])
        
        self.assertEqual(result, [])
        
        print("✅ available_pods error test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_no_pods_found(self, mock_subprocess_obj):
        """Test available_pods function with no pods found"""
        mock_subprocess_obj.execute_cmd.return_value = ("", None)
        
        result = available_pods("test-ns", "sdp", "false", [], [])
        
        self.assertEqual(result, [])
        
        print("✅ available_pods no pods found test passed")

    @patch('main.datetime')
    @patch('main.ARCHIVE_DIR', '/test/archive')
    @patch('main.HOSTNAME', 'test-host')
    def test_make_kafka_data_source_file_path(self, mock_datetime):
        """Test make_kafka_data_source_file_path function"""
        mock_now = datetime(2023, 7, 15, 14, 30, 45)
        mock_datetime.now.return_value = mock_now
        
        result = make_kafka_data_source_file_path("test-pod")
        
        expected = "/test/archive/test-host_test-pod_KPI.txt.20230715143045"
        self.assertEqual(result, expected)
        
        print("✅ make_kafka_data_source_file_path test passed")

    @patch('main.KPI_SDP')
    @patch('main.KafkaDataSourceBuilder')
    @patch('main.kafka_process')
    @patch('main.make_kafka_data_source_file_path')
    @patch('main.ARCHIVE_DIR', '/test/archive')
    @patch('main.HOSTNAME', 'test-host')
    @patch('main.TIMESTAMP', '20230715143045')
    def test_execute_function(self, mock_make_path, mock_kafka_process, mock_builder_class, mock_kpi_class):
        """Test execute function"""
        # Setup mocks
        mock_kpi_instance = MagicMock()
        mock_kpi_class.return_value = mock_kpi_instance
        
        mock_builder_instance = MagicMock()
        mock_builder_class.return_value = mock_builder_instance
        
        mock_make_path.return_value = "/test/archive/test-host_test-pod_KPI.txt.20230715143045"
        
        # Call function
        execute("test-pod", 0, {}, "test-host", "test-ns", "sdp", "/script", "/output", 
                "/archive", "/log", "/kafka/config", False, "sdp")
        
        # Assertions
        mock_kpi_class.assert_called_once_with("test-host", "test-ns", "sdp", "/script", 
                                               "/output", "/archive", "/log", "sdp")
        mock_kpi_instance.main.assert_called_once()
        mock_builder_instance.write_to_file.assert_called_once()
        mock_kafka_process.assert_called_once()
        
        print("✅ execute function test passed")

    @patch('main.available_pods')
    @patch('concurrent.futures.ProcessPoolExecutor')
    def test_main_function(self, mock_executor, mock_available_pods):
        """Test main function"""
        # Setup mocks
        mock_available_pods.return_value = ["pod1", "pod2", "pod3"]
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Call function
        main("test-host", "test-ns", "sdp", {}, "/script", "/output", "/archive", 
             "/log", "/kafka/config", "false", [], False, 3, "sdp", [])
        
        # Assertions
        mock_available_pods.assert_called_once_with("test-ns", "sdp", "false", [], [])
        self.assertEqual(mock_executor_instance.submit.call_count, 3)
        
        print("✅ main function test passed")

    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            load_config("non_existent_config.json")
        
        print("✅ load_config file not found test passed")

    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": "json"')
    def test_load_config_invalid_json(self, mock_file):
        """Test load_config with invalid JSON"""
        with self.assertRaises(json.JSONDecodeError):
            load_config("invalid_config.json")
        
        print("✅ load_config invalid JSON test passed")

    def test_eval_value_multiline_output(self):
        """Test eval_value with multiline command output"""
        with patch('main.subprocess_obj') as mock_subprocess_obj:
            mock_subprocess_obj.execute_cmd.return_value = ("line1\nline2\nline3\n", None)
            
            result = eval_value("cmd:test command")
            
            # Should return the last line
            self.assertEqual(result, "line3")
        
        print("✅ eval_value multiline output test passed")


if __name__ == '__main__':
    print("="*60)
    print("Running KAFKA_SDP_PREPAID Main Module Tests")
    print("="*60)
    unittest.main(verbosity=2)
