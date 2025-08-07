#!/usr/bin/env python3
"""
Comprehensive tests for KAFKA_SDP_GEORED main.py module with proper mocking
These tests use extensive mocking to test complex functions safely
"""

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


class TestMainModuleComprehensive(unittest.TestCase):
    """Comprehensive test cases for main module functions with mocking"""

    def setUp(self):
        """Set up test fixtures"""
        if not MAIN_IMPORT_SUCCESS:
            self.skipTest(f"Main module import failed: {MAIN_IMPORT_ERROR}")
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

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
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertFalse(wait_flag)
            self.assertFalse(test_flag)
            print("✅ parse_args basic test passed")
        finally:
            sys.argv = original_argv

    def test_parse_args_with_flags(self):
        """Test parse_args with flags"""
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['main.py', 'config.json', '--wait', '--test']
            config_path, wait_flag, test_flag = main.parse_args()
            
            self.assertEqual(config_path, 'config.json')
            self.assertTrue(wait_flag)
            self.assertTrue(test_flag)
            print("✅ parse_args with flags test passed")
        finally:
            sys.argv = original_argv

    @patch('main.subprocess_obj')
    def test_eval_value_without_command(self, mock_subprocess):
        """Test eval_value with regular string"""
        result = main.eval_value("simple_value")
        self.assertEqual(result, "simple_value")
        mock_subprocess.execute_cmd.assert_not_called()
        print("✅ eval_value without command test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_command_single_line(self, mock_subprocess):
        """Test eval_value with command returning single line"""
        mock_subprocess.execute_cmd.return_value = ("test_output", None)
        
        result = main.eval_value("cmd:echo test")
        self.assertEqual(result, "test_output")
        mock_subprocess.execute_cmd.assert_called_once_with("echo test")
        print("✅ eval_value with command single line test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_command_multiple_lines(self, mock_subprocess):
        """Test eval_value with command returning multiple lines"""
        mock_subprocess.execute_cmd.return_value = ("line1\nline2\nline3", None)
        
        result = main.eval_value("cmd:kubectl get ns")
        self.assertEqual(result, "line3")  # Should return last line
        print("✅ eval_value with command multiple lines test passed")

    @patch('main.subprocess_obj')
    def test_eval_value_with_command_error(self, mock_subprocess):
        """Test eval_value with command error"""
        mock_subprocess.execute_cmd.return_value = ("", "Command failed")
        
        with self.assertRaises(OSError):
            main.eval_value("cmd:invalid_command")
        print("✅ eval_value with command error test passed")

    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_success(self, mock_file, mock_json_load):
        """Test load_config function with successful loading"""
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
        
        mock_json_load.return_value = config_data
        
        # Mock eval_value to return namespace as-is
        with patch('main.eval_value', side_effect=lambda x: x):
            with patch('main.logger') as mock_logger:
                result = main.load_config('test_config.json')
                
                self.assertEqual(len(result), 9)
                wait_secs, namespace, pod, template, whitelist_enable, whitelist_pods, max_proc, pod_container, blacklist = result
                self.assertEqual(wait_secs, 10)
                self.assertEqual(namespace, "test-namespace")
                self.assertEqual(pod, "sdp")
                
        print("✅ load_config success test passed")

    @patch('main.time.sleep')
    def test_wait_to_start(self, mock_sleep):
        """Test wait_to_start function"""
        with patch('main.logger') as mock_logger:
            main.wait_to_start(30)
            mock_sleep.assert_called_once_with(30)
            mock_logger.info.assert_called()
        print("✅ wait_to_start test passed")

    def test_make_dir_new_directory(self):
        """Test make_dir with new directory"""
        test_path = os.path.join(self.test_dir, "new_directory")
        self.assertFalse(os.path.exists(test_path))
        
        main.make_dir(test_path)
        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.path.isdir(test_path))
        print("✅ make_dir new directory test passed")

    def test_make_dir_existing_directory(self):
        """Test make_dir with existing directory"""
        test_path = os.path.join(self.test_dir, "existing_directory")
        os.makedirs(test_path)
        self.assertTrue(os.path.exists(test_path))
        
        # Should not raise exception
        main.make_dir(test_path)
        self.assertTrue(os.path.exists(test_path))
        print("✅ make_dir existing directory test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_success(self, mock_subprocess_class):
        """Test fetch_hostname with successful execution"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("test-hostname\n", None)
        
        with patch('main.logger') as mock_logger:
            result = main.fetch_hostname()
            self.assertEqual(result, "TEST-HOSTNAME")  # Should be uppercase and stripped
            mock_instance.execute_cmd.assert_called_once_with("hostname")
        
        print("✅ fetch_hostname success test passed")

    @patch('main.SubprocessClass')
    def test_fetch_hostname_error(self, mock_subprocess_class):
        """Test fetch_hostname with command error"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("", "Command failed")
        
        with patch('main.logger') as mock_logger:
            result = main.fetch_hostname()
            self.assertEqual(result, "undefined-hostname")
            mock_logger.error.assert_called()
        
        print("✅ fetch_hostname error test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_success(self, mock_subprocess):
        """Test available_pods with successful pod discovery"""
        pod_output = "csdp-geored-c-0    1/1     Running   0       5d\ncsdp-geored-c-1    1/1     Running   0       5d"
        mock_subprocess.execute_cmd.return_value = (pod_output, None)
        
        with patch('main.logger') as mock_logger:
            result = main.available_pods("test-namespace", "sdp", "false", [], [])
            
            self.assertEqual(len(result), 2)
            self.assertIn("csdp-geored-c-0", result)
            self.assertIn("csdp-geored-c-1", result)
        
        print("✅ available_pods success test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_whitelist(self, mock_subprocess):
        """Test available_pods with whitelist enabled"""
        pod_output = "csdp-geored-c-0    1/1     Running   0       5d\ncsdp-geored-c-1    1/1     Running   0       5d"
        mock_subprocess.execute_cmd.return_value = (pod_output, None)
        
        with patch('main.logger') as mock_logger:
            result = main.available_pods("test-namespace", "sdp", "true", ["csdp-geored-c-0"], [])
            
            self.assertEqual(len(result), 1)
            self.assertIn("csdp-geored-c-0", result)
            self.assertNotIn("csdp-geored-c-1", result)
        
        print("✅ available_pods with whitelist test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_with_blacklist(self, mock_subprocess):
        """Test available_pods with blacklist"""
        pod_output = "csdp-geored-c-0    1/1     Running   0       5d\ncsdp-geored-c-1    1/1     Running   0       5d"
        mock_subprocess.execute_cmd.return_value = (pod_output, None)
        
        with patch('main.logger') as mock_logger:
            result = main.available_pods("test-namespace", "sdp", "false", [], ["csdp-geored-c-1"])
            
            self.assertEqual(len(result), 1)
            self.assertIn("csdp-geored-c-0", result)
            self.assertNotIn("csdp-geored-c-1", result)
        
        print("✅ available_pods with blacklist test passed")

    @patch('main.subprocess_obj')
    def test_available_pods_error(self, mock_subprocess):
        """Test available_pods with command error"""
        mock_subprocess.execute_cmd.return_value = ("", "Command failed")
        
        with patch('main.logger') as mock_logger:
            result = main.available_pods("test-namespace", "sdp", "false", [], [])
            
            self.assertEqual(result, [])
            mock_logger.error.assert_called()
        
        print("✅ available_pods error test passed")

    def test_make_kafka_data_source_file_path(self):
        """Test make_kafka_data_source_file_path function"""
        with patch('main.ARCHIVE_DIR', '/test/archive'):
            with patch('main.HOSTNAME', 'test-host'):
                result = main.make_kafka_data_source_file_path('test-pod')
                
                self.assertIn('/test/archive', result)
                self.assertIn('test-host_test-pod_KPI.txt.', result)
                self.assertTrue(result.endswith('.txt.' + datetime.now().strftime("%Y%m%d")))
        
        print("✅ make_kafka_data_source_file_path test passed")

    @patch('main.kafka_process')
    @patch('main.KafkaDataSourceBuilder')
    @patch('main.KPI_SDP')
    def test_execute_function(self, mock_kpi_sdp, mock_kafka_builder, mock_kafka_process):
        """Test execute function with mocking"""
        # Setup mocks
        mock_kpi_instance = MagicMock()
        mock_kpi_sdp.return_value = mock_kpi_instance
        
        mock_builder_instance = MagicMock()
        mock_kafka_builder.return_value = mock_builder_instance
        mock_builder_instance.data_source.return_value = "test_data"
        
        with patch('main.make_kafka_data_source_file_path', return_value='/test/path'):
            with patch('main.ARCHIVE_DIR', '/test/archive'):
                with patch('main.HOSTNAME', 'test-host'):
                    with patch('main.TIMESTAMP', '20230101120000'):
                        main.execute(
                            'test-pod', 1, {'template': 'data'}, 'hostname', 
                            'namespace', 'main-pod', '/script', '/output', 
                            '/archive', '/log', '/kafka-config', False, 'container'
                        )
        
        # Verify KPI_SDP was instantiated and called
        mock_kpi_sdp.assert_called_once()
        mock_kpi_instance.main.assert_called_once()
        
        # Verify KafkaDataSourceBuilder was used
        mock_kafka_builder.assert_called_once_with({'template': 'data'})
        mock_builder_instance.write_to_file.assert_called_once()
        
        # Verify kafka_process was called
        mock_kafka_process.assert_called_once()
        
        print("✅ execute function test passed")


if __name__ == '__main__':
    print("=" * 70)
    print("KAFKA_SDP_GEORED - Comprehensive Main Module Tests")
    print("=" * 70)
    print("Testing main.py functions with proper mocking")
    print("=" * 70)
    
    unittest.main(verbosity=2)
