*** Settings ***
Documentation    Resource file for air_health_check Robot Framework tests
...              
...              This resource file contains common keywords, variables, and utilities
...              used across multiple Robot Framework test suites for the air_health_check module.
...              
...              Contains:
...              - Common variables and configuration
...              - Reusable keywords for test setup and teardown
...              - Utility functions for mocking and test data generation
...              - Helper keywords for validation and verification
...              
...              Author: Test Suite Generator
...              Date: 2025-07-24
...              Version: 1.0.0

Library          RequestsLibrary
Library          OperatingSystem
Library          Process
Library          Collections
Library          String
Library          DateTime
Library          JSONLibrary
Library          BuiltIn

*** Variables ***
# Application Configuration
${AIR_HEALTH_HOST}           0.0.0.0
${AIR_HEALTH_PORT}           8080
${AIR_HEALTH_BASE_URL}       http://${AIR_HEALTH_HOST}:${AIR_HEALTH_PORT}
${AIR_HEALTH_ENDPOINT}       /air_pod/status

# File Paths and Directories
${AIR_HEALTH_MODULE_DIR}     c:\\Users\\eakaijn\\workspace\\cec-adaptation-pod\\air_health_check
${CONFIG_FILE_NAME}          AirPodConfigurationFile.json
${COMMAND_FILE_NAME}         AirPodCommandFile.json
${LOGGER_CONFIG_NAME}        logger-config.json
${APP_SCRIPT_NAME}           app.py
${COMMAND_EXECUTOR_NAME}     CommandExecutor.py

# Test Configuration
${DEFAULT_TIMEOUT}           30 seconds
${HTTP_TIMEOUT}              10
${APP_STARTUP_DELAY}         3 seconds
${CACHE_INTERVAL}            10
${DEFAULT_THRESHOLD}         50

# Mock Data for Testing
${MOCK_NAMESPACE}            test-namespace
${MOCK_HEALTHY_PODS}         4
${MOCK_TOTAL_PODS}           5
${MOCK_CLUSTER_IP}           192.168.1.100

# Test Patterns
${POD_RUNNING_PATTERN}       *Running*1/1*
${ENVOY_HEALTHY_PATTERN}     Healthy
${JSON_DATA_PATTERN}         *"data":*

# Error Messages
${CONNECTION_ERROR_MSG}      Connection refused
${JSON_ERROR_MSG}            JSONDecodeError
${TIMEOUT_ERROR_MSG}         timeout

*** Keywords ***
# =============================================================================
# Setup and Teardown Keywords
# =============================================================================

Setup Air Health Test Suite
    [Documentation]    Set up the test suite for air_health_check tests
    [Arguments]        ${custom_config}=${EMPTY}
    
    Log    Setting up Air Health test suite
    
    # Verify module directory and files exist
    Verify Air Health Module Structure
    
    # Initialize global test variables
    Set Suite Variable    ${TEST_APP_PROCESS}         ${NONE}
    Set Suite Variable    ${TEST_SESSION_ALIAS}       air_health_test
    Set Suite Variable    ${MOCK_RESPONSES}           &{EMPTY}
    
    # Load configuration if custom config provided
    IF    "${custom_config}" != "${EMPTY}"
        Load Custom Test Configuration    ${custom_config}
    ELSE
        Load Default Test Configuration
    END
    
    Log    Air Health test suite setup completed

Teardown Air Health Test Suite
    [Documentation]    Clean up after air_health_check test suite
    
    Log    Tearing down Air Health test suite
    
    # Stop any running test applications
    Stop Test Air Health Application
    
    # Clean up test files and sessions
    Cleanup Test Environment Files
    Delete All Sessions
    
    # Reset global variables
    Set Suite Variable    ${TEST_APP_PROCESS}    ${NONE}
    
    Log    Air Health test suite teardown completed

Setup Air Health Test Case
    [Documentation]    Set up before each test case
    [Arguments]        ${test_name}=${TEST NAME}
    
    Log    Setting up test case: ${test_name}
    
    # Reset mock responses for each test
    Set Test Variable    ${MOCK_RESPONSES}    &{EMPTY}
    
    # Ensure clean session state
    Delete All Sessions

