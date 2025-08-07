import unittest
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_basic import TestAirHealthCheckBasic


def create_basic_test_suite():
    """Create a basic test suite with working test cases"""
    test_suite = unittest.TestSuite()
    
    # Add basic test cases
    test_suite.addTest(unittest.makeSuite(TestAirHealthCheckBasic))
    
    return test_suite


def run_basic_tests():
    """Run basic tests and generate a report"""
    print("="*60)
    print("Running Basic Air Health Check Tests")
    print("="*60)
    
    # Create test suite
    suite = create_basic_test_suite()
    
    # Create test runner with verbosity
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("BASIC TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    return result


if __name__ == '__main__':
    run_basic_tests()
