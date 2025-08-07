import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import subprocess

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SubprocessClass import SubprocessClass


class TestSubprocessClass(unittest.TestCase):
    """Test cases for SubprocessClass"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('SubprocessClass.LoggingHandler') as mock_logging:
            mock_logging.get_logger.return_value = MagicMock()
            self.subprocess_obj = SubprocessClass()

    @patch('subprocess.Popen')
    def test_execute_cmd_success_with_output(self, mock_popen):
        """Test execute_cmd with successful command that returns output"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"test output", b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("echo 'test'")
        
        self.assertEqual(output, "test output")
        self.assertIsNone(error)
        
        # Verify process cleanup
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        
        print("✅ execute_cmd success with output test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_success_with_error(self, mock_popen):
        """Test execute_cmd with command that returns error"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"command error")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("invalid_command")
        
        self.assertIsNone(output)
        self.assertEqual(error, "command error")
        
        # Verify process cleanup
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        
        print("✅ execute_cmd success with error test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_with_both_output_and_error(self, mock_popen):
        """Test execute_cmd with both output and error"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"some output", b"some error")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("test_command")
        
        # When there's output, it should return output and None for error
        self.assertEqual(output, "some output")
        self.assertIsNone(error)
        
        print("✅ execute_cmd with both output and error test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_popen_parameters(self, mock_popen):
        """Test execute_cmd Popen is called with correct parameters"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_popen.return_value = mock_process
        
        self.subprocess_obj.execute_cmd("test command")
        
        # Verify Popen was called with correct parameters
        mock_popen.assert_called_once_with(
            "test command",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("✅ execute_cmd Popen parameters test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_exception_handling(self, mock_popen):
        """Test execute_cmd exception handling"""
        # Mock Popen to raise exception
        mock_popen.side_effect = Exception("Popen failed")
        
        result = self.subprocess_obj.execute_cmd("test command")
        
        # Should return None when exception occurs
        self.assertIsNone(result)
        
        print("✅ execute_cmd exception handling test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_communicate_exception(self, mock_popen):
        """Test execute_cmd when communicate raises exception"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.side_effect = Exception("Communication failed")
        mock_popen.return_value = mock_process
        
        result = self.subprocess_obj.execute_cmd("test command")
        
        # Should return None when communicate fails
        self.assertIsNone(result)
        
        # Verify cleanup is still attempted
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        
        print("✅ execute_cmd communicate exception test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_cleanup_exception(self, mock_popen):
        """Test execute_cmd when cleanup raises exception"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.terminate.side_effect = Exception("Terminate failed")
        mock_process.kill.side_effect = Exception("Kill failed")
        mock_popen.return_value = mock_process
        
        # Should still work despite cleanup exceptions
        output, error = self.subprocess_obj.execute_cmd("test command")
        
        self.assertEqual(output, "output")
        self.assertIsNone(error)
        
        print("✅ execute_cmd cleanup exception test passed")

    @patch('os.killpg')
    @patch('os.getpgid')
    def test_kill_proc_success(self, mock_getpgid, mock_killpg):
        """Test kill_proc with successful process termination"""
        mock_getpgid.return_value = 1234
        
        self.subprocess_obj.kill_proc(5678)
        
        mock_getpgid.assert_called_once_with(5678)
        mock_killpg.assert_called_once_with(1234, 15)  # SIGTERM = 15
        
        print("✅ kill_proc success test passed")

    @patch('os.killpg')
    @patch('os.getpgid')
    def test_kill_proc_exception(self, mock_getpgid, mock_killpg):
        """Test kill_proc exception handling"""
        mock_getpgid.side_effect = Exception("Process not found")
        
        # Should not raise exception
        self.subprocess_obj.kill_proc(5678)
        
        mock_getpgid.assert_called_once_with(5678)
        mock_killpg.assert_not_called()
        
        print("✅ kill_proc exception test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_without_shell_success(self, mock_popen):
        """Test execute_cmd_without_shell with success"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"output without shell", b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd_without_shell(["echo", "test"])
        
        self.assertEqual(output, "output without shell")
        self.assertIsNone(error)
        
        # Verify Popen was called without shell=True
        mock_popen.assert_called_once_with(
            ["echo", "test"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("✅ execute_cmd_without_shell success test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_without_shell_error(self, mock_popen):
        """Test execute_cmd_without_shell with error"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"error message")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd_without_shell(["invalid", "command"])
        
        self.assertIsNone(output)
        self.assertEqual(error, "error message")
        
        print("✅ execute_cmd_without_shell error test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_without_shell_empty_output(self, mock_popen):
        """Test execute_cmd_without_shell with empty output"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd_without_shell(["true"])
        
        self.assertIsNone(output)
        self.assertIsNone(error)
        
        print("✅ execute_cmd_without_shell empty output test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_without_shell_exception(self, mock_popen):
        """Test execute_cmd_without_shell exception handling"""
        mock_popen.side_effect = Exception("Popen failed")
        
        result = self.subprocess_obj.execute_cmd_without_shell(["test"])
        
        self.assertIsNone(result)
        
        print("✅ execute_cmd_without_shell exception test passed")

    def test_subprocess_class_initialization(self):
        """Test SubprocessClass initialization"""
        with patch('SubprocessClass.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            subprocess_obj = SubprocessClass()
            
            # Verify logger was obtained
            mock_logging.get_logger.assert_called_once_with('SubprocessClass')
            self.assertEqual(subprocess_obj._logger, mock_logger)
        
        print("✅ SubprocessClass initialization test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_unicode_handling(self, mock_popen):
        """Test execute_cmd with unicode characters"""
        # Mock process with unicode output
        mock_process = MagicMock()
        unicode_output = "Test with unicode: ñáéíóú".encode('utf-8')
        mock_process.communicate.return_value = (unicode_output, b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("echo unicode")
        
        self.assertEqual(output, "Test with unicode: ñáéíóú")
        self.assertIsNone(error)
        
        print("✅ execute_cmd unicode handling test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_large_output(self, mock_popen):
        """Test execute_cmd with large output"""
        # Mock process with large output
        mock_process = MagicMock()
        large_output = ("x" * 10000).encode('utf-8')
        mock_process.communicate.return_value = (large_output, b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("generate large output")
        
        self.assertEqual(len(output), 10000)
        self.assertTrue(output.startswith("x"))
        self.assertIsNone(error)
        
        print("✅ execute_cmd large output test passed")

    @patch('subprocess.Popen')
    def test_execute_cmd_empty_command(self, mock_popen):
        """Test execute_cmd with empty command"""
        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        output, error = self.subprocess_obj.execute_cmd("")
        
        # Verify empty command is passed to Popen
        mock_popen.assert_called_once_with(
            "",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("✅ execute_cmd empty command test passed")

    @patch('os.killpg')
    @patch('os.getpgid')
    def test_kill_proc_with_zero_pid(self, mock_getpgid, mock_killpg):
        """Test kill_proc with zero process ID"""
        mock_getpgid.return_value = 0
        
        self.subprocess_obj.kill_proc(0)
        
        mock_getpgid.assert_called_once_with(0)
        mock_killpg.assert_called_once_with(0, 15)
        
        print("✅ kill_proc with zero PID test passed")


if __name__ == '__main__':
    print("="*60)
    print("Running KAFKA_SDP_PREPAID SubprocessClass Module Tests")
    print("="*60)
    unittest.main(verbosity=2)
