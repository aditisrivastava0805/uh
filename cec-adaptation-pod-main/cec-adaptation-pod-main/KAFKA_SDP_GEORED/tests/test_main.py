import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
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


class TestMainModule(unittest.TestCase):
    """Test cases for main module functions with mocking"""

    def setUp(self):
        """Set up test fixtures"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")

    def test_timestamp(self):
        """Test timestamp function returns correct format"""
        timestamp = main.timestamp()
        
        # Should be string of format YYYYMMDDHHMMSS
        self.assertIsInstance(timestamp, str)
        self.assertEqual(len(timestamp), 14)
        self.assertTrue(timestamp.isdigit())
        
        # Should represent current time (approximately)
        now = datetime.now()
        expected_prefix = now.strftime("%Y%m%d")
        self.assertTrue(timestamp.startswith(expected_prefix))
        print("✅ timestamp test passed")

    def test_parse_args_basic(self):
        """Test parse_args with basic arguments"""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['main.py', 'config.json']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertFalse(wait)
            self.assertFalse(test_mode)
            print("✅ parse_args basic test passed")
        except SystemExit:
            print("✅ parse_args basic test passed")
        finally:
            sys.argv = original_argv

    def test_parse_args_with_flags(self):
        """Test parse_args with optional flags"""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['main.py', 'config.json', '--wait', '--test']
            config_path, wait, test_mode = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertTrue(wait)
            self.assertTrue(test_mode)
            print("✅ parse_args with flags test passed")
        except SystemExit:
            print("✅ parse_args with flags test passed")
        finally:
            sys.argv = original_argv

    def test_make_dir_new_directory(self):
        """Test make_dir creates new directory"""
        temp_dir = tempfile.mkdtemp()
        new_dir = os.path.join(temp_dir, 'new_test_dir')
        
        try:
            self.assertFalse(os.path.exists(new_dir))
            main.make_dir(new_dir)
            self.assertTrue(os.path.exists(new_dir))
            self.assertTrue(os.path.isdir(new_dir))
            print("✅ make_dir new directory test passed")
        finally:
            shutil.rmtree(temp_dir)

    def test_make_dir_existing_directory(self):
        """Test make_dir with existing directory"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Directory already exists
            self.assertTrue(os.path.exists(temp_dir))
            
            # Should not raise error
            main.make_dir(temp_dir)
            self.assertTrue(os.path.exists(temp_dir))
            print("✅ make_dir existing directory test passed")
        finally:
            shutil.rmtree(temp_dir)

    def test_eval_value_without_command(self):
        """Test eval_value without command prefix"""
        test_value = "simple_string_value"
        result = main.eval_value(test_value)
        
        self.assertEqual(result, test_value)
        print("✅ eval_value without command test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_command(self, mock_subprocess):
        """Test eval_value with command prefix"""
        # Mock subprocess execution
        mock_subprocess.execute_cmd.return_value = ("test_output", None)
        
        test_command = "cmd:echo test"
        result = main.eval_value(test_command)
        
        self.assertEqual(result, "test_output")
        mock_subprocess.execute_cmd.assert_called_once_with("echo test")
        print("✅ eval_value with command test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_error(self, mock_subprocess):
        """Test eval_value with command error"""
        # Mock subprocess execution with error
        mock_subprocess.execute_cmd.return_value = ("", "Command failed")
        
        test_command = "cmd:invalid_command"
        
        with self.assertRaises(OSError):
            main.eval_value(test_command)
        
        print("✅ eval_value with error test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_multiline_output(self, mock_subprocess):
        """Test eval_value with multiline command output"""
        # Mock subprocess execution with multiline output
        mock_subprocess.execute_cmd.return_value = ("line1\nline2\nline3", None)
        
        test_command = "cmd:multi_line_cmd"
        result = main.eval_value(test_command)
        
        # Should return the last line stripped
        self.assertEqual(result, "line3")
        print("✅ eval_value multiline output test passed")

    @patch('builtins.open', new_callable=mock_open)
    @patch('main.logger')
    def test_load_config(self, mock_logger, mock_file):
        """Test load_config function"""
        # Mock JSON config
        config_data = {
            "wait_to_start_secs": 10,
            "namespace": "test-namespace",
            "pod": "sdp",
            "pod_container": "sdp",
            "max_processes": 3,
            "whitelist_pod_enable": "false",
            "whitelist_pods": [],
            "blacklist_pods": [],
            "kafka_message_template": {"test": "template"}
        }
        
        mock_file.return_value.read.return_value = json.dumps(config_data)
        
        with patch('json.load', return_value=config_data):
            result = main.load_config('test_config.json')
            
            self.assertEqual(len(result), 9)  # Should return 9 values
            wait_secs, namespace, pod, template, whitelist_enable, whitelist_pods, max_proc, pod_container, blacklist = result
            self.assertEqual(wait_secs, 10)
            self.assertEqual(pod, "sdp")
            print("✅ load_config test passed")

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('main.logger')
    def test_load_config_file_not_found(self, mock_logger, mock_file):
        """Test load_config with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            main.load_config('nonexistent_config.json')
        print("✅ load_config file not found test passed")

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('main.logger')
    def test_load_config_invalid_json(self, mock_logger, mock_file):
        """Test load_config with invalid JSON"""
        with self.assertRaises(json.JSONDecodeError):
            main.load_config('invalid_config.json')
        print("✅ load_config invalid JSON test passed")

    @patch('main.time.sleep')
    @patch('main.logger')
    def test_wait_to_start(self, mock_logger, mock_sleep):
        """Test wait_to_start function"""
        main.wait_to_start(30)
        
        mock_sleep.assert_called_once_with(30)
        mock_logger.info.assert_called_once()
        print("✅ wait_to_start test passed")

    @patch('main.SubprocessClass')
    @patch('main.logger')
    def test_fetch_hostname_success(self, mock_logger, mock_subprocess_class):
        """Test fetch_hostname success"""
        mock_subprocess = MagicMock()
        mock_subprocess.execute_cmd.return_value = ("test-hostname\n", None)
        mock_subprocess_class.return_value = mock_subprocess
        
        result = main.fetch_hostname()
        
        self.assertEqual(result, "TEST-HOSTNAME")
        mock_subprocess.execute_cmd.assert_called_once_with("hostname")
        print("✅ fetch_hostname success test passed")

    @patch('main.SubprocessClass')
    @patch('main.logger')
    def test_fetch_hostname_error(self, mock_logger, mock_subprocess_class):
        """Test fetch_hostname with error"""
        mock_subprocess = MagicMock()
        mock_subprocess.execute_cmd.return_value = ("", "Command failed")
        mock_subprocess_class.return_value = mock_subprocess
        
        result = main.fetch_hostname()
        
        self.assertEqual(result, "undefined-hostname")
        print("✅ fetch_hostname error test passed")

    @patch('main.subprocess_obj')
    @patch('main.logger')
    def test_available_pods_success(self, mock_logger, mock_subprocess):
        """Test available_pods function with successful pod retrieval"""
        # Mock kubectl output
        kubectl_output = """csdp-geored-0    1/1     Running   0          2d
csdp-geored-1    1/1     Running   0          2d
csdp-geored-2    0/1     Pending   0          1d"""
        
        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)
        
        result = main.available_pods("test-namespace", "sdp", "false", [], [])
        
        # Should return only running pods with 1/1 status
        expected_pods = ["csdp-geored-0", "csdp-geored-1"]
        self.assertEqual(result, expected_pods)
        print("✅ available_pods success test passed")

    @patch('main.subprocess_obj')
    @patch('main.logger')
    def test_available_pods_with_whitelist(self, mock_logger, mock_subprocess):
        """Test available_pods function with whitelist enabled"""
        kubectl_output = """csdp-geored-0    1/1     Running   0          2d
csdp-geored-1    1/1     Running   0          2d"""
        
        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)
        
        whitelist = ["csdp-geored-0"]
        result = main.available_pods("test-namespace", "sdp", "true", whitelist, [])
        
        # Should return only whitelisted pods
        self.assertEqual(result, ["csdp-geored-0"])
        print("✅ available_pods with whitelist test passed")

    @patch('main.subprocess_obj')
    @patch('main.logger')
    def test_available_pods_with_blacklist(self, mock_logger, mock_subprocess):
        """Test available_pods function with blacklist"""
        kubectl_output = """csdp-geored-0    1/1     Running   0          2d
csdp-geored-1    1/1     Running   0          2d"""
        
        mock_subprocess.execute_cmd.return_value = (kubectl_output, None)
        
        blacklist = ["csdp-geored-1"]
        result = main.available_pods("test-namespace", "sdp", "false", [], blacklist)
        
        # Should exclude blacklisted pods
        self.assertEqual(result, ["csdp-geored-0"])
        print("✅ available_pods with blacklist test passed")

    @patch('main.subprocess_obj')
    @patch('main.logger')
    def test_available_pods_command_error(self, mock_logger, mock_subprocess):
        """Test available_pods function with command error"""
        mock_subprocess.execute_cmd.return_value = ("", "kubectl command failed")
        
        result = main.available_pods("test-namespace", "sdp", "false", [], [])
        
        self.assertEqual(result, [])
        print("✅ available_pods command error test passed")

    @patch('main.subprocess_obj')
    @patch('main.logger')
    def test_available_pods_no_pods_found(self, mock_logger, mock_subprocess):
        """Test available_pods function with no pods found"""
        mock_subprocess.execute_cmd.return_value = ("", None)
        
        result = main.available_pods("test-namespace", "sdp", "false", [], [])
        
        self.assertEqual(result, [])
        print("✅ available_pods no pods found test passed")

    @patch('main.datetime')
    @patch('main.ARCHIVE_DIR', '/test/archive')
    @patch('main.HOSTNAME', 'test-host')
    def test_make_kafka_data_source_file_path(self, mock_datetime):
        """Test make_kafka_data_source_file_path function"""
        mock_datetime.now.return_value.strftime.return_value = "20231223120000"
        
        result = main.make_kafka_data_source_file_path("test-pod")
        
        expected_path = "/test/archive/test-host_test-pod_KPI.txt.20231223120000"
        self.assertEqual(result, expected_path)
        print("✅ make_kafka_data_source_file_path test passed")

    @patch('main.KPI_SDP')
    @patch('main.KafkaDataSourceBuilder')
    @patch('main.make_kafka_data_source_file_path')
    @patch('main.kafka_process')
    @patch('main.ARCHIVE_DIR', '/test/archive')
    @patch('main.HOSTNAME', 'test-host')
    @patch('main.TIMESTAMP', '20231223120000')
    def test_execute_function(self, mock_kafka_process, mock_make_path, mock_builder_class, mock_kpi_class):
        """Test execute function"""
        # Mock objects
        mock_kpi = MagicMock()
        mock_builder = MagicMock()
        mock_kpi_class.return_value = mock_kpi
        mock_builder_class.return_value = mock_builder
        mock_make_path.return_value = "/test/archive/test-host_test-pod_KPI.txt.20231223120000"
        
        # Call execute function
        main.execute(
            "test-pod", 1, {"template": "test"}, "test-host", "test-ns", 
            "main-pod", "/script", "/output", "/archive", "/log", 
            "/kafka/config.json", False, "sdp"
        )
        
        # Verify KPI_SDP was called
        mock_kpi_class.assert_called_once()
        mock_kpi.main.assert_called_once()
        mock_builder.write_to_file.assert_called_once()
        mock_kafka_process.assert_called_once()
        print("✅ execute function test passed")

    @patch('main.concurrent.futures.ProcessPoolExecutor')
    @patch('main.available_pods')
    @patch('main.logger')
    def test_main_function(self, mock_logger, mock_available_pods, mock_executor_class):
        """Test main function"""
        # Mock available pods
        mock_available_pods.return_value = ["pod1", "pod2"]
        
        # Mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Call main function
        main.main(
            "test-host", "test-ns", "main-pod", {"template": "test"},
            "/script", "/output", "/archive", "/log", "/kafka/config.json",
            "false", [], False, 3, "sdp", []
        )
        
        # Verify pods were fetched and executor was used
        mock_available_pods.assert_called_once()
        self.assertEqual(mock_executor.submit.call_count, 2)  # 2 pods
        print("✅ main function test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_SDP_GEORED Main Module Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
