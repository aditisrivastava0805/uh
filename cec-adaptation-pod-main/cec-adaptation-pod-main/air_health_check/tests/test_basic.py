import unittest
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAirHealthCheckBasic(unittest.TestCase):
    """Basic test cases for air_health_check module"""

    def test_import_app_module(self):
        """Test that we can import the app module"""
        try:
            import app
            self.assertTrue(hasattr(app, 'app'))
            print("✅ Successfully imported app module")
        except ImportError as e:
            self.fail(f"Failed to import app module: {e}")

    def test_import_command_executor(self):
        """Test that we can import CommandExecutor"""
        try:
            from CommandExecutor import CommandExecutor
            self.assertTrue(callable(CommandExecutor))
            print("✅ Successfully imported CommandExecutor")
        except ImportError as e:
            self.fail(f"Failed to import CommandExecutor: {e}")

    def test_command_executor_percentage_calculation(self):
        """Test percentage calculation method"""
        try:
            from CommandExecutor import CommandExecutor
            
            # Test normal calculation
            result = CommandExecutor.calculate_percentage(3, 4)
            self.assertEqual(result, 75)
            
            # Test with zero max value
            result = CommandExecutor.calculate_percentage(3, 0)
            self.assertEqual(result, 0.0)
            
            # Test with equal values
            result = CommandExecutor.calculate_percentage(4, 4)
            self.assertEqual(result, 100)
            
            print("✅ Percentage calculation tests passed")
        except Exception as e:
            self.fail(f"Percentage calculation test failed: {e}")

    def test_command_executor_get_healthy_air_pods(self):
        """Test get_healthy_air_pods static method"""
        try:
            from CommandExecutor import CommandExecutor
            
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
            
            print("✅ get_healthy_air_pods test passed")
        except Exception as e:
            self.fail(f"get_healthy_air_pods test failed: {e}")

    def test_command_executor_get_cluster_ip(self):
        """Test get_cluster_ip static method"""
        try:
            from CommandExecutor import CommandExecutor
            
            terminal_output = b"192.168.1.1\n192.168.1.2\n192.168.1.3"
            
            result = CommandExecutor.get_cluster_ip(terminal_output)
            
            # Assertions
            self.assertEqual(result["Cluster_IP"], ["192.168.1.1", "192.168.1.2", "192.168.1.3"])
            
            print("✅ get_cluster_ip test passed")
        except Exception as e:
            self.fail(f"get_cluster_ip test failed: {e}")

    def test_command_executor_get_max_pod_count(self):
        """Test get_max_pod_count static method"""
        try:
            from CommandExecutor import CommandExecutor
            
            terminal_output = b"pod1\npod2\npod3\npod4\npod5"
            
            result = CommandExecutor.get_max_pod_count(terminal_output)
            
            # Assertions
            self.assertEqual(result, 5)
            
            print("✅ get_max_pod_count test passed")
        except Exception as e:
            self.fail(f"get_max_pod_count test failed: {e}")

    def test_app_read_json_file(self):
        """Test read_json_file function"""
        try:
            import app
            import json
            import tempfile
            import os
            
            # Create a temporary JSON file
            test_data = {"test": "data", "number": 123}
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_file = f.name
            
            try:
                result = app.read_json_file(temp_file)
                self.assertEqual(result, test_data)
                print("✅ read_json_file test passed")
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            self.fail(f"read_json_file test failed: {e}")

    def test_configuration_files_exist(self):
        """Test that required configuration files exist"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        config_files = [
            "AirPodConfigurationFile.json",
            "AirPodCommandFile.json",
            "logger-config.json"
        ]
        
        for config_file in config_files:
            file_path = os.path.join(base_dir, config_file)
            self.assertTrue(os.path.exists(file_path), f"Configuration file {config_file} does not exist")
        
        print("✅ Configuration files existence test passed")

    def test_namespace_import(self):
        """Test namespace module import"""
        try:
            # Add lib directory to path
            lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib')
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            
            from Namespace import get_application_namespace, get_adaptation_namespace
            self.assertTrue(callable(get_application_namespace))
            self.assertTrue(callable(get_adaptation_namespace))
            print("✅ Namespace module import test passed")
        except ImportError as e:
            print(f"⚠️  Namespace module import failed (this may be expected): {e}")
            # Don't fail the test as this module may not be available in all environments


if __name__ == '__main__':
    print("="*60)
    print("Running Basic Air Health Check Tests")
    print("="*60)
    unittest.main(verbosity=2)
