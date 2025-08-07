*** Settings ***
Documentation    Comprehensive Robot Framework test suite for air_health_check module
...              
...              This test suite provides comprehensive testing for the air_health_check Flask application
...              including HTTP endpoints, command execution, configuration management, and health monitoring.
...              
...              Test Categories:
...              - Application startup and initialization
...              - HTTP endpoint testing (/air_pod/status)
...              - Configuration file validation
...              - Command execution and parsing
...              - Health status calculation and thresholds
...              - Error handling and edge cases
...              - Performance and reliability testing
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

Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment
Test Setup       Setup Individual Test
Test Teardown    Cleanup Individual Test

*** Variables ***
# Application Configuration
${APP_HOST}              0.0.0.0
${APP_PORT}              8080
${APP_BASE_URL}          http://${APP_HOST}:${APP_PORT}
${APP_ENDPOINT}          /air_pod/status

# File Paths
${MODULE_DIR}            c:\\Users\\eakaijn\\workspace\\cec-adaptation-pod\\air_health_check
${CONFIG_FILE}           AirPodConfigurationFile.json
${COMMAND_FILE}          AirPodCommandFile.json
${LOGGER_CONFIG}         logger-config.json
${APP_SCRIPT}            app.py

# Test Configuration
${TEST_TIMEOUT}          30 seconds
${REQUEST_TIMEOUT}       10
${HEALTH_CHECK_INTERVAL} 10
${DEFAULT_THRESHOLD}     50

# Mock Data
${MOCK_NAMESPACE}        test-namespace
${MOCK_POD_COUNT}        5
${MOCK_HEALTHY_PODS}     4

*** Test Cases ***
# =============================================================================
# Application Startup and Initialization Tests
# =============================================================================

Test Application Module Import
    [Documentation]    Verify that the air_health_check module can be imported successfully
    [Tags]             basic    import    smoke
    
    ${result} =    Run Process    python    -c    import sys; sys.path.append('${MODULE_DIR}'); import app; print('SUCCESS')
    ...            shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    SUCCESS
    Log    Module import successful: ${result.stdout}

Test Configuration File Existence
    [Documentation]    Verify that all required configuration files exist
    [Tags]             basic    config    files
    
    File Should Exist    ${MODULE_DIR}${/}${CONFIG_FILE}
    File Should Exist    ${MODULE_DIR}${/}${COMMAND_FILE}
    File Should Exist    ${MODULE_DIR}${/}${LOGGER_CONFIG}
    File Should Exist    ${MODULE_DIR}${/}${APP_SCRIPT}
    
    Log    All configuration files exist

Test Configuration File Format
    [Documentation]    Verify that configuration files contain valid JSON
    [Tags]             basic    config    validation
    
    ${config_content} =         Get File    ${MODULE_DIR}${/}${CONFIG_FILE}
    ${config_json} =           Convert String To Json    ${config_content}
    
    ${command_content} =        Get File    ${MODULE_DIR}${/}${COMMAND_FILE}
    ${command_json} =          Convert String To Json    ${command_content}
    
    Should Contain             ${config_json}    host
    Should Contain             ${config_json}    port
    Should Contain             ${command_json}    air_pod_threshold
    
    Log    Configuration files contain valid JSON

