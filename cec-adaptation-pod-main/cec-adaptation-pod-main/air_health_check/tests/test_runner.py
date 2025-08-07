import unittest
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_app import TestApp
from tests.test_command_executor import TestCommandExecutor
from tests.test_namespace import TestNamespace
from tests.test_integration import TestAirHealthCheckIntegration


def create_test_suite():
    """Create a test suite containing all test cases"""
    test_suite = unittest.TestSuite()
    
    # Add test cases from TestApp
    test_suite.addTest(unittest.makeSuite(TestApp))
    
    # Add test cases from TestCommandExecutor
    test_suite.addTest(unittest.makeSuite(TestCommandExecutor))
    
    # Add test cases from TestNamespace  
    test_suite.addTest(unittest.makeSuite(TestNamespace))
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestAirHealthCheckIntegration))
    
    return test_suite


def run_tests():
    """Run all tests and generate a report"""
    # Create test suite
    suite = create_test_suite()
    
    # Create test runner with verbosity
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result


if __name__ == '__main__':
    run_tests()
