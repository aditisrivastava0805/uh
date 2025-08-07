import unittest
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKafkaSDPPrepaidBasic(unittest.TestCase):
    """Basic test cases for KAFKA_SDP_PREPAID module"""

    def test_import_main_module(self):
        """Test that we can import the main module"""
        try:
            import main
            self.assertTrue(hasattr(main, 'timestamp'))
            self.assertTrue(hasattr(main, 'parse_args'))
            self.assertTrue(hasattr(main, 'load_config'))
            print("✅ Successfully imported main module")
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")

    def test_import_kpi_sdp_module(self):
        """Test that we can import KPI_SDP module"""
        try:
            from KPI_SDP import KPI_SDP
            self.assertTrue(callable(KPI_SDP))
            print("✅ Successfully imported KPI_SDP module")
        except ImportError as e:
            self.fail(f"Failed to import KPI_SDP module: {e}")

    def test_import_logger_module(self):
        """Test that we can import Logger module"""
        try:
            from Logger import LoggingHandler
            self.assertTrue(callable(LoggingHandler))
            print("✅ Successfully imported Logger module")
        except ImportError as e:
            self.fail(f"Failed to import Logger module: {e}")

    def test_import_subprocess_module(self):
        """Test that we can import SubprocessClass module"""
        try:
            from SubprocessClass import SubprocessClass
            self.assertTrue(callable(SubprocessClass))
            print("✅ Successfully imported SubprocessClass module")
        except ImportError as e:
            self.fail(f"Failed to import SubprocessClass module: {e}")

    def test_configuration_files_exist(self):
        """Test that required configuration files exist"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_files = [
            "config/config.json",
        ]
        
        for config_file in config_files:
            file_path = os.path.join(base_dir, config_file)
            self.assertTrue(os.path.exists(file_path), f"Configuration file {config_file} does not exist")
        
        print("✅ Configuration files existence test passed")

    def test_timestamp_functionality(self):
        """Test timestamp generation functionality"""
        try:
            import main
            
            result = main.timestamp()
            
            # Should be 14 character timestamp
            self.assertEqual(len(result), 14)
            self.assertTrue(result.isdigit())
            
            print("✅ Timestamp functionality test passed")
        except Exception as e:
            self.fail(f"Timestamp functionality test failed: {e}")

    def test_basic_kpi_sdp_functionality(self):
        """Test basic KPI_SDP functionality"""
        try:
            from unittest.mock import patch, MagicMock
            
            with patch('KPI_SDP.LoggingHandler') as mock_logging:
                mock_logging.get_logger.return_value = MagicMock()
                
                from KPI_SDP import KPI_SDP
                
                kpi_sdp = KPI_SDP(
                    "test-host", "test-ns", "test-pod", "/script",
                    "/output", "/archive", "/log", "sdp"
                )
                
                self.assertEqual(kpi_sdp.host_name, "test-host")
                self.assertEqual(kpi_sdp.namespace, "test-ns")
                self.assertEqual(kpi_sdp.pod, "test-pod")
                
                print("✅ Basic KPI_SDP functionality test passed")
        except Exception as e:
            self.fail(f"Basic KPI_SDP functionality test failed: {e}")

    def test_basic_subprocess_functionality(self):
        """Test basic SubprocessClass functionality"""
        try:
            from unittest.mock import patch, MagicMock
            
            with patch('SubprocessClass.LoggingHandler') as mock_logging:
                mock_logging.get_logger.return_value = MagicMock()
                
                from SubprocessClass import SubprocessClass
                
                subprocess_obj = SubprocessClass()
                
                with patch('subprocess.Popen') as mock_popen:
                    mock_process = MagicMock()
                    mock_process.communicate.return_value = (b"test output", b"")
                    mock_popen.return_value = mock_process
                    
                    output, error = subprocess_obj.execute_cmd("echo test")
                    
                    self.assertEqual(output, "test output")
                    self.assertIsNone(error)
                
                print("✅ Basic SubprocessClass functionality test passed")
        except Exception as e:
            self.fail(f"Basic SubprocessClass functionality test failed: {e}")

    def test_basic_logging_functionality(self):
        """Test basic LoggingHandler functionality"""
        try:
            from unittest.mock import patch, MagicMock
            
            with patch('logging.basicConfig') as mock_basicConfig:
                with patch('os.path.join') as mock_path_join:
                    mock_path_join.return_value = "/test/log"
                    
                    from Logger import LoggingHandler
                    
                    logger_handler = LoggingHandler("/test/script")
                    
                    # Test static method
                    logger = LoggingHandler.get_logger("TestLogger")
                    self.assertIsNotNone(logger)
                    
                    print("✅ Basic LoggingHandler functionality test passed")
        except Exception as e:
            self.fail(f"Basic LoggingHandler functionality test failed: {e}")

    def test_basic_pod_parsing_functionality(self):
        """Test basic pod parsing functionality"""
        try:
            from unittest.mock import patch
            
            with patch('main.subprocess_obj') as mock_subprocess_obj:
                import main
                
                # Mock kubectl output
                mock_output = """csdp-pod-1 1/1 Running 0 1d
csdp-pod-2 1/1 Running 0 2d
csdp-pod-3 0/1 Pending 0 1h"""
                
                mock_subprocess_obj.execute_cmd.return_value = (mock_output, None)
                
                result = main.available_pods("test-ns", "sdp", "false", [], [])
                
                # Should return only running pods with 1/1 status
                expected = ["csdp-pod-1", "csdp-pod-2"]
                self.assertEqual(result, expected)
                
                print("✅ Basic pod parsing functionality test passed")
        except Exception as e:
            self.fail(f"Basic pod parsing test failed: {e}")


if __name__ == '__main__':
    print("="*60)
    print("Running KAFKA_SDP_PREPAID Basic Tests")
    print("="*60)
    unittest.main(verbosity=2)
