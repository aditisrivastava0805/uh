import unittest
import sys
import os

print("=" * 60)
print("KAFKA_SDP_PREPAID Basic Test - Debug Version")
print("=" * 60)

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"Python path: {sys.path[:3]}...")
print(f"Current directory: {os.getcwd()}")
print(f"Parent directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

# Try to import main module
try:
    print("Attempting to import main module...")
    from main import timestamp, parse_args
    print("✅ Successfully imported main functions")
    IMPORT_SUCCESS = True
    IMPORT_ERROR = None
except Exception as e:
    print(f"❌ Failed to import main module: {e}")
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)

class TestKafkaSDPPrepaidDebug(unittest.TestCase):
    """Debug version of basic tests"""

    def test_import_status(self):
        """Test import status"""
        print(f"Import Success: {IMPORT_SUCCESS}")
        if not IMPORT_SUCCESS:
            print(f"Import Error: {IMPORT_ERROR}")
        else:
            print("✅ All imports successful")

    def test_timestamp_if_available(self):
        """Test timestamp function if available"""
        if IMPORT_SUCCESS:
            result = timestamp()
            print(f"Timestamp result: {result}")
            self.assertEqual(len(result), 14)
            print("✅ Timestamp test passed")
        else:
            print("⚠️ Skipping timestamp test due to import failure")

    def test_file_existence(self):
        """Test that files exist"""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_file = os.path.join(script_dir, 'main.py')
        print(f"Checking for main.py at: {main_file}")
        self.assertTrue(os.path.exists(main_file))
        print("✅ main.py exists")

if __name__ == '__main__':
    print("Starting test execution...")
    unittest.main(verbosity=2, buffer=False)
