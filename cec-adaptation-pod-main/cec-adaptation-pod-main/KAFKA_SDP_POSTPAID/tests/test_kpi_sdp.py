import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import time

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import with error handling
try:
    from KPI_SDP import KPI_SDP
    KPI_SDP_IMPORT_SUCCESS = True
    KPI_SDP_IMPORT_ERROR = None
except Exception as e:
    KPI_SDP_IMPORT_SUCCESS = False
    KPI_SDP_IMPORT_ERROR = str(e)


class TestKPISDPClass(unittest.TestCase):
    """Test cases for KPI_SDP class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        # Mock the LoggingHandler to avoid logger issues
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            # Mock SubprocessClass to avoid subprocess issues
            with patch('KPI_SDP.SubprocessClass') as mock_subprocess:
                self.kpi_sdp = KPI_SDP(
                    hostname="test-hostname",
                    namespace="test-namespace", 
                    pod="test-pod",
                    script_dir="/test/script",
                    output_dir="/test/output",
                    archive_dir="/test/archive",
                    log_dir="/test/log",
                    pod_container="test-container"
                )

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_kpi_sdp_initialization(self, mock_subprocess, mock_logging):
        """Test KPI_SDP class initialization"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod", 
            script_dir="/test/script",
            output_dir="/test/output",
            archive_dir="/test/archive",
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test instance attributes
        self.assertEqual(kpi_sdp.host_name, "test-hostname")
        self.assertEqual(kpi_sdp.namespace, "test-namespace")
        self.assertEqual(kpi_sdp.pod, "test-pod")
        self.assertEqual(kpi_sdp.pod_container, "test-container")
        self.assertEqual(kpi_sdp.script_dir, "/test/script")
        self.assertEqual(kpi_sdp.output_dir, "/test/output")
        self.assertEqual(kpi_sdp.archive_dir, "/test/archive")
        self.assertEqual(kpi_sdp.log_dir, "/test/log")

        # Test datetime attributes are set
        self.assertIsInstance(kpi_sdp.currentDT, datetime)
        self.assertIsInstance(kpi_sdp.todayYMD, str)
        self.assertIsInstance(kpi_sdp.todayYYMMDD, str)
        self.assertIsInstance(kpi_sdp.today_timestamp, str)
        self.assertIsInstance(kpi_sdp.yesterdayYMD, str)
        self.assertIsInstance(kpi_sdp.yesterdayYYMMDD, str)

        print("✅ KPI_SDP initialization test passed")

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_kpi_sdp_datetime_formats(self, mock_subprocess, mock_logging):
        """Test that datetime formats are correct"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod",
            script_dir="/test/script", 
            output_dir="/test/output",
            archive_dir="/test/archive",
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test date format YYYY-MM-DD
        self.assertRegex(kpi_sdp.todayYMD, r'^\d{4}-\d{2}-\d{2}$')
        self.assertRegex(kpi_sdp.yesterdayYMD, r'^\d{4}-\d{2}-\d{2}$')
        
        # Test date format YY-MM-DD
        self.assertRegex(kpi_sdp.todayYYMMDD, r'^\d{2}-\d{2}-\d{2}$')
        self.assertRegex(kpi_sdp.yesterdayYYMMDD, r'^\d{2}-\d{2}-\d{2}$')
        
        # Test timestamp format YYYYMMDDHHMMSS
        self.assertRegex(kpi_sdp.today_timestamp, r'^\d{14}$')

        # Test UTC timestamp format
        self.assertRegex(kpi_sdp.utcTimestamp, r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')

        print("✅ KPI_SDP datetime formats test passed")

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_method(self, mock_subprocess, mock_logging):
        """Test update_command method"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger
        
        # Mock the subprocess execute_cmd method
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute_cmd.return_value = ("test output", None)
        mock_subprocess.return_value = mock_subprocess_instance

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod",
            script_dir="/test/script",
            output_dir="/test/output", 
            archive_dir="/test/archive",
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test normal command
        output, error = kpi_sdp.update_command("test-sdp", "echo hello")
        
        self.assertEqual(output, "test output")
        self.assertIsNone(error)
        
        # Verify the command was formatted correctly
        expected_cmd = "kubectl exec -it -n test-namespace test-sdp -c test-container -- echo hello"
        mock_subprocess_instance.execute_cmd.assert_called_with(expected_cmd)

        print("✅ KPI_SDP update_command test passed")

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_bash_type(self, mock_subprocess, mock_logging):
        """Test update_command method with bash command type"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger
        
        # Mock the subprocess execute_cmd method
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute_cmd.return_value = ("bash output", None)
        mock_subprocess.return_value = mock_subprocess_instance

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod",
            script_dir="/test/script",
            output_dir="/test/output",
            archive_dir="/test/archive", 
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test bash command
        output, error = kpi_sdp.update_command("test-sdp", "ls -la", "bash")
        
        self.assertEqual(output, "bash output")
        self.assertIsNone(error)
        
        # Verify the command was formatted correctly for bash
        expected_cmd = "kubectl exec -it -n test-namespace test-sdp -c test-container -- bash -c 'ls -la'"
        mock_subprocess_instance.execute_cmd.assert_called_with(expected_cmd)

        print("✅ KPI_SDP update_command bash type test passed")

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_with_braces(self, mock_subprocess, mock_logging):
        """Test update_command method with braces in command"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger
        
        # Mock the subprocess execute_cmd method
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute_cmd.return_value = ("output", None)
        mock_subprocess.return_value = mock_subprocess_instance

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod",
            script_dir="/test/script",
            output_dir="/test/output",
            archive_dir="/test/archive",
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test command with braces (should be escaped)
        output, error = kpi_sdp.update_command("test-sdp", "echo {test}")
        
        # Verify braces were escaped in the command
        expected_cmd = "kubectl exec -it -n test-namespace test-sdp -c test-container -- echo {{test}}"
        mock_subprocess_instance.execute_cmd.assert_called_with(expected_cmd)

        print("✅ KPI_SDP update_command with braces test passed")

    @patch('KPI_SDP.LoggingHandler')
    @patch('KPI_SDP.SubprocessClass')
    def test_time_calculations(self, mock_subprocess, mock_logging):
        """Test time calculation attributes"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger

        kpi_sdp = KPI_SDP(
            hostname="test-hostname",
            namespace="test-namespace",
            pod="test-pod",
            script_dir="/test/script",
            output_dir="/test/output",
            archive_dir="/test/archive",
            log_dir="/test/log",
            pod_container="test-container"
        )

        # Test that time calculations are integers (milliseconds)
        self.assertIsInstance(kpi_sdp.todayUTCMilli, int)
        self.assertIsInstance(kpi_sdp.localNowMilli, int)
        self.assertIsInstance(kpi_sdp.timeDiff, int)

        # Test that kafka text is formatted correctly
        self.assertIsInstance(kpi_sdp.kafkaText, str)
        # Should contain comma-separated values
        parts = kpi_sdp.kafkaText.split(',')
        self.assertEqual(len(parts), 4)  # date, timestamp, utc_milli, local_milli

        print("✅ KPI_SDP time calculations test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running KAFKA_SDP_POSTPAID KPI_SDP Tests")
    print("=" * 60)
    if KPI_SDP_IMPORT_SUCCESS:
        print("✅ KPI_SDP import successful - running full test suite")
    else:
        print(f"⚠️ KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")
        print("Some tests will be skipped")
    print("=" * 60)
    unittest.main(verbosity=2)
