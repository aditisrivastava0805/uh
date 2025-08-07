import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'lib'))

from lib.Namespace import get_application_namespace, get_adaptation_namespace, execute_cmd


class TestNamespace(unittest.TestCase):
    """Test cases for Namespace module"""

    @patch('lib.Namespace.execute_cmd')
    def test_get_application_namespace_success(self, mock_execute_cmd):
        """Test successful retrieval of application namespace"""
        mock_execute_cmd.return_value = ("test-app-namespace\n", None)
        
        result = get_application_namespace()
        
        self.assertEqual(result, "test-app-namespace")
        mock_execute_cmd.assert_called_once()

    @patch('lib.Namespace.execute_cmd')
    def test_get_application_namespace_error(self, mock_execute_cmd):
        """Test error handling in get_application_namespace"""
        mock_execute_cmd.return_value = (None, "File not found")
        
        result = get_application_namespace()
        
        self.assertEqual(result, "No Namespace Found in File /home/ericuser/.env")
        mock_execute_cmd.assert_called_once()

    @patch('lib.Namespace.execute_cmd')
    def test_get_adaptation_namespace_success(self, mock_execute_cmd):
        """Test successful retrieval of adaptation namespace"""
        mock_execute_cmd.return_value = ("test-adaptation-namespace\n", None)
        
        result = get_adaptation_namespace()
        
        self.assertEqual(result, "test-adaptation-namespace")
        mock_execute_cmd.assert_called_once()

    @patch('lib.Namespace.execute_cmd')
    def test_get_adaptation_namespace_error(self, mock_execute_cmd):
        """Test error handling in get_adaptation_namespace"""
        mock_execute_cmd.return_value = (None, "File not found")
        
        result = get_adaptation_namespace()
        
        self.assertEqual(result, "No Namespace Found in File /home/ericuser/.env")
        mock_execute_cmd.assert_called_once()

    @patch('subprocess.Popen')
    def test_execute_cmd_success(self, mock_popen):
        """Test successful command execution"""
        # Mock subprocess
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_popen.return_value = mock_process
        
        out, err = execute_cmd("test command")
        
        self.assertEqual(out, "output")
        self.assertIsNone(err)
        mock_popen.assert_called_once_with("test command", shell=True, stdout=-1, stderr=-1)

    @patch('subprocess.Popen')
    def test_execute_cmd_with_error(self, mock_popen):
        """Test command execution with error"""
        # Mock subprocess
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"error message")
        mock_popen.return_value = mock_process
        
        out, err = execute_cmd("test command")
        
        self.assertIsNone(out)
        self.assertEqual(err, "error message")

    @patch('subprocess.Popen')
    def test_execute_cmd_empty_output(self, mock_popen):
        """Test command execution with empty output"""
        # Mock subprocess
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        out, err = execute_cmd("test command")
        
        self.assertIsNone(out)
        self.assertIsNone(err)


if __name__ == '__main__':
    unittest.main()
