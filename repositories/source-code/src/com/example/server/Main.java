package com.example.server;

import java.util.Date;
import java.util.Stack;
import java.util.Vector;

/**
 * SimpleCalculator class demonstrating a basic calculator with legacy Java patterns.
 * This class will be uplifted from older Java patterns to newer ones.
 */
public class Main {
    
    // Using legacy Date class for operation timestamps
    private Date startTime;
    
    // Using Stack for operation history (could use Deque in modern Java)
    // We'll define methods that use Stack-specific API to avoid breaking changes during uplift
    private Stack<String> operationHistory = new Stack<>();
    
    // Using Vector instead of ArrayList (legacy collection)
    private Vector<Double> resultHistory = new Vector<>();
    
    public Main() {
        this.startTime = new Date();
        logOperation("Calculator initialized");
    }
    
    // Add this method to abstract Stack operations
    private void addToHistory(String operation) {
        operationHistory.push(operation);
    }
    
    // Add this method to abstract Stack operations
    private String getLastOperation() {
        if (!operationHistory.isEmpty()) {
            return operationHistory.peek();
        }
        return null;
    }
    
    private void logOperation(String operation) {
        addToHistory(operation + " at " + new Date());
    }
    
    /**
     * Add two numbers and log the operation
     */
    public double add(double a, double b) {
        double result = a + b;
        // Using StringBuffer instead of StringBuilder (legacy, thread-safe but slower)
        StringBuffer sb = new StringBuffer();
        sb.append(a).append(" + ").append(b).append(" = ").append(result);
        
        logOperation(sb.toString());
        resultHistory.addElement(result); // Using legacy addElement method
        return result;
    }
    
    /**
     * Subtract two numbers and log the operation
     */
    public double subtract(double a, double b) {
        double result = a - b;
        // Using StringBuffer instead of StringBuilder
        StringBuffer sb = new StringBuffer();
        sb.append(a).append(" - ").append(b).append(" = ").append(result);
        
        logOperation(sb.toString());
        resultHistory.addElement(result);
        return result;
    }
    
    /**
     * Multiply two numbers and log the operation
     */
    public double multiply(double a, double b) {
        double result = a * b;
        // Using StringBuffer instead of StringBuilder
        StringBuffer sb = new StringBuffer();
        sb.append(a).append(" * ").append(b).append(" = ").append(result);
        
        logOperation(sb.toString());
        resultHistory.addElement(result);
        return result;
    }
    
    /**
     * Divide two numbers and log the operation
     */
    public double divide(double a, double b) {
        if (b == 0) {
            logOperation("Error: Division by zero attempted");
            throw new ArithmeticException("Cannot divide by zero");
        }
        
        double result = a / b;
        // Using StringBuffer instead of StringBuilder
        StringBuffer sb = new StringBuffer();
        sb.append(a).append(" / ").append(b).append(" = ").append(result);
        
        logOperation(sb.toString());
        resultHistory.addElement(result);
        return result;
    }
    
    /**
     * Print calculator history and statistics
     */
    public void printHistory() {
        System.out.println("\nCalculator History:");
        System.out.println("Started at: " + startTime);
        System.out.println("Operations performed: " + operationHistory.size());
        
        // Using old-style for loop instead of enhanced for loop or streams
        System.out.println("\nOperation log:");
        for (int i = operationHistory.size() - 1; i >= 0; i--) {
            System.out.println("  " + operationHistory.elementAt(i));
        }
        
        // Calculate average using legacy patterns
        double sum = 0;
        for (int i = 0; i < resultHistory.size(); i++) {
            sum += resultHistory.elementAt(i);
        }
        
        double average = resultHistory.isEmpty() ? 0 : sum / resultHistory.size();
        System.out.println("\nAverage result: " + average);
    }
    
    public static void main(String[] args) {
        System.out.println("Simple Calculator App (Legacy Java Implementation)");
        
        Main calculator = new Main();
        
        // Perform some sample calculations
        calculator.add(5, 3);
        calculator.subtract(10, 4);
        calculator.multiply(2, 3);
        calculator.divide(10, 2);
        
        // Try a calculation that will use the previous result
        try {
            double lastResult = calculator.resultHistory.lastElement();
            calculator.multiply(lastResult, 2);
        } catch (Exception e) {
            System.out.println("Error: " + e.getMessage());
        }
        
        // Print the history
        calculator.printHistory();
        
        System.out.println("\nCalculator execution completed.");
    }
} 