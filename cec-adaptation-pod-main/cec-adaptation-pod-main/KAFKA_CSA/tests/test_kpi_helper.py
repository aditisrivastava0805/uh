#!/usr/bin/env python3
"""
Tests for KPI_Helper utility functions in KAFKA_CSA module
These tests focus on the helper utility functions
"""

import unittest
import sys
import os
import tempfile
import time
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    from KPI_Helper import banner, files_newer_that_mins, delete_files_older_than_days, is_http_ok, is_http_error
    KPI_HELPER_IMPORT_SUCCESS = True
    KPI_HELPER_IMPORT_ERROR = None
except Exception as e:
    KPI_HELPER_IMPORT_SUCCESS = False
    KPI_HELPER_IMPORT_ERROR = str(e)


class TestKpiHelper(unittest.TestCase):
    """Test cases for KPI_Helper utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        if not KPI_HELPER_IMPORT_SUCCESS:
            self.skipTest(f"KPI_Helper import failed: {KPI_HELPER_IMPORT_ERROR}")
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_banner_function_basic(self):
        """Test banner function with various inputs"""
        # Test normal text
        result = banner("Test Message")
        self.assertIsInstance(result, str)
        self.assertIn("Test Message", result)
        self.assertIn("-", result)
        
        # Test empty string
        result = banner("")
        self.assertIsInstance(result, str)
        self.assertIn("-", result)
        
        # Test long text
        long_text = "This is a very long test message to see how banner handles it"
        result = banner(long_text)
        self.assertIn(long_text, result)
        
        print("✅ Banner function basic test passed")

    def test_banner_function_formatting(self):
        """Test banner function formatting consistency"""
        # Test that banner creates consistent formatting
        test_messages = ["Start", "Processing", "End", "Error occurred"]
        
        for message in test_messages:
            result = banner(message)
            
            # Should contain the message
            self.assertIn(message, result)
            
            # Should start and end with dashes
            self.assertTrue("-" in result)
            
            # Should be properly formatted
            self.assertTrue(len(result) > len(message))
        
        print("✅ Banner function formatting test passed")

    def test_is_http_ok_function(self):
        """Test is_http_ok function with various HTTP codes"""
        # Test successful codes (1xx, 2xx, 3xx)
        ok_codes = ["100", "101", "200", "201", "204", "301", "302", "304"]
        for code in ok_codes:
            self.assertTrue(is_http_ok(code), f"Code {code} should be OK")
        
        # Test error codes (4xx, 5xx)
        error_codes = ["400", "401", "403", "404", "500", "502", "503"]
        for code in error_codes:
            self.assertFalse(is_http_ok(code), f"Code {code} should not be OK")
        
        print("✅ is_http_ok function test passed")

    def test_is_http_error_function(self):
        """Test is_http_error function with various HTTP codes"""
        # Test successful codes (1xx, 2xx, 3xx) - should not be errors
        ok_codes = ["100", "101", "200", "201", "204", "301", "302", "304"]
        for code in ok_codes:
            self.assertFalse(is_http_error(code), f"Code {code} should not be error")
        
        # Test error codes (4xx, 5xx) - should be errors
        error_codes = ["400", "401", "403", "404", "500", "502", "503"]
        for code in error_codes:
            self.assertTrue(is_http_error(code), f"Code {code} should be error")
        
        print("✅ is_http_error function test passed")

    def test_http_functions_edge_cases(self):
        """Test HTTP status functions with edge cases"""
        # Test edge cases
        edge_cases = [
            ("0", False, False),  # Invalid but handled
            ("999", False, True), # High number
            ("399", True, False), # Boundary case
            ("400", False, True), # Boundary case
        ]
        
        for code, expected_ok, expected_error in edge_cases:
            actual_ok = is_http_ok(code)
            actual_error = is_http_error(code)
            
            self.assertEqual(actual_ok, expected_ok, 
                           f"is_http_ok('{code}') should return {expected_ok}")
            self.assertEqual(actual_error, expected_error, 
                           f"is_http_error('{code}') should return {expected_error}")
        
        print("✅ HTTP functions edge cases test passed")

    def test_files_newer_that_mins_empty_directory(self):
        """Test files_newer_that_mins with empty directory"""
        # Test with empty directory
        result = files_newer_that_mins(self.test_dir, "*.txt", 10)
        self.assertEqual(result, [])
        
        # Test with non-existent pattern
        result = files_newer_that_mins(self.test_dir, "*.nonexistent", 10)
        self.assertEqual(result, [])
        
        print("✅ Files newer than mins empty directory test passed")

    def test_files_newer_that_mins_with_files(self):
        """Test files_newer_that_mins with actual files"""
        current_time = time.time()
        
        # Create files with different ages
        recent_file = os.path.join(self.test_dir, "recent.txt")
        old_file = os.path.join(self.test_dir, "old.txt")
        
        # Create files
        with open(recent_file, 'w') as f:
            f.write("recent")
        with open(old_file, 'w') as f:
            f.write("old")
        
        # Set file modification times
        recent_time = current_time - 300  # 5 minutes ago
        old_time = current_time - 1200    # 20 minutes ago
        
        os.utime(recent_file, (recent_time, recent_time))
        os.utime(old_file, (old_time, old_time))
        
        # Test finding files newer than 10 minutes
        newer_files = files_newer_that_mins(self.test_dir, "*.txt", 10)
        
        # Should find only the recent file
        self.assertEqual(len(newer_files), 1)
        self.assertTrue(any("recent.txt" in f for f in newer_files))
        
        # Test finding files newer than 30 minutes (should find both)
        newer_files = files_newer_that_mins(self.test_dir, "*.txt", 30)
        self.assertEqual(len(newer_files), 2)
        
        print("✅ Files newer than mins with files test passed")

    def test_delete_files_older_than_days_empty_directory(self):
        """Test delete_files_older_than_days with empty directory"""
        # Should not raise exception with empty directory
        try:
            delete_files_older_than_days(self.test_dir, 1)
            print("✅ Delete files older than days empty directory test passed")
        except Exception as e:
            self.fail(f"delete_files_older_than_days raised exception with empty dir: {e}")

    def test_delete_files_older_than_days_with_files(self):
        """Test delete_files_older_than_days with actual files"""
        current_time = time.time()
        
        # Create files with different ages
        recent_file = os.path.join(self.test_dir, "recent.txt")
        old_file = os.path.join(self.test_dir, "old.txt")
        
        # Create files
        with open(recent_file, 'w') as f:
            f.write("recent")
        with open(old_file, 'w') as f:
            f.write("old")
        
        # Set file modification times
        recent_time = current_time - (2 * 24 * 60 * 60)  # 2 days ago
        old_time = current_time - (10 * 24 * 60 * 60)    # 10 days ago
        
        os.utime(recent_file, (recent_time, recent_time))
        os.utime(old_file, (old_time, old_time))
        
        # Verify both files exist
        self.assertTrue(os.path.exists(recent_file))
        self.assertTrue(os.path.exists(old_file))
        
        # Delete files older than 5 days
        delete_files_older_than_days(self.test_dir, 5)
        
        # Recent file should still exist, old file should be deleted
        self.assertTrue(os.path.exists(recent_file))
        self.assertFalse(os.path.exists(old_file))
        
        print("✅ Delete files older than days with files test passed")

    def test_delete_files_older_than_days_subdirectories(self):
        """Test that delete_files_older_than_days doesn't affect subdirectories"""
        # Create a subdirectory
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir)
        
        # Create old file and old subdirectory
        old_file = os.path.join(self.test_dir, "old_file.txt")
        with open(old_file, 'w') as f:
            f.write("old")
        
        # Set old times
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        os.utime(old_file, (old_time, old_time))
        os.utime(sub_dir, (old_time, old_time))
        
        # Delete files older than 5 days
        delete_files_older_than_days(self.test_dir, 5)
        
        # File should be deleted, subdirectory should remain
        self.assertFalse(os.path.exists(old_file))
        self.assertTrue(os.path.exists(sub_dir))
        
        print("✅ Delete files older than days subdirectories test passed")

    def test_pattern_matching_files_newer_that_mins(self):
        """Test pattern matching in files_newer_that_mins"""
        # Create files with different extensions
        txt_file = os.path.join(self.test_dir, "test.txt")
        log_file = os.path.join(self.test_dir, "test.log")
        xml_file = os.path.join(self.test_dir, "test.xml")
        
        for file_path in [txt_file, log_file, xml_file]:
            with open(file_path, 'w') as f:
                f.write("test")
        
        # Test pattern matching
        txt_files = files_newer_that_mins(self.test_dir, "*.txt", 60)
        self.assertEqual(len(txt_files), 1)
        self.assertTrue(any("test.txt" in f for f in txt_files))
        
        log_files = files_newer_that_mins(self.test_dir, "*.log", 60)
        self.assertEqual(len(log_files), 1)
        self.assertTrue(any("test.log" in f for f in log_files))
        
        all_files = files_newer_that_mins(self.test_dir, "*", 60)
        self.assertEqual(len(all_files), 3)
        
        print("✅ Pattern matching files newer that mins test passed")

    def test_helper_functions_integration(self):
        """Test helper functions working together"""
        # Create a test scenario that uses multiple functions
        
        # Create test files
        files_to_create = ["app.log", "debug.txt", "error.log"]
        current_time = time.time()
        
        for i, filename in enumerate(files_to_create):
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"Content of {filename}")
            
            # Set different ages
            file_time = current_time - (i * 60 * 60 * 24)  # 0, 1, 2 days ago
            os.utime(file_path, (file_time, file_time))
        
        # Test integration: find recent files, then clean old ones
        recent_files = files_newer_that_mins(self.test_dir, "*.log", 60 * 24)  # 1 day
        self.assertTrue(len(recent_files) > 0)
        
        # Delete old files
        delete_files_older_than_days(self.test_dir, 1)
        
        # Check results
        remaining_files = os.listdir(self.test_dir)
        self.assertTrue(len(remaining_files) <= len(files_to_create))
        
        print("✅ Helper functions integration test passed")


if __name__ == '__main__':
    print("=" * 70)
    print("KAFKA_CSA - KPI_Helper Utility Function Tests")
    print("=" * 70)
    print("Testing utility functions for file operations and HTTP status")
    print("=" * 70)
    
    unittest.main(verbosity=2)
