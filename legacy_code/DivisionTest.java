package com.example.server;

public class DivisionTest {
    public static void main(String[] args) {
        Main calculator = new Main();
        try {
            calculator.divide(10, 0);
            System.out.println("TEST FAILED: Division by zero did not throw exception");
        } catch (ArithmeticException e) {
            System.out.println("TEST PASSED: Division by zero correctly threw exception: " + e.getMessage());
        }
    }
}
