#!/usr/bin/env python3
"""
Tests for KPI_SDP class in KAFKA_SDP_GEORED module
These tests focus on the KPI_SDP class functionality
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    from KPI_SDP import KPI_SDP
    KPI_SDP_IMPORT_SUCCESS = True
    KPI_SDP_IMPORT_ERROR = None
except Exception as e:
    KPI_SDP_IMPORT_SUCCESS = False
    KPI_SDP_IMPORT_ERROR = str(e)


class TestKpiSdpFixed(unittest.TestCase):
    """Test cases for KPI_SDP class"""

    def setUp(self):
        """Set up test fixtures"""
        if not KPI_SDP_IMPORT_SUCCESS:
            self.skipTest(f"KPI_SDP import failed: {KPI_SDP_IMPORT_ERROR}")

    def test_kpi_sdp_initialization(self):
        """Test KPI_SDP class initialization"""
        # Mock the LoggingHandler to avoid dependency issues
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            kpi_sdp = KPI_SDP(
                hostname="test-host",
                namespace="test-ns",
                pod="test-pod",
                script_dir="/test/script",
                output_dir="/test/output",
                archive_dir="/test/archive",
                log_dir="/test/log",
                pod_container="test-container"
            )
            
            # Test that basic attributes are set
            self.assertEqual(kpi_sdp.host_name, "test-host")
            self.assertEqual(kpi_sdp.namespace, "test-ns")
            self.assertEqual(kpi_sdp.pod, "test-pod")
            self.assertEqual(kpi_sdp.pod_container, "test-container")
            self.assertEqual(kpi_sdp.script_dir, "/test/script")
            self.assertEqual(kpi_sdp.output_dir, "/test/output")
            self.assertEqual(kpi_sdp.archive_dir, "/test/archive")
            self.assertEqual(kpi_sdp.log_dir, "/test/log")
            
        print("✅ KPI_SDP initialization test passed")

    def test_date_calculations(self):
        """Test date calculation attributes"""
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            kpi_sdp = KPI_SDP(
                hostname="test-host",
                namespace="test-ns", 
                pod="test-pod",
                script_dir="/test/script",
                output_dir="/test/output", 
                archive_dir="/test/archive",
                log_dir="/test/log",
                pod_container="test-container"
            )
            
            # Test date attributes
            self.assertIsInstance(kpi_sdp.yesterdayYMD, str)
            self.assertIsInstance(kpi_sdp.yesterdayYYMMDD, str)
            
            # Test date format
            yesterday = datetime.now() - timedelta(1)
            expected_ymd = yesterday.strftime('%Y-%m-%d')
            expected_yymmdd = yesterday.strftime('%y-%m-%d')
            
            self.assertEqual(kpi_sdp.yesterdayYMD, expected_ymd)
            self.assertEqual(kpi_sdp.yesterdayYYMMDD, expected_yymmdd)
            
        print("✅ Date calculations test passed")

    def test_logger_initialization(self):
        """Test that logger is properly initialized"""
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            kpi_sdp = KPI_SDP(
                hostname="test-host",
                namespace="test-ns",
                pod="test-pod", 
                script_dir="/test/script",
                output_dir="/test/output",
                archive_dir="/test/archive",
                log_dir="/test/log",
                pod_container="test-container"
            )
            
            # Verify logger was requested
            mock_logging.get_logger.assert_called_once_with('KPI_SDP')
            self.assertEqual(kpi_sdp._logger, mock_logger)
            
        print("✅ Logger initialization test passed")

    def test_parameter_assignment(self):
        """Test that all parameters are correctly assigned"""
        with patch('KPI_SDP.LoggingHandler'):
            test_params = {
                'hostname': 'geored-host-01',
                'namespace': 'chf-apps',
                'pod': 'csdp-geored-c-0',
                'script_dir': '/opt/cec/KAFKA_SDP_GEORED',
                'output_dir': '/opt/cec/KAFKA_SDP_GEORED/output',
                'archive_dir': '/opt/cec/KAFKA_SDP_GEORED/archive',
                'log_dir': '/opt/cec/KAFKA_SDP_GEORED/log',
                'pod_container': 'sdp'
            }
            
            kpi_sdp = KPI_SDP(**test_params)
            
            # Verify all parameters
            self.assertEqual(kpi_sdp.host_name, test_params['hostname'])
            self.assertEqual(kpi_sdp.namespace, test_params['namespace'])
            self.assertEqual(kpi_sdp.pod, test_params['pod'])
            self.assertEqual(kpi_sdp.script_dir, test_params['script_dir'])
            self.assertEqual(kpi_sdp.output_dir, test_params['output_dir'])
            self.assertEqual(kpi_sdp.archive_dir, test_params['archive_dir'])
            self.assertEqual(kpi_sdp.log_dir, test_params['log_dir'])
            self.assertEqual(kpi_sdp.pod_container, test_params['pod_container'])
            
        print("✅ Parameter assignment test passed")

    def test_time_calculations(self):
        """Test time-related calculations"""
        with patch('KPI_SDP.LoggingHandler'):
            kpi_sdp = KPI_SDP(
                hostname="test-host",
                namespace="test-ns",
                pod="test-pod",
                script_dir="/test/script", 
                output_dir="/test/output",
                archive_dir="/test/archive",
                log_dir="/test/log",
                pod_container="test-container"
            )
            
            # Test that date calculations are consistent
            now = datetime.now()
            yesterday = now - timedelta(1)
            
            # Date should be from yesterday
            self.assertTrue(kpi_sdp.yesterdayYMD.startswith(str(yesterday.year)))
            self.assertTrue(kpi_sdp.yesterdayYYMMDD.startswith(str(yesterday.year)[2:]))
            
            # Format should be correct
            self.assertEqual(len(kpi_sdp.yesterdayYMD), 10)  # YYYY-MM-DD
            self.assertEqual(len(kpi_sdp.yesterdayYYMMDD), 8)  # YY-MM-DD
            
        print("✅ Time calculations test passed")

    def test_class_attributes(self):
        """Test that class has expected attributes"""
        # Test class-level attributes
        self.assertTrue(hasattr(KPI_SDP, '__init__'))
        
        # Check if main method exists (should be defined in the class)
        kpi_methods = [method for method in dir(KPI_SDP) if not method.startswith('_')]
        self.assertTrue(len(kpi_methods) > 0, "KPI_SDP should have public methods")
        
        print("✅ Class attributes test passed")

    def test_logger_accessibility(self):
        """Test that logger is accessible after initialization"""
        with patch('KPI_SDP.LoggingHandler') as mock_logging:
            mock_logger = MagicMock()
            mock_logging.get_logger.return_value = mock_logger
            
            kpi_sdp = KPI_SDP(
                hostname="test-host",
                namespace="test-ns",
                pod="test-pod",
                script_dir="/test/script",
                output_dir="/test/output", 
                archive_dir="/test/archive",
                log_dir="/test/log",
                pod_container="test-container"
            )
            
            # Test that logger is accessible
            self.assertIsNotNone(kpi_sdp._logger)
            self.assertEqual(kpi_sdp._logger, mock_logger)
            
            # Test that we can call logger methods (they should be mocked)
            kpi_sdp._logger.info("Test message")
            mock_logger.info.assert_called_with("Test message")
            
        print("✅ Logger accessibility test passed")

    def test_geored_specific_setup(self):
        """Test GEORED-specific initialization"""
        with patch('KPI_SDP.LoggingHandler'):
            # Test with GEORED-specific values
            kpi_sdp = KPI_SDP(
                hostname="geored-node-1",
                namespace="chf-ec-apps", 
                pod="csdp-geored-c-0",
                script_dir="/opt/cec/KAFKA_SDP_GEORED",
                output_dir="/opt/cec/KAFKA_SDP_GEORED/output",
                archive_dir="/opt/cec/KAFKA_SDP_GEORED/archive", 
                log_dir="/opt/cec/KAFKA_SDP_GEORED/log",
                pod_container="sdp"
            )
            
            # Verify GEORED-specific setup
            self.assertIn("geored", kpi_sdp.host_name.lower())
            self.assertEqual(kpi_sdp.pod_container, "sdp")
            self.assertIn("GEORED", kpi_sdp.script_dir)
            
        print("✅ GEORED-specific setup test passed")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        with patch('KPI_SDP.LoggingHandler'):
            # Test with empty strings
            kpi_sdp = KPI_SDP(
                hostname="",
                namespace="",
                pod="",
                script_dir="",
                output_dir="",
                archive_dir="", 
                log_dir="",
                pod_container=""
            )
            
            # Should not raise exception
            self.assertEqual(kpi_sdp.host_name, "")
            self.assertEqual(kpi_sdp.namespace, "")
            self.assertEqual(kpi_sdp.pod, "")
            
            # Date calculations should still work
            self.assertIsInstance(kpi_sdp.yesterdayYMD, str)
            self.assertIsInstance(kpi_sdp.yesterdayYYMMDD, str)
            
        print("✅ Edge cases test passed")


if __name__ == '__main__':
    print("=" * 70)
    print("KAFKA_SDP_GEORED - KPI_SDP Class Tests (Fixed)")
    print("=" * 70)
    print("Testing KPI_SDP class initialization and basic functionality")
    print("=" * 70)
    
    unittest.main(verbosity=2)