Teardown Air Health Test Case
    [Documentation]    Clean up after each test case
    [Arguments]        ${test_name}=${TEST NAME}
    
    Log    Cleaning up test case: ${test_name}
    
    # Close any open sessions
    Run Keyword And Ignore Error    Delete All Sessions
    
    # Clean up test-specific files
    Run Keyword And Ignore Error    Remove File    ${AIR_HEALTH_MODULE_DIR}${/}test_*.json
    Run Keyword And Ignore Error    Remove File    ${AIR_HEALTH_MODULE_DIR}${/}test_*.py

# =============================================================================
# Verification and Validation Keywords
# =============================================================================

Verify Air Health Module Structure
    [Documentation]    Verify that the air_health_check module has correct structure
    
    # Check main directory
    Directory Should Exist    ${AIR_HEALTH_MODULE_DIR}
    
    # Check required files
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${CONFIG_FILE_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${COMMAND_FILE_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${LOGGER_CONFIG_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${APP_SCRIPT_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${COMMAND_EXECUTOR_NAME}
    
    # Check tests directory
    Directory Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}tests
    
    Log    Air Health module structure verified

Verify Configuration File Format
    [Documentation]    Verify that configuration files contain valid JSON
    [Arguments]        ${config_file}=${CONFIG_FILE_NAME}
    
    ${config_path} =       Set Variable    ${AIR_HEALTH_MODULE_DIR}${/}${config_file}
    ${config_content} =    Get File        ${config_path}
    
    # Verify JSON is valid
    ${config_json} =       Convert String To Json    ${config_content}
    
    # Verify required keys exist
    Should Contain         ${config_json}    host
    Should Contain         ${config_json}    port
    
    Log    Configuration file format verified: ${config_file}
    
    [Return]               ${config_json}

Verify Command File Format
    [Documentation]    Verify that command file contains valid JSON with required commands
    [Arguments]        ${command_file}=${COMMAND_FILE_NAME}
    
    ${command_path} =      Set Variable    ${AIR_HEALTH_MODULE_DIR}${/}${command_file}
    ${command_content} =   Get File        ${command_path}
    
    # Verify JSON is valid
    ${command_json} =      Convert String To Json    ${command_content}
    
    # Verify required command sections
    Should Contain         ${command_json}    check_healthy_pod
    Should Contain         ${command_json}    cluster_ip
    Should Contain         ${command_json}    air_pod_max_count
    Should Contain         ${command_json}    envoy_pod_check
    Should Contain         ${command_json}    air_pod_threshold
    
    # Verify threshold is valid
    Should Be True         isinstance(${command_json['air_pod_threshold']}, int)
    Should Be True         0 <= ${command_json['air_pod_threshold']} <= 100
    
    Log    Command file format verified: ${command_file}
    
    [Return]               ${command_json}

Verify HTTP Response Structure
    [Documentation]    Verify that HTTP response has expected structure
    [Arguments]        ${response}
    
    # Check basic response properties
    Should Be True         hasattr(${response}, 'status_code')
    Should Be True         hasattr(${response}, 'text')
    
    # If successful response, verify JSON structure
    IF    ${response.status_code} == 200
        ${json_response} =    Convert String To Json    ${response.text}
        Should Contain        ${json_response}          data
        Log    HTTP response structure verified (success)
    ELSE
        Log    HTTP response structure verified (error status: ${response.status_code})
    END

# =============================================================================
# Mock and Test Data Generation Keywords
# =============================================================================

Create Mock Configuration
    [Documentation]    Create a mock configuration for testing
    [Arguments]        ${host}=${AIR_HEALTH_HOST}    ${port}=${AIR_HEALTH_PORT}    ${test_mode}=${FALSE}
    
    &{mock_config} =       Create Dictionary
    ...                    host=${host}
    ...                    port=${port}
    ...                    schedule_time=15
    ...                    req_url=http://localhost:8080/hello/
    ...                    is_unhealthy_test_mode=${test_mode}
    
    Log    Created mock configuration: ${mock_config}
    
    [Return]               &{mock_config}

Create Mock Commands
    [Documentation]    Create mock commands for testing
    [Arguments]        ${namespace}=${MOCK_NAMESPACE}    ${threshold}=${DEFAULT_THRESHOLD}
    
    &{mock_commands} =     Create Dictionary
    ...                    air_pod_threshold=${threshold}
    
    &{check_healthy_pod} = Create Dictionary
    ...                    command=kubectl get pods -n ${namespace} | egrep cair | grep -v gui | grep Running | grep '1/1'
    
    &{cluster_ip} =        Create Dictionary
    ...                    command=kubectl get httpproxy -n ${namespace} | grep cair | awk -F' ' '{print $2}'
    
    &{air_pod_max_count} = Create Dictionary
    ...                    command=kubectl get pods -n ${namespace} | egrep cair | grep -v gui
    
    &{envoy_pod_check} =   Create Dictionary
    ...                    command=kubectl get pod -n ${namespace} | grep envoy | grep trf | grep -q '1/1' && echo Healthy || echo Unhealthy
    
    Set To Dictionary      ${mock_commands}    check_healthy_pod=${check_healthy_pod}
    Set To Dictionary      ${mock_commands}    cluster_ip=${cluster_ip}
    Set To Dictionary      ${mock_commands}    air_pod_max_count=${air_pod_max_count}
    Set To Dictionary      ${mock_commands}    envoy_pod_check=${envoy_pod_check}
    
    Log    Created mock commands for namespace: ${namespace}
    
    [Return]               &{mock_commands}

Generate Mock Pod Data
    [Documentation]    Generate mock pod data for testing
    [Arguments]        ${healthy_count}=${MOCK_HEALTHY_PODS}    ${total_count}=${MOCK_TOTAL_PODS}
    
    @{healthy_pods} =      Create List
    @{unhealthy_pods} =    Create List
    
    # Generate healthy pods
    FOR    ${i}    IN RANGE    ${healthy_count}
        ${pod_name} =      Set Variable    cair-pod-${i}
        ${pod_status} =    Set Variable    ${pod_name} Running 1/1
        Append To List     ${healthy_pods}    ${pod_status}
    END
    
    # Generate unhealthy pods if total > healthy
    ${unhealthy_count} =   Evaluate    ${total_count} - ${healthy_count}
    FOR    ${i}    IN RANGE    ${unhealthy_count}
        ${pod_index} =     Evaluate    ${healthy_count} + ${i}
        ${pod_name} =      Set Variable    cair-pod-${pod_index}
        ${pod_status} =    Set Variable    ${pod_name} CrashLoopBackOff 0/1
        Append To List     ${unhealthy_pods}    ${pod_status}
    END
    
    # Combine all pods
    @{all_pods} =          Combine Lists    ${healthy_pods}    ${unhealthy_pods}
    
    &{pod_data} =          Create Dictionary
    ...                    healthy_pods=${healthy_pods}
    ...                    unhealthy_pods=${unhealthy_pods}
    ...                    all_pods=${all_pods}
    ...                    healthy_count=${healthy_count}
    ...                    total_count=${total_count}
    
    Log    Generated mock pod data: ${healthy_count}/${total_count} healthy
    
    [Return]               &{pod_data}

Create Mock Subprocess Response
    [Documentation]    Create a mock response for subprocess commands
    [Arguments]        ${stdout}=success    ${stderr}=${EMPTY}    ${returncode}=0
    
    &{mock_response} =     Create Dictionary
    ...                    stdout=${stdout}
    ...                    stderr=${stderr}
    ...                    returncode=${returncode}
    
    Log    Created mock subprocess response: rc=${returncode}
    
    [Return]               &{mock_response}

# =============================================================================
# Application Management Keywords
# =============================================================================

Start Test Air Health Application
    [Documentation]    Start the air_health_check application for testing
    [Arguments]        ${use_mocks}=${TRUE}    ${config_override}=&{EMPTY}
    
    Log    Starting test Air Health application
    
    # Stop any existing application
    Stop Test Air Health Application
    
    # Create test runner script with mocks
    ${test_script} =       Generate Application Test Script    ${use_mocks}    ${config_override}
    Create File            ${AIR_HEALTH_MODULE_DIR}${/}test_runner.py    ${test_script}
    
    # Start application process
    ${process} =           Start Process    python    test_runner.py
    ...                    cwd=${AIR_HEALTH_MODULE_DIR}    shell=True    alias=air_health_app
    
    Set Suite Variable     ${TEST_APP_PROCESS}    ${process}
    
    # Wait for application to start
    Sleep                  ${APP_STARTUP_DELAY}
    
    Log    Test Air Health application started with PID: ${process.pid}

Stop Test Air Health Application
    [Documentation]    Stop the air_health_check test application
    
    IF    ${TEST_APP_PROCESS} is not None
        Log    Stopping test Air Health application
        
        TRY
            Terminate Process    ${TEST_APP_PROCESS}
            Wait For Process     ${TEST_APP_PROCESS}    timeout=5s
        EXCEPT
            Log    Force terminating application
            TRY
                Kill Process    ${TEST_APP_PROCESS}
            EXCEPT
                Log    Could not terminate application process
            END
        END
        
        Set Suite Variable    ${TEST_APP_PROCESS}    ${NONE}
    END
    
    # Clean up test runner script
    Run Keyword And Ignore Error    Remove File    ${AIR_HEALTH_MODULE_DIR}${/}test_runner.py

Generate Application Test Script
    [Documentation]    Generate a Python script to run the application with mocks
    [Arguments]        ${use_mocks}=${TRUE}    ${config_override}=&{EMPTY}
    
    ${mock_setup} =    Set Variable If    ${use_mocks}
    ...    # Mock external dependencies
    ...    import lib.Namespace
    ...    lib.Namespace.get_application_namespace = lambda: '${MOCK_NAMESPACE}'
    ...    
    ...    # Mock subprocess commands
    ...    import subprocess
    ...    original_run = subprocess.run
    ...    
    ...    def mock_run(*args, **kwargs):
    ...        cmd_str = str(args[0]) if args else ''
    ...        if 'kubectl get pods' in cmd_str and 'grep Running' in cmd_str:
    ...            class MockResult:
    ...                stdout = 'cair-pod-1 Running 1/1\\ncair-pod-2 Running 1/1'
    ...                stderr = ''
    ...                returncode = 0
    ...            return MockResult()
    ...        elif 'kubectl get pods' in cmd_str:
    ...            class MockResult:
    ...                stdout = 'cair-pod-1 Running 1/1\\ncair-pod-2 Running 1/1\\ncair-pod-3 CrashLoopBackOff 0/1'
    ...                stderr = ''
    ...                returncode = 0
    ...            return MockResult()
    ...        elif 'kubectl get httpproxy' in cmd_str:
    ...            class MockResult:
    ...                stdout = '${MOCK_CLUSTER_IP}'
    ...                stderr = ''
    ...                returncode = 0
    ...            return MockResult()
    ...        elif 'envoy' in cmd_str:
    ...            class MockResult:
    ...                stdout = 'Healthy'
    ...                stderr = ''
    ...                returncode = 0
    ...            return MockResult()
    ...        return original_run(*args, **kwargs)
    ...    
    ...    subprocess.run = mock_run
    ...    ${EMPTY}
    
    ${config_setup} =  Set Variable If    ${config_override}
    ...    # Override configuration
    ...    import json
    ...    config_override = ${config_override}
    ...    with open('${CONFIG_FILE_NAME}', 'r') as f:
    ...        original_config = json.load(f)
    ...    original_config.update(config_override)
    ...    with open('${CONFIG_FILE_NAME}', 'w') as f:
    ...        json.dump(original_config, f)
    ...    ${EMPTY}
    
    ${script} =        Catenate    SEPARATOR=\n
    ...    import sys
    ...    import os
    ...    
    ...    # Add paths
    ...    sys.path.append('.')
    ...    sys.path.append('..')
    ...    
    ...    ${mock_setup}
    ...    
    ...    ${config_setup}
    ...    
    ...    # Import and run the application
    ...    try:
    ...        from app import app, read_json_file
    ...        config = read_json_file('${CONFIG_FILE_NAME}')
    ...        app.run(host=config['host'], port=config['port'], debug=False, use_reloader=False)
    ...    except Exception as e:
    ...        print(f'Application error: {e}')
    ...        import traceback
    ...        traceback.print_exc()
    
    [Return]           ${script}

# =============================================================================
# HTTP Testing Keywords
# =============================================================================

Make Air Health Request
    [Documentation]    Make HTTP request to air_health_check endpoint
    [Arguments]        ${endpoint}=${AIR_HEALTH_ENDPOINT}    ${expected_status}=any    ${timeout}=${HTTP_TIMEOUT}
    
    # Create session if not exists
    ${session_exists} =    Run Keyword And Return Status    Get Request    ${TEST_SESSION_ALIAS}    /
    IF    not ${session_exists}
        Create Session    ${TEST_SESSION_ALIAS}    ${AIR_HEALTH_BASE_URL}    timeout=${timeout}
    END
    
    # Make request
    ${response} =          GET On Session    ${TEST_SESSION_ALIAS}    ${endpoint}    expected_status=${expected_status}
    
    Log    Made request to ${endpoint}, status: ${response.status_code}
    
    [Return]               ${response}

Verify Air Health Response Success
    [Documentation]    Verify that air health response indicates success
    [Arguments]        ${response}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    ${json_response} =     Convert String To Json    ${response.text}
    Should Contain         ${json_response}          data
    
    Log    Air health response verified as successful

Verify Air Health Response Error
    [Documentation]    Verify that air health response indicates error appropriately
    [Arguments]        ${response}    ${expected_error_status}=500
    
    Should Be Equal As Integers    ${response.status_code}    ${expected_error_status}
    
    Log    Air health response verified as error (status: ${response.status_code})

# =============================================================================
# Utility Keywords
# =============================================================================

Load Default Test Configuration
    [Documentation]    Load default test configuration
    
    ${config} =            Verify Configuration File Format
    ${commands} =          Verify Command File Format
    
    Set Suite Variable     ${TEST_CONFIG}     ${config}
    Set Suite Variable     ${TEST_COMMANDS}   ${commands}
    
    Log    Default test configuration loaded

Load Custom Test Configuration
    [Documentation]    Load custom test configuration
    [Arguments]        ${custom_config_path}
    
    ${config_content} =    Get File              ${custom_config_path}
    ${config} =            Convert String To Json    ${config_content}
    
    Set Suite Variable     ${TEST_CONFIG}    ${config}
    
    Log    Custom test configuration loaded from: ${custom_config_path}

Cleanup Test Environment Files
    [Documentation]    Clean up temporary files created during testing
    
    @{temp_files} =        Create List
    ...                    test_runner.py
    ...                    test_config.json
    ...                    test_commands.json
    ...                    mock_*.json
    ...                    *.log
    
    FOR    ${file_pattern}    IN    @{temp_files}
        ${files} =         Run Keyword And Ignore Error    List Files In Directory    ${AIR_HEALTH_MODULE_DIR}    ${file_pattern}
        IF    '${files[0]}' == 'PASS'
            FOR    ${file}    IN    @{files[1]}
                Run Keyword And Ignore Error    Remove File    ${AIR_HEALTH_MODULE_DIR}${/}${file}
            END
        END
    END
    
    Log    Test environment files cleaned up

Calculate Health Percentage
    [Documentation]    Calculate health percentage from healthy and total counts
    [Arguments]        ${healthy_count}    ${total_count}
    
    IF    ${total_count} == 0
        ${percentage} =    Set Variable    0
    ELSE
        ${percentage} =    Evaluate    (${healthy_count} / ${total_count}) * 100
    END
    
    Log    Health percentage: ${healthy_count}/${total_count} = ${percentage}%
    
    [Return]               ${percentage}

Wait For Application Ready
    [Documentation]    Wait for application to be ready to accept requests
    [Arguments]        ${max_wait_time}=30s    ${check_interval}=1s
    
    Log    Waiting for application to be ready
    
    ${end_time} =          Add Time To Date    ${EMPTY}    ${max_wait_time}
    
    WHILE    True
        ${current_time} =  Get Current Date
        IF    '${current_time}' > '${end_time}'
            Fail    Application did not become ready within ${max_wait_time}
        END
        
        TRY
            Create Session    ready_check    ${AIR_HEALTH_BASE_URL}    timeout=2
            ${response} =     GET On Session    ready_check    ${AIR_HEALTH_ENDPOINT}    expected_status=any
            Delete All Sessions
            
            # If we get any response, application is ready
            IF    ${response.status_code} in [200, 500, 503]
                Log    Application is ready (status: ${response.status_code})
                BREAK
            END
        EXCEPT
            Log    Application not ready yet, waiting...
            Sleep    ${check_interval}
        END
    END

Log Test Results Summary
    [Documentation]    Log a summary of test results
    [Arguments]        ${test_name}    ${status}    ${details}=${EMPTY}
    
    ${timestamp} =         Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    
    Log    ========================================
    Log    Test: ${test_name}
    Log    Status: ${status}
    Log    Time: ${timestamp}
    IF    "${details}" != "${EMPTY}"
        Log    Details: ${details}
    END
    Log    ========================================
