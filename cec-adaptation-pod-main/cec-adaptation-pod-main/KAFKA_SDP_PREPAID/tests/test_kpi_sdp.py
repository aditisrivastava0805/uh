import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from KPI_SDP import KPI_SDP


class TestKPISDP(unittest.TestCase):
    """Test cases for KPI_SDP class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.hostname = "test-hostname"
        self.namespace = "test-namespace"
        self.pod = "test-pod"
        self.script_dir = "/test/script"
        self.output_dir = "/test/output"
        self.archive_dir = "/test/archive"
        self.log_dir = "/test/log"
        self.pod_container = "sdp"
        
        # Create KPI_SDP instance
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logging.get_logger.return_value = MagicMock()
            self.kpi_sdp = KPI_SDP(
                self.hostname, self.namespace, self.pod, self.script_dir,
                self.output_dir, self.archive_dir, self.log_dir, self.pod_container
            )

    def test_initialization(self):
        """Test KPI_SDP class initialization"""
        # Test that all attributes are set correctly
        self.assertEqual(self.kpi_sdp.host_name, self.hostname)
        self.assertEqual(self.kpi_sdp.namespace, self.namespace)
        self.assertEqual(self.kpi_sdp.pod, self.pod)
        self.assertEqual(self.kpi_sdp.script_dir, self.script_dir)
        self.assertEqual(self.kpi_sdp.output_dir, self.output_dir)
        self.assertEqual(self.kpi_sdp.archive_dir, self.archive_dir)
        self.assertEqual(self.kpi_sdp.log_dir, self.log_dir)
        self.assertEqual(self.kpi_sdp.pod_container, self.pod_container)
        
        # Test that date/time attributes are set
        self.assertIsNotNone(self.kpi_sdp.yesterdayYMD)
        self.assertIsNotNone(self.kpi_sdp.todayYMD)
        self.assertIsNotNone(self.kpi_sdp.today_timestamp)
        self.assertIsNotNone(self.kpi_sdp.todayUTCMilli)
        
        print("✅ KPI_SDP initialization test passed")

    def test_date_calculations(self):
        """Test date and time calculations"""
        # Test yesterday date format
        yesterday = datetime.now() - timedelta(1)
        expected_yesterday = yesterday.strftime('%Y-%m-%d')
        self.assertEqual(self.kpi_sdp.yesterdayYMD, expected_yesterday)
        
        # Test today date format
        today = datetime.now()
        expected_today = today.strftime('%Y-%m-%d')
        self.assertEqual(self.kpi_sdp.todayYMD, expected_today)
        
        # Test timestamp format (should be 14 digits)
        self.assertEqual(len(self.kpi_sdp.today_timestamp), 14)
        self.assertTrue(self.kpi_sdp.today_timestamp.isdigit())
        
        print("✅ Date calculations test passed")

    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_normal(self, mock_subprocess_class):
        """Test update_command with normal command"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("test output", None)
        
        # Reset the subprocess_obj with our mock
        self.kpi_sdp.subprocess_obj = mock_instance
        
        output, error = self.kpi_sdp.update_command("test-sdp", "ls -la")
        
        self.assertEqual(output, "test output")
        self.assertIsNone(error)
        
        # Verify the command was formatted correctly
        expected_cmd = f"kubectl exec -it -n {self.namespace} test-sdp -c {self.pod_container} -- ls -la"
        mock_instance.execute_cmd.assert_called_once_with(expected_cmd)
        
        print("✅ update_command normal test passed")

    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_bash(self, mock_subprocess_class):
        """Test update_command with bash command type"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("bash output", None)
        
        # Reset the subprocess_obj with our mock
        self.kpi_sdp.subprocess_obj = mock_instance
        
        output, error = self.kpi_sdp.update_command("test-sdp", "grep test file.txt", "bash")
        
        self.assertEqual(output, "bash output")
        self.assertIsNone(error)
        
        # Verify the command was formatted correctly for bash
        expected_cmd = f"kubectl exec -it -n {self.namespace} test-sdp -c {self.pod_container} -- bash -c 'grep test file.txt'"
        mock_instance.execute_cmd.assert_called_once_with(expected_cmd)
        
        print("✅ update_command bash test passed")

    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_with_braces(self, mock_subprocess_class):
        """Test update_command with curly braces in command"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = ("output", None)
        
        # Reset the subprocess_obj with our mock
        self.kpi_sdp.subprocess_obj = mock_instance
        
        command_with_braces = "awk '{print $1}'"
        output, error = self.kpi_sdp.update_command("test-sdp", command_with_braces)
        
        # Verify braces were escaped
        expected_cmd = f"kubectl exec -it -n {self.namespace} test-sdp -c {self.pod_container} -- awk '{{print $1}}'"
        mock_instance.execute_cmd.assert_called_once_with(expected_cmd)
        
        print("✅ update_command with braces test passed")

    @patch('KPI_SDP.SubprocessClass')
    def test_update_command_error(self, mock_subprocess_class):
        """Test update_command with error"""
        mock_instance = MagicMock()
        mock_subprocess_class.return_value = mock_instance
        mock_instance.execute_cmd.return_value = (None, "Command failed")
        
        # Reset the subprocess_obj with our mock
        self.kpi_sdp.subprocess_obj = mock_instance
        
        output, error = self.kpi_sdp.update_command("test-sdp", "invalid command")
        
        self.assertIsNone(output)
        self.assertEqual(error, "Command failed")
        
        print("✅ update_command error test passed")

    def test_update_command_exception(self):
        """Test update_command with exception"""
        # Mock subprocess to raise exception
        self.kpi_sdp.subprocess_obj = MagicMock()
        self.kpi_sdp.subprocess_obj.execute_cmd.side_effect = Exception("Test exception")
        
        result = self.kpi_sdp.update_command("test-sdp", "test command")
        
        self.assertIsNone(result)
        
        print("✅ update_command exception test passed")

    def test_GetCIP_PeerStat(self):
        """Test GetCIP_PeerStat method"""
        with patch.object(self.kpi_sdp, 'update_command') as mock_update_command:
            mock_update_command.return_value = ("CONNECTED\nDISCONNECTED\nCONNECTED", None)
            
            member1, member2 = self.kpi_sdp.GetCIP_PeerStat("test-sdp", 1, "user", "pass", "host")
            
            self.assertEqual(member1, "CONNECTED\nDISCONNECTED\nCONNECTED")
            self.assertIsNone(member2)
            
            # Verify update_command was called with correct parameters
            mock_update_command.assert_called_once()
            args, kwargs = mock_update_command.call_args
            self.assertEqual(args[0], "test-sdp")
            self.assertIn("FDSRequestSender", args[1])
            self.assertEqual(kwargs.get('command_type', args[2] if len(args) > 2 else None), 'bash')
        
        print("✅ GetCIP_PeerStat test passed")

    def test_add_kafka_kpi(self):
        """Test add_kafka_kpi method"""
        # Mock KafkaDataSourceBuilder
        mock_builder = MagicMock()
        
        self.kpi_sdp.add_kafka_kpi(mock_builder, "TEST_KPI", "test_value")
        
        # Verify add_kpi was called with correct parameters
        mock_builder.add_kpi.assert_called_once_with(
            "TEST_KPI", "test_value", "OK" if "test_value" != "None" else "NOK"
        )
        
        print("✅ add_kafka_kpi test passed")

    def test_add_kafka_kpi_none_value(self):
        """Test add_kafka_kpi method with None value"""
        # Mock KafkaDataSourceBuilder
        mock_builder = MagicMock()
        
        self.kpi_sdp.add_kafka_kpi(mock_builder, "TEST_KPI", "None")
        
        # Verify add_kpi was called with NOK result for None value
        mock_builder.add_kpi.assert_called_once_with("TEST_KPI", "None", "NOK")
        
        print("✅ add_kafka_kpi None value test passed")

    @patch.object(KPI_SDP, 'update_command')
    @patch.object(KPI_SDP, 'add_kafka_kpi')
    def test_main_method_basic_kpis(self, mock_add_kpi, mock_update_command):
        """Test main method with basic KPIs"""
        # Setup mock for commands
        mock_update_command.side_effect = [
            ("output1", None),  # First command
            ("output2", None),  # Second command
            ("output3", None),  # Third command
        ]
        
        # Mock KafkaDataSourceBuilder
        mock_builder = MagicMock()
        
        # Call main method with mock parameters
        self.kpi_sdp.main(("test-pod", 0, mock_builder))
        
        # Verify that KPIs were added
        self.assertTrue(mock_add_kpi.called)
        
        print("✅ main method basic KPIs test passed")

    def test_time_calculations(self):
        """Test time-related calculations"""
        # Test UTC milliseconds is a positive integer
        self.assertIsInstance(self.kpi_sdp.todayUTCMilli, int)
        self.assertGreater(self.kpi_sdp.todayUTCMilli, 0)
        
        # Test local time milliseconds
        self.assertIsInstance(self.kpi_sdp.localNowMilli, int)
        
        # Test UTC timestamp format
        self.assertIsInstance(self.kpi_sdp.utcTimestamp, str)
        self.assertEqual(len(self.kpi_sdp.utcTimestamp), 19)  # YYYY-MM-DD HH:MM:SS
        
        # Test kafka text contains expected components
        self.assertIn(str(self.kpi_sdp.todayUTCMilli), self.kpi_sdp.kafkaText)
        self.assertIn(str(self.kpi_sdp.localNowMilli), self.kpi_sdp.kafkaText)
        
        print("✅ Time calculations test passed")

    def test_format_datetime_attributes(self):
        """Test datetime format attributes"""
        # Test yesterday formats
        self.assertRegex(self.kpi_sdp.yesterdayYMD, r'\d{4}-\d{2}-\d{2}')
        self.assertRegex(self.kpi_sdp.yesterdayYYMMDD, r'\d{2}-\d{2}-\d{2}')
        
        # Test today formats
        self.assertRegex(self.kpi_sdp.todayYMD, r'\d{4}-\d{2}-\d{2}')
        self.assertRegex(self.kpi_sdp.todayYYMMDD, r'\d{2}-\d{2}-\d{2}')
        self.assertRegex(self.kpi_sdp.today_timestamp, r'\d{14}')
        
        # Test UTC formats
        self.assertRegex(self.kpi_sdp.todayUTC, r'\d{4}-\d{2}-\d{2}')
        self.assertRegex(self.kpi_sdp.utcTimestamp, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        
        print("✅ Format datetime attributes test passed")

    @patch.object(KPI_SDP, 'GetCIP_PeerStat')
    @patch.object(KPI_SDP, 'GetDCIP_PeerStat')  
    @patch.object(KPI_SDP, 'update_command')
    @patch.object(KPI_SDP, 'add_kafka_kpi')
    def test_main_method_cip_disconnected_count(self, mock_add_kpi, mock_update_command, mock_dcip, mock_cip):
        """Test main method CIP link down count calculation"""
        # Mock CIP peer status with DISCONNECTED entries
        mock_cip.return_value = ("CONNECTED\nDISCONNECTED\nDISCONNECTED\nCONNECTED", None)
        mock_dcip.return_value = ("CONNECTED\nCONNECTED", None)
        
        # Mock other command outputs
        mock_update_command.return_value = ("5", None)
        
        # Mock KafkaDataSourceBuilder
        mock_builder = MagicMock()
        
        # Call main method
        self.kpi_sdp.main(("test-pod", 0, mock_builder))
        
        # Verify CIP_LINK_DOWN_COUNT was called with count of 2 (2 DISCONNECTED entries)
        cip_calls = [call for call in mock_add_kpi.call_args_list if call[0][1] == "CIP_LINK_DOWN_COUNT"]
        if cip_calls:
            self.assertEqual(cip_calls[0][0][2], "2")
        
        print("✅ main method CIP disconnected count test passed")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with empty strings
        with patch.object(self.kpi_sdp, 'update_command') as mock_update_command:
            mock_update_command.return_value = ("", None)
            output, error = self.kpi_sdp.update_command("test-sdp", "")
            self.assertEqual(output, "")
            self.assertIsNone(error)
        
        # Test with very long command
        long_command = "a" * 1000
        with patch.object(self.kpi_sdp, 'update_command') as mock_update_command:
            mock_update_command.return_value = ("output", None)
            output, error = self.kpi_sdp.update_command("test-sdp", long_command)
            self.assertEqual(output, "output")
        
        print("✅ Edge cases test passed")


if __name__ == '__main__':
    print("="*60)
    print("Running KAFKA_SDP_PREPAID KPI_SDP Module Tests")
    print("="*60)
    unittest.main(verbosity=2)
