import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import date

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Logger import LoggingHandler


class TestLoggingHandler(unittest.TestCase):
    """Test cases for LoggingHandler class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.script_dir = "/test/script/dir"

    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_logging_handler_initialization(self, mock_basicConfig, mock_path_join):
        """Test LoggingHandler initialization"""
        mock_path_join.return_value = "/test/script/dir/log"
        
        # Create LoggingHandler instance
        logger_handler = LoggingHandler(self.script_dir)
        
        # Verify os.path.join was called correctly
        mock_path_join.assert_called_once_with(self.script_dir, 'log')
        
        # Verify logging.basicConfig was called
        mock_basicConfig.assert_called_once()
        
        # Check the call arguments
        call_args = mock_basicConfig.call_args
        kwargs = call_args[1]
        
        self.assertIn('level', kwargs)
        self.assertIn('filename', kwargs)
        self.assertIn('filemode', kwargs)
        self.assertIn('format', kwargs)
        self.assertIn('datefmt', kwargs)
        
        print("✅ LoggingHandler initialization test passed")

    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_logging_configuration_parameters(self, mock_basicConfig, mock_path_join):
        """Test logging configuration parameters"""
        mock_path_join.return_value = "/test/script/dir/log"
        
        # Create LoggingHandler instance
        LoggingHandler(self.script_dir)
        
        # Get the call arguments
        call_args = mock_basicConfig.call_args
        kwargs = call_args[1]
        
        # Test specific configuration values
        self.assertEqual(kwargs['filemode'], 'a')  # Append mode
        self.assertIn('%(asctime)s', kwargs['format'])  # Contains timestamp
        self.assertIn('%(name)s', kwargs['format'])     # Contains logger name
        self.assertIn('%(levelname)s', kwargs['format'])  # Contains log level
        self.assertIn('%(message)s', kwargs['format'])  # Contains message
        self.assertEqual(kwargs['datefmt'], '%d/%m/%Y %H:%M:%S')  # Date format
        
        print("✅ Logging configuration parameters test passed")

    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_log_filename_format(self, mock_basicConfig, mock_path_join):
        """Test log filename format includes current date"""
        mock_path_join.return_value = "/test/script/dir/log"
        
        # Create LoggingHandler instance
        LoggingHandler(self.script_dir)
        
        # Get the filename from the call
        call_args = mock_basicConfig.call_args
        kwargs = call_args[1]
        filename = kwargs['filename']
        
        # Check that filename contains today's date
        today_str = date.today().strftime("%Y-%m-%d")
        self.assertIn(today_str, filename)
        self.assertIn('kafka_sdp_log_', filename)
        self.assertIn('.log', filename)
        
        print("✅ Log filename format test passed")

    @patch('logging.getLogger')
    def test_get_logger_static_method(self, mock_getLogger):
        """Test get_logger static method"""
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        
        # Call static method
        result = LoggingHandler.get_logger("TestLogger")
        
        # Verify logging.getLogger was called with correct name
        mock_getLogger.assert_called_once_with("TestLogger")
        
        # Verify correct logger is returned
        self.assertEqual(result, mock_logger)
        
        print("✅ get_logger static method test passed")

    def test_get_logger_returns_different_loggers(self):
        """Test that get_logger returns different loggers for different names"""
        # This test uses actual logging module to verify behavior
        logger1 = LoggingHandler.get_logger("Logger1")
        logger2 = LoggingHandler.get_logger("Logger2")
        logger3 = LoggingHandler.get_logger("Logger1")  # Same name as logger1
        
        # Different names should give different loggers
        self.assertNotEqual(logger1, logger2)
        
        # Same names should give the same logger instance
        self.assertEqual(logger1, logger3)
        
        # Check logger names
        self.assertEqual(logger1.name, "Logger1")
        self.assertEqual(logger2.name, "Logger2")
        
        print("✅ get_logger different loggers test passed")

    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_multiple_logger_handler_instances(self, mock_basicConfig, mock_path_join):
        """Test creating multiple LoggingHandler instances"""
        mock_path_join.side_effect = lambda *args: "/".join(args)
        
        # Create multiple instances
        handler1 = LoggingHandler("/dir1")
        handler2 = LoggingHandler("/dir2")
        
        # Verify basicConfig was called multiple times
        self.assertEqual(mock_basicConfig.call_count, 2)
        
        # Verify path.join was called with different directories
        path_join_calls = mock_path_join.call_args_list
        self.assertEqual(path_join_calls[0][0], ("/dir1", "log"))
        self.assertEqual(path_join_calls[1][0], ("/dir2", "log"))
        
        print("✅ Multiple logger handler instances test passed")

    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_logging_level_setting(self, mock_basicConfig, mock_path_join):
        """Test that logging level is set to INFO"""
        import logging
        mock_path_join.return_value = "/test/log"
        
        # Create LoggingHandler instance
        LoggingHandler(self.script_dir)
        
        # Get the call arguments
        call_args = mock_basicConfig.call_args
        kwargs = call_args[1]
        
        # Verify logging level is set to INFO
        self.assertEqual(kwargs['level'], logging.INFO)
        
        print("✅ Logging level setting test passed")

    def test_logger_handler_with_empty_script_dir(self):
        """Test LoggingHandler with empty script directory"""
        with patch('os.path.join') as mock_path_join:
            with patch('logging.basicConfig') as mock_basicConfig:
                mock_path_join.return_value = "/log"
                
                # Create LoggingHandler with empty string
                LoggingHandler("")
                
                # Verify it still works
                mock_path_join.assert_called_once_with("", "log")
                mock_basicConfig.assert_called_once()
        
        print("✅ Empty script dir test passed")

    def test_logger_handler_with_special_characters(self):
        """Test LoggingHandler with special characters in path"""
        special_dir = "/test/dir with spaces/and-dashes"
        
        with patch('os.path.join') as mock_path_join:
            with patch('logging.basicConfig') as mock_basicConfig:
                mock_path_join.return_value = special_dir + "/log"
                
                # Create LoggingHandler with special characters
                LoggingHandler(special_dir)
                
                # Verify it handles special characters correctly
                mock_path_join.assert_called_once_with(special_dir, "log")
                mock_basicConfig.assert_called_once()
        
        print("✅ Special characters test passed")    @patch('Logger.date')
    @patch('os.path.join')
    @patch('logging.basicConfig')
    def test_log_filename_with_mocked_date(self, mock_basicConfig, mock_path_join, mock_date):
        """Test log filename generation with mocked date"""
        # Mock today's date
        mock_today = MagicMock()
        mock_today.strftime.return_value = "2023-07-15"
        mock_date.today.return_value = mock_today
        
        mock_path_join.return_value = "/test/log"
        
        # Create LoggingHandler instance
        LoggingHandler(self.script_dir)
        
        # Get the filename from the call
        call_args = mock_basicConfig.call_args
        kwargs = call_args[1]
        filename = kwargs['filename']
        
        # Verify the mocked date is used in filename
        self.assertIn("2023-07-15", filename)
        mock_today.strftime.assert_called_once_with("%Y-%m-%d")
        
        print("✅ Log filename with mocked date test passed")

    def test_get_logger_with_none_name(self):
        """Test get_logger with None as name"""
        with patch('logging.getLogger') as mock_getLogger:
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger
            
            # Call with None
            result = LoggingHandler.get_logger(None)
            
            # Verify logging.getLogger was called with None
            mock_getLogger.assert_called_once_with(None)
            self.assertEqual(result, mock_logger)
        
        print("✅ get_logger with None name test passed")

    def test_get_logger_with_empty_string(self):
        """Test get_logger with empty string as name"""
        with patch('logging.getLogger') as mock_getLogger:
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger
            
            # Call with empty string
            result = LoggingHandler.get_logger("")
            
            # Verify logging.getLogger was called with empty string
            mock_getLogger.assert_called_once_with("")
            self.assertEqual(result, mock_logger)
        
        print("✅ get_logger with empty string test passed")


if __name__ == '__main__':
    print("="*60)
    print("Running KAFKA_SDP_PREPAID Logger Module Tests")
    print("="*60)
    unittest.main(verbosity=2)
