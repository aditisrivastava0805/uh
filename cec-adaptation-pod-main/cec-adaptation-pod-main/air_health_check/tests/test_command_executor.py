import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from unittest.mock import call

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CommandExecutor import CommandExecutor


class TestCommandExecutor(unittest.TestCase):
    """Test cases for CommandExecutor class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
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

    @patch('CommandExecutor.get_application_namespace')
    def test_init(self, mock_namespace):
        """Test CommandExecutor initialization"""
        mock_namespace.return_value = "test-namespace"
        
        executor = CommandExecutor(self.config_file, False)
        
        self.assertEqual(executor.config_file, self.config_file)
        self.assertEqual(executor.namespace, "test-namespace")
        self.assertEqual(executor.is_unhealthy_test_mode, False)
        self.assertIsNone(executor.air_pod_healthy_status)
        self.assertIsNone(executor.cluster_ip)

    @patch('CommandExecutor.get_application_namespace')
    @patch('CommandExecutor.CommandExecutor.execute_command')
    @patch('CommandExecutor.CommandExecutor.get_envoy_pods_status')
    def test_run_healthy_pods(self, mock_envoy_status, mock_execute_command, mock_namespace):
        """Test run method with healthy pods"""
        mock_namespace.return_value = "test-namespace"
        
        # Mock return values
        mock_air_pod_health = {
            "Number_of_Healthy_Air_Pods": 3,
            "pod1": {"Air_Pod_Status": "Running"},
            "pod2": {"Air_Pod_Status": "Running"},
            "pod3": {"Air_Pod_Status": "Running"}
        }
        mock_max_count = 4
        mock_cluster_ip = {"Cluster_IP": ["192.168.1.1"]}
        
        mock_execute_command.side_effect = [mock_air_pod_health, mock_max_count, mock_cluster_ip]
        mock_envoy_status.return_value = "Healthy"
        
        executor = CommandExecutor(self.config_file, False)
        result, error = executor.run(self.command_json)
        
        # Assertions
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertEqual(result["Health_Status"], "healthy")
        self.assertEqual(result["Number_of_Healthy_Air_Pods"], 3)
        self.assertEqual(result["Cluster_IP"], ["192.168.1.1"])

    @patch('CommandExecutor.get_application_namespace')
    @patch('CommandExecutor.CommandExecutor.execute_command')
    @patch('CommandExecutor.CommandExecutor.get_envoy_pods_status')
    def test_run_unhealthy_pods_below_threshold(self, mock_envoy_status, mock_execute_command, mock_namespace):
        """Test run method with pods below threshold"""
        mock_namespace.return_value = "test-namespace"
        
        # Mock return values - only 1 healthy pod out of 4 (25% < 50% threshold)
        mock_air_pod_health = {
            "Number_of_Healthy_Air_Pods": 1,
            "pod1": {"Air_Pod_Status": "Running"}
        }
        mock_max_count = 4
        mock_cluster_ip = {"Cluster_IP": ["192.168.1.1"]}
        
        mock_execute_command.side_effect = [mock_air_pod_health, mock_max_count, mock_cluster_ip]
        mock_envoy_status.return_value = "Healthy"
        
        executor = CommandExecutor(self.config_file, False)
        result, error = executor.run(self.command_json)
        
        # Assertions
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertEqual(result["Health_Status"], "unhealthy")
        self.assertEqual(result["Number_of_Healthy_Air_Pods"], 1)
        self.assertEqual(result["Cluster_IP"], ["192.168.1.1"])

    @patch('CommandExecutor.get_application_namespace')
    @patch('CommandExecutor.CommandExecutor.execute_command')
    @patch('CommandExecutor.CommandExecutor.get_envoy_pods_status')
    def test_run_unhealthy_envoy_pods(self, mock_envoy_status, mock_execute_command, mock_namespace):
        """Test run method with unhealthy envoy pods"""
        mock_namespace.return_value = "test-namespace"
        
        # Mock return values
        mock_air_pod_health = {
            "Number_of_Healthy_Air_Pods": 4,
            "pod1": {"Air_Pod_Status": "Running"},
            "pod2": {"Air_Pod_Status": "Running"},
            "pod3": {"Air_Pod_Status": "Running"},
            "pod4": {"Air_Pod_Status": "Running"}
        }
        mock_max_count = 4
        mock_cluster_ip = {"Cluster_IP": ["192.168.1.1"]}
        
        mock_execute_command.side_effect = [mock_air_pod_health, mock_max_count, mock_cluster_ip]
        mock_envoy_status.return_value = "Unhealthy"
        
        executor = CommandExecutor(self.config_file, False)
        result, error = executor.run(self.command_json)
        
        # Assertions
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertEqual(result["Health_Status"], "unhealthy")
        self.assertEqual(result["Number_of_Healthy_Air_Pods"], 4)
        self.assertEqual(result["Cluster_IP"], ["192.168.1.1"])

    @patch('CommandExecutor.get_application_namespace')
    @patch('CommandExecutor.CommandExecutor.execute_command')
    @patch('CommandExecutor.CommandExecutor.get_envoy_pods_status')
    def test_run_unhealthy_test_mode(self, mock_envoy_status, mock_execute_command, mock_namespace):
        """Test run method in unhealthy test mode"""
        mock_namespace.return_value = "test-namespace"
        
        # Mock return values - healthy pods but test mode is enabled
        mock_air_pod_health = {
            "Number_of_Healthy_Air_Pods": 4,
            "pod1": {"Air_Pod_Status": "Running"},
            "pod2": {"Air_Pod_Status": "Running"},
            "pod3": {"Air_Pod_Status": "Running"},
            "pod4": {"Air_Pod_Status": "Running"}
        }
        mock_max_count = 4
        mock_cluster_ip = {"Cluster_IP": ["192.168.1.1"]}
        
        mock_execute_command.side_effect = [mock_air_pod_health, mock_max_count, mock_cluster_ip]
        mock_envoy_status.return_value = "Healthy"
        
        executor = CommandExecutor(self.config_file, True)  # Enable test mode
        result, error = executor.run(self.command_json)
        
        # Assertions
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertEqual(result["Health_Status"], "unhealthy")

    @patch('CommandExecutor.get_application_namespace')
    @patch('CommandExecutor.CommandExecutor.execute_command')
    def test_run_exception_handling(self, mock_execute_command, mock_namespace):
        """Test run method exception handling"""
        mock_namespace.return_value = "test-namespace"
        mock_execute_command.side_effect = Exception("Command execution failed")
        
        executor = CommandExecutor(self.config_file, False)
        result, error = executor.run(self.command_json)
        
        # Assertions
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn("Command execution failed", error)

    @patch('subprocess.Popen')
    def test_execute_command_air_pod_quality_check(self, mock_popen):
        """Test execute_command for air pod quality check"""
        # Mock subprocess output
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"pod1 1/1 Running 0 1d\npod2 1/1 Running 0 2d", None)
        mock_popen.return_value = mock_process
        
        executor = CommandExecutor(self.config_file, False)
        
        with patch.object(executor, 'get_healthy_air_pods') as mock_get_healthy:
            mock_get_healthy.return_value = {"Number_of_Healthy_Air_Pods": 2}
            
            result = executor.execute_command("test command", "air_pod_quality_check")
            
            mock_get_healthy.assert_called_once()
            self.assertEqual(result, {"Number_of_Healthy_Air_Pods": 2})

    @patch('subprocess.Popen')
    def test_execute_command_cluster_ip(self, mock_popen):
        """Test execute_command for cluster IP"""
        # Mock subprocess output
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"192.168.1.1\n192.168.1.2", None)
        mock_popen.return_value = mock_process
        
        executor = CommandExecutor(self.config_file, False)
        
        with patch.object(executor, 'get_cluster_ip') as mock_get_cluster_ip:
            mock_get_cluster_ip.return_value = {"Cluster_IP": ["192.168.1.1", "192.168.1.2"]}
            
            result = executor.execute_command("test command", "cluster_ip")
            
            mock_get_cluster_ip.assert_called_once()
            self.assertEqual(result, {"Cluster_IP": ["192.168.1.1", "192.168.1.2"]})

    @patch('subprocess.Popen')
    def test_execute_command_max_count(self, mock_popen):
        """Test execute_command for max pod count"""
        # Mock subprocess output
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"pod1\npod2\npod3\npod4", None)
        mock_popen.return_value = mock_process
        
        executor = CommandExecutor(self.config_file, False)
        
        with patch.object(executor, 'get_max_pod_count') as mock_get_max_count:
            mock_get_max_count.return_value = 4
            
            result = executor.execute_command("test command", "air_pod_max_count")
            
            mock_get_max_count.assert_called_once()
            self.assertEqual(result, 4)

    def test_get_healthy_air_pods(self):
        """Test get_healthy_air_pods static method"""
        terminal_output = b"pod1 1/1 Running 0 1d\npod2 1/1 Running 0 2d\npod3 1/1 Running 0 3d"
        
        result = CommandExecutor.get_healthy_air_pods(terminal_output)
        
        # Assertions
        self.assertEqual(result["Number_of_Healthy_Air_Pods"], 3)
        self.assertIn("pod1", result)
        self.assertIn("pod2", result)
        self.assertIn("pod3", result)
        self.assertEqual(result["pod1"]["Air_Pod_Status"], "Running")
        self.assertEqual(result["pod1"]["Number_Of_Containers"], "1/1")
        self.assertEqual(result["pod1"]["Number_Of_Restart"], "0")
        self.assertEqual(result["pod1"]["Pod_Up_Time"], "1d")

    def test_get_cluster_ip(self):
        """Test get_cluster_ip static method"""
        terminal_output = b"192.168.1.1\n192.168.1.2\n192.168.1.3"
        
        result = CommandExecutor.get_cluster_ip(terminal_output)
        
        # Assertions
        self.assertEqual(result["Cluster_IP"], ["192.168.1.1", "192.168.1.2", "192.168.1.3"])

    def test_calculate_percentage(self):
        """Test calculate_percentage static method"""
        # Test normal calculation
        result = CommandExecutor.calculate_percentage(3, 4)
        self.assertEqual(result, 75)
        
        # Test with zero max value
        result = CommandExecutor.calculate_percentage(3, 0)
        self.assertEqual(result, 0.0)
        
        # Test with equal values
        result = CommandExecutor.calculate_percentage(4, 4)
        self.assertEqual(result, 100)
        
        # Test with decimal result
        result = CommandExecutor.calculate_percentage(1, 3)
        self.assertEqual(result, 33)  # rounded

    def test_get_max_pod_count(self):
        """Test get_max_pod_count static method"""
        terminal_output = b"pod1\npod2\npod3\npod4\npod5"
        
        result = CommandExecutor.get_max_pod_count(terminal_output)
        
        # Assertions
        self.assertEqual(result, 5)

    @patch('subprocess.Popen')
    def test_get_envoy_pods_status_healthy(self, mock_popen):
        """Test get_envoy_pods_status with healthy status"""
        # Mock subprocess output
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"Healthy", None)
        mock_popen.return_value = mock_process
        
        executor = CommandExecutor(self.config_file, False)
        
        with patch.object(executor, 'execute_command') as mock_execute:
            mock_execute.return_value = (b"Healthy", None)
            
            result = executor.get_envoy_pods_status("test command")
            
            self.assertEqual(result, "b'Healthy'")

    @patch('subprocess.Popen')
    def test_get_envoy_pods_status_unhealthy(self, mock_popen):
        """Test get_envoy_pods_status with unhealthy status"""
        # Mock subprocess output
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"Unhealthy", None)
        mock_popen.return_value = mock_process
        
        executor = CommandExecutor(self.config_file, False)
        
        with patch.object(executor, 'execute_command') as mock_execute:
            mock_execute.return_value = (b"Unhealthy", None)
            
            result = executor.get_envoy_pods_status("test command")
            
            self.assertEqual(result, "b'Unhealthy'")

    def test_get_healthy_air_pods_empty_output(self):
        """Test get_healthy_air_pods with empty output"""
        terminal_output = b""
        
        result = CommandExecutor.get_healthy_air_pods(terminal_output)
        
        # Should handle empty output gracefully
        self.assertEqual(result["Number_of_Healthy_Air_Pods"], 0)

    def test_get_cluster_ip_empty_output(self):
        """Test get_cluster_ip with empty output"""
        terminal_output = b""
        
        result = CommandExecutor.get_cluster_ip(terminal_output)
        
        # Should handle empty output gracefully
        self.assertEqual(result["Cluster_IP"], [])

    def test_get_max_pod_count_empty_output(self):
        """Test get_max_pod_count with empty output"""
        terminal_output = b""
        
        result = CommandExecutor.get_max_pod_count(terminal_output)
        
        # Should handle empty output gracefully
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
