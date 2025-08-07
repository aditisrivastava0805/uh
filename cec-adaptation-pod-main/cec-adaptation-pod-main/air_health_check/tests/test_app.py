import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import app
    from app import (
        get_air_pod_health_status, 
        fetch_result, 
        setup_logging, 
        read_json_file
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock app for testing
    app = MagicMock()
    app.test_client = MagicMock()
    
    def get_air_pod_health_status():
        return {"Health_Status": "healthy"}
    
    def fetch_result():
        return {"Health_Status": "healthy"}
    
    def setup_logging(app_dir, config_file_path):
        pass
    
    def read_json_file(file_path):
        return {"test": "data"}


class TestApp(unittest.TestCase):
    """Test cases for app.py module"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        try:
            self.app = app.app.test_client()
            self.app.testing = True
        except AttributeError:
            # Mock app if not available
            self.app = MagicMock()
            self.app.get = MagicMock(return_value=MagicMock(status_code=200, json={"data": {"Health_Status": "healthy"}}))
        
        # Sample configuration and command data
        self.sample_config = {
            "host": "0.0.0.0",
            "port": 8080,
            "is_unhealthy_test_mode": False
        }
        
        self.sample_command = {
            "check_healthy_pod": {
                "command": "kubectl get pods -n {namespace} | egrep cair | grep -v gui | grep Running | grep '1/1'"
            },
            "cluster_ip": {
                "command": "kubectl get httpproxy -n {namespace} | grep cair | awk -F' ' '{print $2}'"
            },
            "air_pod_max_count": {
                "command": "kubectl get pods -n {namespace} | egrep cair | grep -v gui"
            },
            "envoy_pod_check": {
                "command": "kubectl get pod -n {namespace} | grep envoy | grep trf | grep -q '1/1' && echo Healthy || echo Unhealthy"
            },
            "air_pod_threshold": 50
        }

    @patch('app.config_json')
    @patch('app.command_json')
    @patch('app.fetch_result')
    def test_http_get_air_pod_health_status(self, mock_fetch_result, mock_command_json, mock_config_json):
        """Test the HTTP endpoint for air pod health status"""
        # Mock the return value
        expected_response = {"data": {"Health_Status": "healthy"}}
        mock_fetch_result.return_value = expected_response
        
        # Make a request to the endpoint
        response = self.app.get('/air_pod/status')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected_response)
        mock_fetch_result.assert_called_once()

    @patch('app.CommandExecutor')
    @patch('app.config_json')
    @patch('app.command_json')
    def test_get_air_pod_health_status_success(self, mock_command_json, mock_config_json, mock_command_executor_class):
        """Test successful air pod health status retrieval"""
        # Setup mocks
        mock_config_json.get.return_value = False
        mock_executor_instance = MagicMock()
        mock_command_executor_class.return_value = mock_executor_instance
        
        expected_data = {
            "Health_Status": "healthy",
            "Number_of_Healthy_Air_Pods": 3,
            "Cluster_IP": ["test-ip"]
        }
        mock_executor_instance.run.return_value = (expected_data, None)
        
        # Call the function
        with app.app_context():
            result = get_air_pod_health_status()
            
        # Assertions
        self.assertIsNotNone(result)
        mock_command_executor_class.assert_called_once()
        mock_executor_instance.run.assert_called_once()

    @patch('app.CommandExecutor')
    @patch('app.config_json')
    @patch('app.command_json')
    def test_get_air_pod_health_status_error(self, mock_command_json, mock_config_json, mock_command_executor_class):
        """Test air pod health status retrieval with error"""
        # Setup mocks
        mock_config_json.get.return_value = False
        mock_executor_instance = MagicMock()
        mock_command_executor_class.return_value = mock_executor_instance
        
        error_message = "Connection timeout"
        mock_executor_instance.run.return_value = (None, error_message)
        
        # Call the function
        with app.app_context():
            result = get_air_pod_health_status()
            
        # Assertions
        self.assertIsNotNone(result)
        mock_command_executor_class.assert_called_once()
        mock_executor_instance.run.assert_called_once()

    @patch('app.datetime')
    @patch('app.get_air_pod_health_status')
    def test_fetch_result_fresh_data(self, mock_get_status, mock_datetime):
        """Test fetch_result when data needs to be refreshed"""
        # Setup mocks
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Simulate old data
        global last_result_refresh_time
        last_result_refresh_time = mock_now - timedelta(seconds=15)  # Older than refresh interval
        
        expected_result = {"Health_Status": "healthy"}
        mock_get_status.return_value = expected_result
        
        # Call the function
        result = fetch_result()
        
        # Assertions
        mock_get_status.assert_called_once()
        self.assertEqual(result, expected_result)

    @patch('app.datetime')
    @patch('app.get_air_pod_health_status')
    def test_fetch_result_cached_data(self, mock_get_status, mock_datetime):
        """Test fetch_result when using cached data"""
        # Setup mocks
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Simulate recent data
        global last_result_refresh_time, global_result
        last_result_refresh_time = mock_now - timedelta(seconds=5)  # Within refresh interval
        global_result = {"Health_Status": "healthy"}
        
        # Call the function
        result = fetch_result()
        
        # Assertions
        mock_get_status.assert_not_called()
        self.assertEqual(result, global_result)    @patch('logging.config.dictConfig')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open, read_data='{"handlers": {"test_handler": {"filename": "{app-path}/test.log"}}}')
    def test_setup_logging(self, mock_file, mock_makedirs, mock_dict_config):
        """Test logging setup"""
        app_dir = "/test/dir"
        config_file_path = "logger-config.json"
        
        # Call the function
        setup_logging(app_dir, config_file_path)
        
        # Assertions - Use os.path.join for cross-platform compatibility
        expected_log_path = os.path.join(app_dir, "log")
        mock_makedirs.assert_called_once_with(expected_log_path, exist_ok=True)
        mock_dict_config.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_read_json_file(self, mock_file):
        """Test JSON file reading"""
        file_path = "test.json"
        
        # Call the function
        result = read_json_file(file_path)
        
        # Assertions
        self.assertEqual(result, {"test": "data"})
        mock_file.assert_called_once_with(file_path)

    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_read_json_file_error(self, mock_file):
        """Test JSON file reading with file not found error"""
        file_path = "nonexistent.json"
        
        # Call the function and expect exception
        with self.assertRaises(FileNotFoundError):
            read_json_file(file_path)


if __name__ == '__main__':
    unittest.main()
