import unittest
import sys
import os
from unittest.mock import patch
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSafeFunctions(unittest.TestCase):
    """Test only the functions that don't depend on global logger or complex dependencies"""

    def test_timestamp_function(self):
        """Test timestamp function"""
        from main import timestamp
        result = timestamp()
        
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 14)
        self.assertTrue(result.isdigit())
        
        # Verify it's a valid datetime format
        datetime.strptime(result, "%Y%m%d%H%M%S")
        
        print("✅ Timestamp function test passed")

    @patch('sys.argv', ['main.py', 'config.json'])
    def test_parse_args_basic(self):
        """Test parse_args basic functionality"""
        from main import parse_args
        config_path, wait, test_mode = parse_args()
        
        self.assertEqual(config_path, 'config.json')
        self.assertFalse(wait)
        self.assertFalse(test_mode)
        
        print("✅ Parse args basic test passed")

    @patch('sys.argv', ['main.py', 'config.json', '--wait', '--test'])
    def test_parse_args_with_flags(self):
        """Test parse_args with flags"""
        from main import parse_args
        config_path, wait, test_mode = parse_args()
        
        self.assertEqual(config_path, 'config.json')
        self.assertTrue(wait)
        self.assertTrue(test_mode)
        
        print("✅ Parse args with flags test passed")

    @patch('os.makedirs')
    @patch('os.path.isdir', return_value=False)
    def test_make_dir_function(self, mock_isdir, mock_makedirs):
        """Test make_dir function"""
        from main import make_dir
        test_path = "/test/directory"
        
        make_dir(test_path)
        
        mock_isdir.assert_called_once_with(test_path)
        mock_makedirs.assert_called_once_with(test_path, exist_ok=True)
        
        print("✅ Make directory function test passed")

    def test_eval_value_simple(self):
        """Test eval_value with simple string (no command)"""
        from main import eval_value
        result = eval_value("simple_string")
        
        self.assertEqual(result, "simple_string")
        
        print("✅ Eval value simple test passed")

    def test_module_imports_successfully(self):
        """Test that the main module can be imported"""
        import main
        
        # Check for key functions
        self.assertTrue(hasattr(main, 'timestamp'))
        self.assertTrue(hasattr(main, 'parse_args'))
        self.assertTrue(hasattr(main, 'make_dir'))
        self.assertTrue(hasattr(main, 'eval_value'))
        
        print("✅ Module imports successfully")

    def test_file_structure_exists(self):
        """Test basic file structure"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check main.py exists
        main_file = os.path.join(script_dir, 'main.py')
        self.assertTrue(os.path.exists(main_file))
        
        # Check config directory exists
        config_dir = os.path.join(script_dir, 'config')
        self.assertTrue(os.path.exists(config_dir))
        
        print("✅ File structure exists test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("KAFKA_SDP_PREPAID - Safe Function Tests")
    print("=" * 60)
    print("Testing only functions that don't require complex mocking")
    print("=" * 60)
    unittest.main(verbosity=2)
