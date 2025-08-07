package com.example.server;

import java.util.Hashtable;
import java.util.Vector;
import java.util.Enumeration;

/**
 * CalculatorTestUtil class for testing the calculator functionality.
 * Contains legacy Java patterns that can be modernized.
 */
public class TestUtil {
    
    // Using legacy Vector instead of ArrayList
    private Vector<TestCase> testCases = new Vector<>();
    
    // Using legacy Hashtable instead of HashMap
    private Hashtable<String, Double> expectedResults = new Hashtable<>();
    
    // Reference to the calculator being tested
    private Main calculator;
    
    /**
     * Inner class to represent a test case with legacy patterns
     */
    private class TestCase {
        String operation;
        double a;
        double b;
        
        public TestCase(String operation, double a, double b) {
            this.operation = operation;
            this.a = a;
            this.b = b;
        }
        
        public String toString() {
            return operation + "(" + a + ", " + b + ")";
        }
    }
    
    // Helper methods to abstract collection operations
    private void addTestCase(TestCase testCase) {
        testCases.addElement(testCase);
    }
    
    private void addExpectedResult(String key, Double value) {
        expectedResults.put(key, value);
    }
    
    private Double getExpectedResult(String key) {
        return expectedResults.get(key);
    }
    
    private Enumeration<TestCase> getTestCases() {
        return testCases.elements();
    }
    
    public TestUtil() {
        calculator = new Main();
        initializeTestCases();
    }
    
    private void initializeTestCases() {
        // Add test cases using abstracted methods
        addTestCase(new TestCase("add", 10, 5));
        addTestCase(new TestCase("subtract", 10, 5));
        addTestCase(new TestCase("multiply", 10, 5));
        addTestCase(new TestCase("divide", 10, 5));
        
        // Add expected results using abstracted methods
        addExpectedResult("add(10.0, 5.0)", 15.0);
        addExpectedResult("subtract(10.0, 5.0)", 5.0);
        addExpectedResult("multiply(10.0, 5.0)", 50.0);
        addExpectedResult("divide(10.0, 5.0)", 2.0);
    }
    
    /**
     * Run all calculator tests and verify results
     */
    public void runTests() {
        System.out.println("Running Calculator Tests...");
        
        int passed = 0;
        int failed = 0;
        
        // Using abstracted method to get Enumeration
        for (Enumeration<TestCase> e = getTestCases(); e.hasMoreElements();) {
            TestCase testCase = e.nextElement();
            boolean result = runSingleTest(testCase);
            
            if (result) {
                passed++;
            } else {
                failed++;
            }
        }
        
        // Using StringBuffer instead of StringBuilder
        StringBuffer summary = new StringBuffer();
        summary.append("\nTest Summary: ");
        summary.append(passed).append(" passed, ");
        summary.append(failed).append(" failed, ");
        summary.append(testCases.size()).append(" total");
        
        System.out.println(summary.toString());
    }
    
    /**
     * Run a single test case and verify the result
     */
    private boolean runSingleTest(TestCase testCase) {
        double result = 0;
        boolean success = false;
        
        try {
            System.out.print("Testing " + testCase + "... ");
            
            // Perform the operation based on the test case
            switch (testCase.operation) {
                case "add":
                    result = calculator.add(testCase.a, testCase.b);
                    break;
                case "subtract":
                    result = calculator.subtract(testCase.a, testCase.b);
                    break;
                case "multiply":
                    result = calculator.multiply(testCase.a, testCase.b);
                    break;
                case "divide":
                    result = calculator.divide(testCase.a, testCase.b);
                    break;
                default:
                    throw new IllegalArgumentException("Unknown operation: " + testCase.operation);
            }
            
            // Check if the result matches the expected value
            Double expected = getExpectedResult(testCase.toString());
            if (expected != null && Math.abs(expected - result) < 0.0001) {
                System.out.println("PASSED (" + result + ")");
                success = true;
            } else {
                System.out.println("FAILED (Expected: " + expected + ", Got: " + result + ")");
                success = false;
            }
            
        } catch (Exception e) {
            System.out.println("ERROR: " + e.getMessage());
            success = false;
        }
        
        return success;
    }
    
    public static void main(String[] args) {
        System.out.println("Calculator Test Utility");
        TestUtil testUtil = new TestUtil();
        testUtil.runTests();
        System.out.println("\nTest execution completed.");
    }
} 