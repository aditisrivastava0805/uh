import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from CommandExecutor import CommandExecutor


class TestAirHealthCheckIntegration(unittest.TestCase):
    """Integration tests for the air health check system"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
        
        self.config_file = {
            "host": "0.0.0.0",
            "port": 8080,
            "is_unhealthy_test_mode": False
        }
        
        self.command_json = {
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
    @patch('CommandExecutor.get_application_namespace')
    @patch('subprocess.Popen')
    def test_full_healthy_scenario(self, mock_popen, mock_namespace, mock_command_json, mock_config_json):
        """Test complete healthy scenario from HTTP request to response"""
        # Setup mocks
        mock_namespace.return_value = "test-namespace"
        mock_config_json.get.return_value = False
        mock_command_json.__getitem__.side_effect = lambda key: self.command_json[key]
        mock_command_json.get.side_effect = lambda key, default=None: self.command_json.get(key, default)
        
        # Mock subprocess calls for different commands
        def mock_popen_side_effect(cmd, **kwargs):
            mock_process = MagicMock()
            if "egrep cair" in cmd and "Running" in cmd:
                # Healthy pods output
                mock_process.communicate.return_value = (
                    b"cair-pod-1 1/1 Running 0 1d\ncair-pod-2 1/1 Running 0 2d\ncair-pod-3 1/1 Running 0 3d",
                    None
                )
            elif "egrep cair" in cmd and "Running" not in cmd:
                # Max count output
                mock_process.communicate.return_value = (
                    b"cair-pod-1\ncair-pod-2\ncair-pod-3\ncair-pod-4",
                    None
                )
            elif "httpproxy" in cmd:
                # Cluster IP output
                mock_process.communicate.return_value = (b"192.168.1.100", None)
            elif "envoy" in cmd:
                # Envoy health check output
                mock_process.communicate.return_value = (b"Healthy", None)
            return mock_process
        
        mock_popen.side_effect = mock_popen_side_effect
        
        # Make HTTP request
        response = self.app.get('/air_pod/status')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        
        # Check that we get expected healthy response structure
        self.assertIn('data', response_data)
        data = response_data['data']
        self.assertEqual(data['Health_Status'], 'healthy')
        self.assertEqual(data['Number_of_Healthy_Air_Pods'], 3)
        self.assertIn('Cluster_IP', data)

    @patch('app.config_json')
    @patch('app.command_json')
    @patch('CommandExecutor.get_application_namespace')
    @patch('subprocess.Popen')
    def test_full_unhealthy_scenario_below_threshold(self, mock_popen, mock_namespace, mock_command_json, mock_config_json):
        """Test complete unhealthy scenario due to pods below threshold"""
        # Setup mocks
        mock_namespace.return_value = "test-namespace"
        mock_config_json.get.return_value = False
        mock_command_json.__getitem__.side_effect = lambda key: self.command_json[key]
        mock_command_json.get.side_effect = lambda key, default=None: self.command_json.get(key, default)
        
        # Mock subprocess calls for different commands
        def mock_popen_side_effect(cmd, **kwargs):
            mock_process = MagicMock()
            if "egrep cair" in cmd and "Running" in cmd:
                # Only 1 healthy pod
                mock_process.communicate.return_value = (b"cair-pod-1 1/1 Running 0 1d", None)
            elif "egrep cair" in cmd and "Running" not in cmd:
                # 4 total pods
                mock_process.communicate.return_value = (
                    b"cair-pod-1\ncair-pod-2\ncair-pod-3\ncair-pod-4",
                    None
                )
            elif "httpproxy" in cmd:
                # Cluster IP output
                mock_process.communicate.return_value = (b"192.168.1.100", None)
            elif "envoy" in cmd:
                # Envoy health check output
                mock_process.communicate.return_value = (b"Healthy", None)
            return mock_process
        
        mock_popen.side_effect = mock_popen_side_effect
        
        # Make HTTP request
        response = self.app.get('/air_pod/status')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        
        # Check that we get expected unhealthy response
        self.assertIn('data', response_data)
        data = response_data['data']
        self.assertEqual(data['Health_Status'], 'unhealthy')
        self.assertEqual(data['Number_of_Healthy_Air_Pods'], 1)
        self.assertIn('Cluster_IP', data)

    @patch('app.config_json')
    @patch('app.command_json')
    @patch('CommandExecutor.get_application_namespace')
    @patch('subprocess.Popen')
    def test_full_unhealthy_scenario_envoy_unhealthy(self, mock_popen, mock_namespace, mock_command_json, mock_config_json):
        """Test complete unhealthy scenario due to unhealthy envoy pods"""
        # Setup mocks
        mock_namespace.return_value = "test-namespace"
        mock_config_json.get.return_value = False
        mock_command_json.__getitem__.side_effect = lambda key: self.command_json[key]
        mock_command_json.get.side_effect = lambda key, default=None: self.command_json.get(key, default)
        
        # Mock subprocess calls for different commands
        def mock_popen_side_effect(cmd, **kwargs):
            mock_process = MagicMock()
            if "egrep cair" in cmd and "Running" in cmd:
                # All pods healthy
                mock_process.communicate.return_value = (
                    b"cair-pod-1 1/1 Running 0 1d\ncair-pod-2 1/1 Running 0 2d\ncair-pod-3 1/1 Running 0 3d\ncair-pod-4 1/1 Running 0 4d",
                    None
                )
            elif "egrep cair" in cmd and "Running" not in cmd:
                # 4 total pods
                mock_process.communicate.return_value = (
                    b"cair-pod-1\ncair-pod-2\ncair-pod-3\ncair-pod-4",
                    None
                )
            elif "httpproxy" in cmd:
                # Cluster IP output
                mock_process.communicate.return_value = (b"192.168.1.100", None)
            elif "envoy" in cmd:
                # Envoy health check output - UNHEALTHY
                mock_process.communicate.return_value = (b"Unhealthy", None)
            return mock_process
        
        mock_popen.side_effect = mock_popen_side_effect
        
        # Make HTTP request
        response = self.app.get('/air_pod/status')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        
        # Check that we get expected unhealthy response due to envoy
        self.assertIn('data', response_data)
        data = response_data['data']
        self.assertEqual(data['Health_Status'], 'unhealthy')
        self.assertIn('Cluster_IP', data)

    @patch('app.config_json')
    @patch('app.command_json')
    @patch('CommandExecutor.get_application_namespace')
    @patch('subprocess.Popen')
    def test_error_handling_command_failure(self, mock_popen, mock_namespace, mock_command_json, mock_config_json):
        """Test error handling when commands fail"""
        # Setup mocks
        mock_namespace.return_value = "test-namespace"
        mock_config_json.get.return_value = False
        mock_command_json.__getitem__.side_effect = lambda key: self.command_json[key]
        mock_command_json.get.side_effect = lambda key, default=None: self.command_json.get(key, default)
        
        # Mock subprocess to raise exception
        mock_popen.side_effect = Exception("kubectl command failed")
        
        # Make HTTP request
        response = self.app.get('/air_pod/status')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        
        # Should get error in response
        self.assertIn('data', response_data)

    @patch('CommandExecutor.get_application_namespace')
    def test_command_executor_initialization(self, mock_namespace):
        """Test CommandExecutor initialization with different configurations"""
        mock_namespace.return_value = "test-namespace"
        
        # Test normal mode
        executor = CommandExecutor(self.config_file, False)
        self.assertFalse(executor.is_unhealthy_test_mode)
        
        # Test unhealthy test mode
        executor_test = CommandExecutor(self.config_file, True)
        self.assertTrue(executor_test.is_unhealthy_test_mode)

    def test_percentage_calculation_edge_cases(self):
        """Test percentage calculation with various edge cases"""
        # Normal case
        self.assertEqual(CommandExecutor.calculate_percentage(3, 4), 75)
        
        # Zero available
        self.assertEqual(CommandExecutor.calculate_percentage(0, 4), 0)
        
        # Zero max (division by zero protection)
        self.assertEqual(CommandExecutor.calculate_percentage(3, 0), 0.0)
        
        # Equal values
        self.assertEqual(CommandExecutor.calculate_percentage(5, 5), 100)
        
        # Fractional result
        self.assertEqual(CommandExecutor.calculate_percentage(1, 3), 33)

    @patch('app.config_json')
    @patch('app.command_json')
    def test_caching_mechanism(self, mock_command_json, mock_config_json):
        """Test that the caching mechanism works correctly"""
        mock_config_json.get.return_value = False
        
        with patch('app.get_air_pod_health_status') as mock_get_status:
            mock_get_status.return_value = {"Health_Status": "healthy"}
            
            # First request should call get_air_pod_health_status
            response1 = self.app.get('/air_pod/status')
            self.assertEqual(response1.status_code, 200)
            
            # Second request within cache interval should use cached result
            response2 = self.app.get('/air_pod/status')
            self.assertEqual(response2.status_code, 200)
            
            # Should have called get_air_pod_health_status at least once
            self.assertTrue(mock_get_status.called)


if __name__ == '__main__':
    unittest.main()
