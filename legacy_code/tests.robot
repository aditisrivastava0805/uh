*** Settings ***
Documentation     Calculator Test Suite for Java JDK Uplift Validation
Library           Process
Library           OperatingSystem
Library           String

*** Variables ***
${JAVA_CMD}       java
${COMPILE_CMD}    javac
${EPSILON}        0.0001    # For floating point comparisons

*** Test Cases ***
Test Calculator Compilation
    [Documentation]    Verify that Main.java (calculator) compiles successfully
    [Tags]             compilation
    Log To Console     Testing Calculator compilation...
    
    # Change to the source directory
    ${result} =        Run Process    ${COMPILE_CMD}    src/com/example/server/Main.java
    ...                cwd=/app/source-code
    Should Be Equal As Integers    ${result.rc}    0    Calculator compilation failed
    Log To Console     Calculator compiled successfully

Test TestUtil Compilation
    [Documentation]    Verify that TestUtil.java compiles successfully
    [Tags]             compilation
    Log To Console     Testing TestUtil compilation...
    
    # Compile TestUtil with classpath pointing to source-code directory
    ${result} =        Run Process    ${COMPILE_CMD}    -cp    src:/app/source-code/src    src/com/example/server/TestUtil.java
    ...                cwd=/app/ESSVT
    Should Be Equal As Integers    ${result.rc}    0    TestUtil compilation failed
    Log To Console     TestUtil compiled successfully

Test Calculator Basic Operations
    [Documentation]    Verify that calculator performs basic operations correctly
    [Tags]             execution
    Log To Console     Testing calculator basic operations...
    
    # Run the calculator
    ${result} =        Run Process    ${JAVA_CMD}    -cp    src    com.example.server.Main
    ...                cwd=/app/source-code
    Should Be Equal As Integers    ${result.rc}    0    Calculator execution failed
    
    # Verify outputs for basic operations
    Should Contain     ${result.stdout}    5.0 + 3.0 = 8.0
    Should Contain     ${result.stdout}    10.0 - 4.0 = 6.0
    Should Contain     ${result.stdout}    2.0 * 3.0 = 6.0
    Should Contain     ${result.stdout}    10.0 / 2.0 = 5.0
    
    Log To Console     Calculator operations verified successfully

Test TestUtil Execution
    [Documentation]    Verify that TestUtil executes and validates calculator operations
    [Tags]             execution
    Log To Console     Testing TestUtil execution...
    
    # Run the TestUtil with classpath pointing to both ESSVT and source-code directories
    ${result} =        Run Process    ${JAVA_CMD}    -cp    src:/app/source-code/src    com.example.server.TestUtil
    ...                cwd=/app/ESSVT
    Should Be Equal As Integers    ${result.rc}    0    TestUtil execution failed
    
    # Verify test results
    Should Contain     ${result.stdout}    Testing add(10.0, 5.0)... PASSED
    Should Contain     ${result.stdout}    Testing subtract(10.0, 5.0)... PASSED
    Should Contain     ${result.stdout}    Testing multiply(10.0, 5.0)... PASSED
    Should Contain     ${result.stdout}    Testing divide(10.0, 5.0)... PASSED
    Should Contain     ${result.stdout}    Test Summary: 4 passed, 0 failed, 4 total
    
    Log To Console     TestUtil execution verified successfully

Test Calculator Division By Zero
    [Documentation]    Verify that calculator handles division by zero correctly
    [Tags]             error-handling
    Log To Console     Testing division by zero handling...

    # Compile and run the pre-existing DivisionTest.java file
    ${compile} =       Run Process    ${COMPILE_CMD}    -cp    src:/app/source-code/src    src/com/example/server/DivisionTest.java
    ...                cwd=/app/ESSVT
    Should Be Equal As Integers    ${compile.rc}    0    Division test compilation failed

    ${result} =        Run Process    ${JAVA_CMD}    -cp    src:/app/source-code/src    com.example.server.DivisionTest
    ...                cwd=/app/ESSVT
    Should Be Equal As Integers    ${result.rc}    0    Division test execution failed
    Should Contain     ${result.stdout}    TEST PASSED

    Log To Console     Division by zero handling verified successfully

*** Keywords ***
Verify Calculator Result
    [Arguments]    ${output}    ${operation}    ${expected}
    ${lines} =         Get Lines Containing String    ${output}    ${operation}
    ${line} =          Get Line    ${lines}    0
    ${actual} =        Fetch From Right    ${line}    =
    ${actual} =        Strip String    ${actual}
    ${expected} =      Convert To Number    ${expected}
    ${actual} =        Convert To Number    ${actual}
    ${diff} =          Evaluate    abs(${actual} - ${expected})
    Should Be True     ${diff} < ${EPSILON}    Expected ${expected} but got ${actual}