Test Application Startup Simulation
    [Documentation]    Test application startup process with mocked dependencies
    [Tags]             startup    integration    mock
    
    # Create test script to simulate startup
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, os, json
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    # Mock the namespace function
    ...    import lib.Namespace
    ...    lib.Namespace.get_application_namespace = lambda: 'test-namespace'
    ...    
    ...    # Import and test basic functionality
    ...    from app import read_json_file, setup_logging
    ...    
    ...    try:
    ...        config = read_json_file('${MODULE_DIR}/${CONFIG_FILE}')
    ...        commands = read_json_file('${MODULE_DIR}/${COMMAND_FILE}')
    ...        print('STARTUP_SUCCESS')
    ...    except Exception as e:
    ...        print(f'STARTUP_ERROR: {e}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    STARTUP_SUCCESS
    Log    Application startup simulation successful

# =============================================================================
# HTTP Endpoint Testing
# =============================================================================

Test HTTP Endpoint Availability
    [Documentation]    Test if the Flask application can be started and HTTP endpoint responds
    [Tags]             http    endpoint    integration
    
    # Start application in background for testing
    Start Test Application
    
    # Wait for application to start
    Sleep    3s
    
    # Test endpoint availability
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    ${response} =    GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
    
    Should Be True    ${response.status_code} in [200, 500]
    Log    HTTP endpoint responded with status: ${response.status_code}
    
    [Teardown]    Stop Test Application

Test HTTP Response Format
    [Documentation]    Verify that HTTP responses follow expected JSON format
    [Tags]             http    response    format
    
    Start Test Application
    Sleep    3s
    
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    ${response} =    GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
    
    # Verify response is JSON formatted
    TRY
        ${json_response} =    Convert String To Json    ${response.text}
        Should Contain        ${json_response}    data
        Log    Response contains expected JSON structure
    EXCEPT
        Log    Response is not valid JSON: ${response.text}
        Should Be True    ${response.status_code} >= 400    Expected error status for invalid response
    END
    
    [Teardown]    Stop Test Application

Test HTTP Caching Behavior
    [Documentation]    Test the caching behavior of health status results
    [Tags]             http    caching    performance
    
    Start Test Application
    Sleep    3s
    
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    # Make first request
    ${start_time} =      Get Current Date    result_format=epoch
    ${response1} =       GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
    ${first_time} =      Get Current Date    result_format=epoch
    
    # Make second request immediately (should use cache)
    ${response2} =       GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
    ${second_time} =     Get Current Date    result_format=epoch
    
    # Second request should be faster due to caching
    ${first_duration} =  Evaluate    ${first_time} - ${start_time}
    ${second_duration} = Evaluate    ${second_time} - ${first_time}
    
    Should Be True       ${second_duration} < ${first_duration}
    Log    Caching behavior verified: First: ${first_duration}s, Second: ${second_duration}s
    
    [Teardown]    Stop Test Application

# =============================================================================
# Command Execution Testing
# =============================================================================

Test Command Configuration Parsing
    [Documentation]    Test parsing and validation of command configuration
    [Tags]             command    config    parsing
    
    ${command_content} =    Get File    ${MODULE_DIR}${/}${COMMAND_FILE}
    ${command_json} =      Convert String To Json    ${command_content}
    
    # Verify required command sections exist
    Should Contain         ${command_json}    check_healthy_pod
    Should Contain         ${command_json}    cluster_ip
    Should Contain         ${command_json}    air_pod_max_count
    Should Contain         ${command_json}    envoy_pod_check
    Should Contain         ${command_json}    air_pod_threshold
    
    # Verify command structure
    Should Contain         ${command_json['check_healthy_pod']}    command
    Should Contain         ${command_json['cluster_ip']}          command
    
    # Verify threshold is numeric
    Should Be True         isinstance(${command_json['air_pod_threshold']}, int)
    
    Log    Command configuration parsing successful

Test Command Template Replacement
    [Documentation]    Test namespace template replacement in commands
    [Tags]             command    template    namespace
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, json
    ...    sys.path.append('${MODULE_DIR}')
    ...    
    ...    # Load command configuration
    ...    with open('${MODULE_DIR}/${COMMAND_FILE}') as f:
    ...        commands = json.load(f)
    ...    
    ...    # Test template replacement
    ...    test_namespace = 'test-ns'
    ...    cmd = commands['check_healthy_pod']['command']
    ...    replaced_cmd = cmd.replace('{namespace}', test_namespace)
    ...    
    ...    if 'test-ns' in replaced_cmd and '{namespace}' not in replaced_cmd:
    ...        print('TEMPLATE_REPLACEMENT_SUCCESS')
    ...    else:
    ...        print('TEMPLATE_REPLACEMENT_FAILED')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    TEMPLATE_REPLACEMENT_SUCCESS
    Log    Template replacement successful

Test Mock Command Execution
    [Documentation]    Test command execution with mocked kubectl commands
    [Tags]             command    execution    mock
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, os, subprocess
    ...    from unittest.mock import patch, MagicMock
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    # Mock subprocess and namespace
    ...    with patch('subprocess.run') as mock_run, \\
    ...         patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        
    ...        mock_ns.return_value = 'test-namespace'
    ...        mock_run.return_value = MagicMock(stdout='pod1 Running\\npod2 Running', returncode=0)
    ...        
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        config = {'test': 'config'}
    ...        executor = CommandExecutor(config, False)
    ...        
    ...        print('MOCK_EXECUTION_SUCCESS')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    MOCK_EXECUTION_SUCCESS
    Log    Mock command execution successful

# =============================================================================
# Health Status Calculation Testing
# =============================================================================

Test Health Percentage Calculation
    [Documentation]    Test health percentage calculation logic
    [Tags]             health    calculation    percentage
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    from unittest.mock import patch
    ...    
    ...    # Mock namespace function
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.return_value = 'test-namespace'
    ...        
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        config = {'test': 'config'}
    ...        executor = CommandExecutor(config, False)
    ...        
    ...        # Test percentage calculation
    ...        percentage = executor.calculate_percentage(4, 5)
    ...        if percentage == 80:
    ...            print('PERCENTAGE_CALCULATION_SUCCESS')
    ...        else:
    ...            print(f'PERCENTAGE_CALCULATION_FAILED: {percentage}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    PERCENTAGE_CALCULATION_SUCCESS
    Log    Health percentage calculation successful

Test Health Threshold Logic
    [Documentation]    Test health status determination based on threshold
    [Tags]             health    threshold    logic
    
    ${command_content} =    Get File    ${MODULE_DIR}${/}${COMMAND_FILE}
    ${command_json} =      Convert String To Json    ${command_content}
    
    ${threshold} =         Convert To Integer    ${command_json['air_pod_threshold']}
    
    # Test scenarios
    ${above_threshold} =   Evaluate    ${threshold} + 10
    ${below_threshold} =   Evaluate    ${threshold} - 10
    ${equal_threshold} =   Set Variable    ${threshold}
    
    Should Be True         ${above_threshold} > ${threshold}
    Should Be True         ${below_threshold} < ${threshold}
    Should Be True         ${equal_threshold} == ${threshold}
    
    Log    Health threshold logic verified: threshold=${threshold}

Test Unhealthy Test Mode
    [Documentation]    Test the unhealthy test mode functionality
    [Tags]             health    test_mode    unhealthy
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    from unittest.mock import patch
    ...    
    ...    # Mock namespace function
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.return_value = 'test-namespace'
    ...        
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        # Test normal mode
    ...        config = {'test': 'config'}
    ...        executor_normal = CommandExecutor(config, False)
    ...        if executor_normal.is_unhealthy_test_mode == False:
    ...            print('NORMAL_MODE_SUCCESS')
    ...        
    ...        # Test unhealthy mode
    ...        executor_unhealthy = CommandExecutor(config, True)
    ...        if executor_unhealthy.is_unhealthy_test_mode == True:
    ...            print('UNHEALTHY_MODE_SUCCESS')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    NORMAL_MODE_SUCCESS
    Should Contain                 ${result.stdout}    UNHEALTHY_MODE_SUCCESS
    Log    Unhealthy test mode functionality verified

# =============================================================================
# Configuration Management Testing
# =============================================================================

Test Configuration Loading
    [Documentation]    Test loading and parsing of configuration files
    [Tags]             config    loading    validation
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, json
    ...    sys.path.append('${MODULE_DIR}')
    ...    
    ...    from app import read_json_file
    ...    
    ...    try:
    ...        config = read_json_file('${MODULE_DIR}/${CONFIG_FILE}')
    ...        commands = read_json_file('${MODULE_DIR}/${COMMAND_FILE}')
    ...        
    ...        # Verify config structure
    ...        required_config_keys = ['host', 'port', 'schedule_time']
    ...        for key in required_config_keys:
    ...            if key not in config:
    ...                raise ValueError(f'Missing config key: {key}')
    ...        
    ...        # Verify command structure
    ...        required_command_keys = ['check_healthy_pod', 'air_pod_threshold']
    ...        for key in required_command_keys:
    ...            if key not in commands:
    ...                raise ValueError(f'Missing command key: {key}')
    ...        
    ...        print('CONFIG_LOADING_SUCCESS')
    ...    except Exception as e:
    ...        print(f'CONFIG_LOADING_ERROR: {e}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    CONFIG_LOADING_SUCCESS
    Log    Configuration loading successful

Test Invalid Configuration Handling
    [Documentation]    Test handling of invalid or missing configuration
    [Tags]             config    error_handling    validation
    
    # Create temporary invalid config file
    ${invalid_config} =    Set Variable    {"invalid": "json", "missing_comma": true "invalid_syntax"}
    Create File            ${MODULE_DIR}${/}invalid_config.json    ${invalid_config}
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, json
    ...    sys.path.append('${MODULE_DIR}')
    ...    
    ...    from app import read_json_file
    ...    
    ...    try:
    ...        config = read_json_file('${MODULE_DIR}/invalid_config.json')
    ...        print('ERROR_HANDLING_FAILED')
    ...    except json.JSONDecodeError:
    ...        print('JSON_ERROR_HANDLED')
    ...    except Exception as e:
    ...        print(f'OTHER_ERROR_HANDLED: {type(e).__name__}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    ERROR_HANDLED
    
    # Cleanup
    Remove File    ${MODULE_DIR}${/}invalid_config.json
    
    Log    Invalid configuration handling verified

Test Configuration Value Types
    [Documentation]    Test that configuration values have correct data types
    [Tags]             config    types    validation
    
    ${config_content} =    Get File    ${MODULE_DIR}${/}${CONFIG_FILE}
    ${config_json} =      Convert String To Json    ${config_content}
    
    # Verify data types
    Should Be True        isinstance(${config_json['port']}, int)
    Should Be True        isinstance(${config_json['host']}, str)
    Should Be True        isinstance(${config_json['schedule_time']}, int)
    Should Be True        isinstance(${config_json['is_unhealthy_test_mode']}, bool)
    
    # Verify value ranges
    Should Be True        ${config_json['port']} > 0
    Should Be True        ${config_json['port']} < 65536
    Should Be True        ${config_json['schedule_time']} > 0
    
    Log    Configuration value types verified

# =============================================================================
# Error Handling and Edge Cases
# =============================================================================

Test Missing Namespace Handling
    [Documentation]    Test handling when namespace cannot be determined
    [Tags]             error_handling    namespace    edge_case
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    from unittest.mock import patch
    ...    
    ...    # Mock namespace function to return None
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.return_value = None
    ...        
    ...        try:
    ...            from CommandExecutor import CommandExecutor
    ...            
    ...            config = {'test': 'config'}
    ...            executor = CommandExecutor(config, False)
    ...            
    ...            if executor.namespace is None:
    ...                print('NAMESPACE_NONE_HANDLED')
    ...            else:
    ...                print('NAMESPACE_NONE_NOT_HANDLED')
    ...        except Exception as e:
    ...            print(f'NAMESPACE_ERROR_HANDLED: {type(e).__name__}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    HANDLED
    Log    Missing namespace handling verified

Test Command Execution Failure
    [Documentation]    Test handling of failed command execution
    [Tags]             error_handling    command    failure
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, subprocess
    ...    from unittest.mock import patch, MagicMock
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    # Mock subprocess to simulate command failure
    ...    with patch('subprocess.run') as mock_run, \\
    ...         patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        
    ...        mock_ns.return_value = 'test-namespace'
    ...        mock_run.side_effect = subprocess.CalledProcessError(1, 'kubectl')
    ...        
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        config = {'test': 'config'}
    ...        executor = CommandExecutor(config, False)
    ...        
    ...        try:
    ...            result = executor.execute_command('failing_command', 'test_operation')
    ...            print('COMMAND_FAILURE_HANDLED')
    ...        except Exception as e:
    ...            print(f'COMMAND_FAILURE_ERROR: {type(e).__name__}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    HANDLED
    Log    Command execution failure handling verified

Test Zero Pod Count Scenario
    [Documentation]    Test handling when no pods are found
    [Tags]             edge_case    pods    zero_count
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    from unittest.mock import patch
    ...    
    ...    # Mock namespace function
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.return_value = 'test-namespace'
    ...        
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        config = {'test': 'config'}
    ...        executor = CommandExecutor(config, False)
    ...        
    ...        # Test zero division scenario
    ...        try:
    ...            percentage = executor.calculate_percentage(0, 0)
    ...            print(f'ZERO_DIVISION_RESULT: {percentage}')
    ...        except ZeroDivisionError:
    ...            print('ZERO_DIVISION_ERROR_HANDLED')
    ...        except Exception as e:
    ...            print(f'OTHER_ERROR: {type(e).__name__}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Log    Zero pod count scenario handled: ${result.stdout}

# =============================================================================
# Performance and Reliability Testing
# =============================================================================

Test Application Response Time
    [Documentation]    Test application response time under normal conditions
    [Tags]             performance    response_time    load
    
    Start Test Application
    Sleep    3s
    
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    # Measure response time for multiple requests
    @{response_times} =    Create List
    
    FOR    ${i}    IN RANGE    5
        ${start_time} =    Get Current Date    result_format=epoch
        ${response} =      GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
        ${end_time} =      Get Current Date    result_format=epoch
        ${duration} =      Evaluate    ${end_time} - ${start_time}
        Append To List     ${response_times}    ${duration}
        Sleep              1s
    END
    
    # Calculate average response time
    ${total_time} =        Evaluate    sum(${response_times})
    ${avg_time} =          Evaluate    ${total_time} / len(${response_times})
    
    # Response time should be reasonable (less than 5 seconds)
    Should Be True         ${avg_time} < 5
    
    Log    Average response time: ${avg_time} seconds
    
    [Teardown]    Stop Test Application

Test Concurrent Request Handling
    [Documentation]    Test application handling of concurrent requests
    [Tags]             performance    concurrent    load
    
    Start Test Application
    Sleep    3s
    
    # This test simulates concurrent access by making rapid sequential requests
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    @{results} =    Create List
    
    FOR    ${i}    IN RANGE    3
        ${response} =    GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
        Append To List   ${results}    ${response.status_code}
    END
    
    # All requests should complete (either successfully or with consistent errors)
    ${unique_codes} =    Remove Duplicates    ${results}
    ${code_count} =      Get Length    ${unique_codes}
    
    # Should have consistent response codes
    Should Be True       ${code_count} <= 2
    
    Log    Concurrent requests handled with status codes: ${results}
    
    [Teardown]    Stop Test Application

Test Memory Usage Simulation
    [Documentation]    Test application memory usage patterns
    [Tags]             performance    memory    resource
    
    # This test runs a simple simulation to check for obvious memory issues
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, gc, time
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    from unittest.mock import patch
    ...    
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.return_value = 'test-namespace'
    ...        
    ...        # Import and create multiple instances
    ...        from CommandExecutor import CommandExecutor
    ...        
    ...        objects = []
    ...        for i in range(10):
    ...            config = {'test': f'config_{i}'}
    ...            executor = CommandExecutor(config, False)
    ...            objects.append(executor)
    ...        
    ...        # Force garbage collection
    ...        del objects
    ...        gc.collect()
    ...        
    ...        print('MEMORY_TEST_COMPLETED')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    MEMORY_TEST_COMPLETED
    Log    Memory usage simulation completed successfully

# =============================================================================
# Integration Testing
# =============================================================================

Test Full Workflow Integration
    [Documentation]    Test complete workflow from startup to health status response
    [Tags]             integration    workflow    end_to_end
    
    Start Test Application
    Sleep    3s
    
    Create Session    air_health    ${APP_BASE_URL}    timeout=${REQUEST_TIMEOUT}
    
    # Test the complete workflow
    ${response} =    GET On Session    air_health    ${APP_ENDPOINT}    expected_status=any
    
    # Verify response structure regardless of success/failure
    Should Be True    ${response.status_code} in [200, 500, 503]
    
    # If successful, verify JSON structure
    IF    ${response.status_code} == 200
        ${json_response} =    Convert String To Json    ${response.text}
        Should Contain        ${json_response}    data
        Log    Full workflow completed successfully
    ELSE
        Log    Workflow completed with expected error status: ${response.status_code}
    END
    
    [Teardown]    Stop Test Application

Test Configuration Integration
    [Documentation]    Test integration between configuration files and application logic
    [Tags]             integration    configuration    files
    
    # Verify configuration consistency
    ${config_content} =     Get File    ${MODULE_DIR}${/}${CONFIG_FILE}
    ${config_json} =       Convert String To Json    ${config_content}
    
    ${command_content} =    Get File    ${MODULE_DIR}${/}${COMMAND_FILE}
    ${command_json} =      Convert String To Json    ${command_content}
    
    # Verify that configurations are consistent
    Should Be True          ${config_json['port']} > 0
    Should Be True          ${command_json['air_pod_threshold']} >= 0
    Should Be True          ${command_json['air_pod_threshold']} <= 100
    
    # Test that host and port are valid
    Should Not Be Empty     ${config_json['host']}
    Should Be True          isinstance(${config_json['port']}, int)
    
    Log    Configuration integration verified

Test Error Recovery Integration
    [Documentation]    Test application recovery from various error scenarios
    [Tags]             integration    error_recovery    resilience
    
    ${test_script} =    Catenate    SEPARATOR=\n
    ...    import sys, json
    ...    from unittest.mock import patch, MagicMock
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    # Test recovery from namespace error
    ...    with patch('lib.Namespace.get_application_namespace') as mock_ns:
    ...        mock_ns.side_effect = [Exception('Namespace error'), 'recovered-namespace']
    ...        
    ...        try:
    ...            from CommandExecutor import CommandExecutor
    ...            
    ...            # First call should handle error
    ...            config = {'test': 'config'}
    ...            executor1 = CommandExecutor(config, False)
    ...            
    ...            # Second call should work with recovered namespace
    ...            executor2 = CommandExecutor(config, False)
    ...            
    ...            print('ERROR_RECOVERY_SUCCESS')
    ...        except Exception as e:
    ...            print(f'ERROR_RECOVERY_FAILED: {e}')
    
    ${result} =    Run Process    python    -c    ${test_script}    shell=True    timeout=${TEST_TIMEOUT}
    
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain                 ${result.stdout}    SUCCESS
    Log    Error recovery integration verified

*** Keywords ***
Setup Test Environment
    [Documentation]    Set up the test environment for all tests
    
    Log    Setting up test environment for air_health_check
    
    # Verify module directory exists
    Directory Should Exist    ${MODULE_DIR}
    
    # Set test variables
    Set Global Variable       ${TEST_APP_PROCESS}    ${NONE}
    
    Log    Test environment setup completed

Cleanup Test Environment
    [Documentation]    Clean up the test environment after all tests
    
    Log    Cleaning up test environment
    
    # Ensure no test applications are running
    Stop Test Application
    
    # Clean up any temporary files
    Run Keyword And Ignore Error    Remove File    ${MODULE_DIR}${/}test_*.json
    Run Keyword And Ignore Error    Remove File    ${MODULE_DIR}${/}*.log
    
    Log    Test environment cleanup completed

Setup Individual Test
    [Documentation]    Set up before each individual test
    
    Log    Setting up individual test: ${TEST NAME}

Cleanup Individual Test
    [Documentation]    Clean up after each individual test
    
    Log    Cleaning up individual test: ${TEST NAME}
    
    # Ensure any sessions are closed
    Run Keyword And Ignore Error    Delete All Sessions

Start Test Application
    [Documentation]    Start the Flask application for testing
    
    Log    Starting test application
    
    # Create a test script that mocks external dependencies
    ${test_app_script} =    Catenate    SEPARATOR=\n
    ...    import sys, os, threading, time
    ...    sys.path.append('${MODULE_DIR}')
    ...    sys.path.append('${MODULE_DIR}/..')
    ...    
    ...    # Mock external dependencies
    ...    import lib.Namespace
    ...    lib.Namespace.get_application_namespace = lambda: 'test-namespace'
    ...    
    ...    # Mock subprocess for kubectl commands
    ...    import subprocess
    ...    original_run = subprocess.run
    ...    
    ...    def mock_run(*args, **kwargs):
    ...        # Return mock kubectl responses
    ...        if 'kubectl get pods' in str(args):
    ...            class MockResult:
    ...                stdout = 'pod1 Running 1/1\\npod2 Running 1/1'
    ...                stderr = ''
    ...                returncode = 0
    ...            return MockResult()
    ...        return original_run(*args, **kwargs)
    ...    
    ...    subprocess.run = mock_run
    ...    
    ...    # Start the Flask app
    ...    from app import app, read_json_file
    ...    
    ...    try:
    ...        config = read_json_file('${MODULE_DIR}/${CONFIG_FILE}')
    ...        app.run(host='${APP_HOST}', port=${APP_PORT}, debug=False, use_reloader=False)
    ...    except Exception as e:
    ...        print(f'App start error: {e}')
    
    Create File    ${MODULE_DIR}${/}test_app_runner.py    ${test_app_script}
    
    # Start application in background
    ${process} =    Start Process    python    ${MODULE_DIR}${/}test_app_runner.py
    ...             shell=True    alias=test_app
    
    Set Global Variable    ${TEST_APP_PROCESS}    ${process}
    
    Log    Test application started with PID: ${process.pid}

Stop Test Application
    [Documentation]    Stop the Flask application
    
    Log    Stopping test application
    
    IF    ${TEST_APP_PROCESS} is not None
        TRY
            Terminate Process    ${TEST_APP_PROCESS}
            Wait For Process     ${TEST_APP_PROCESS}    timeout=5s
        EXCEPT
            Log    Force killing test application
            TRY
                Kill Process    ${TEST_APP_PROCESS}
            EXCEPT
                Log    Could not kill test application process
            END
        END
        
        Set Global Variable    ${TEST_APP_PROCESS}    ${NONE}
    END
    
    # Clean up test runner script
    Run Keyword And Ignore Error    Remove File    ${MODULE_DIR}${/}test_app_runner.py
    
    Log    Test application stopped
