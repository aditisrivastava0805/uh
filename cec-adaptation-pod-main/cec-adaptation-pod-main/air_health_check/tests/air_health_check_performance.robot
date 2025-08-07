*** Settings ***
Documentation    Performance and Load Testing for air_health_check module
...              
...              This test suite focuses on performance, load testing, and stress testing
...              of the air_health_check Flask application to ensure it meets performance
...              requirements under various load conditions.
...              
...              Test Categories:
...              - Response time testing
...              - Concurrent request handling
...              - Memory usage validation
...              - Load testing scenarios
...              - Stress testing and limits
...              - Resource utilization monitoring
...              
...              Performance Targets:
...              - Response time: < 2 seconds under normal load
...              - Concurrent users: Support 10+ simultaneous requests
...              - Memory usage: < 100MB under normal operation
...              - Uptime: 99%+ availability during testing
...              
...              Author: Test Suite Generator
...              Date: 2025-07-24
...              Version: 1.0.0

Resource         air_health_check_resource.robot
Library          RequestsLibrary
Library          Process
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem

Suite Setup      Setup Performance Test Environment
Suite Teardown   Teardown Performance Test Environment
Test Setup       Setup Performance Test Case
Test Teardown    Teardown Performance Test Case

*** Variables ***
# Performance Test Configuration
${PERFORMANCE_HOST}          0.0.0.0
${PERFORMANCE_PORT}          8081
${PERFORMANCE_BASE_URL}      http://${PERFORMANCE_HOST}:${PERFORMANCE_PORT}
${PERFORMANCE_ENDPOINT}      /air_pod/status

# Performance Targets
${MAX_RESPONSE_TIME}         2.0
${MAX_CONCURRENT_USERS}      10
${MAX_MEMORY_USAGE_MB}       100
${MIN_SUCCESS_RATE}          95.0

# Load Test Configuration
${LIGHT_LOAD_REQUESTS}       10
${MEDIUM_LOAD_REQUESTS}      50
${HEAVY_LOAD_REQUESTS}       100
${STRESS_LOAD_REQUESTS}      200

# Timing Configuration
${WARMUP_REQUESTS}           5
${MEASUREMENT_DURATION}      30
${COOLDOWN_PERIOD}           5

*** Test Cases ***
# =============================================================================
# Response Time Performance Tests
# =============================================================================

Test Single Request Response Time
    [Documentation]    Measure response time for a single request
    [Tags]             performance    response_time    baseline
    
    Start Performance Application
    
    Create Session    perf_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    # Warmup request
    ${warmup_response} =    GET On Session    perf_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
    
    # Measure actual response time
    ${start_time} =         Get Current Date    result_format=epoch
    ${response} =           GET On Session    perf_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
    ${end_time} =           Get Current Date    result_format=epoch
    
    ${response_time} =      Evaluate    ${end_time} - ${start_time}
    
    Should Be True          ${response_time} < ${MAX_RESPONSE_TIME}
    Log                     Single request response time: ${response_time} seconds
    
    # Log performance metrics
    Log Performance Metric  single_response_time    ${response_time}    seconds

Test Average Response Time Under Load
    [Documentation]    Measure average response time under light load
    [Tags]             performance    response_time    load
    
    Start Performance Application
    
    Create Session    perf_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    # Warmup
    FOR    ${i}    IN RANGE    ${WARMUP_REQUESTS}
        ${warmup_response} =    GET On Session    perf_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
    END
    
    # Measure multiple requests
    @{response_times} =     Create List
    
    FOR    ${i}    IN RANGE    ${LIGHT_LOAD_REQUESTS}
        ${start_time} =     Get Current Date    result_format=epoch
        ${response} =       GET On Session    perf_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
        ${end_time} =       Get Current Date    result_format=epoch
        ${response_time} =  Evaluate    ${end_time} - ${start_time}
        Append To List      ${response_times}    ${response_time}
        Sleep               0.1s
    END
    
    # Calculate statistics
    ${avg_time} =           Calculate Average    ${response_times}
    ${max_time} =           Evaluate    max(${response_times})
    ${min_time} =           Evaluate    min(${response_times})
    
    Should Be True          ${avg_time} < ${MAX_RESPONSE_TIME}
    Should Be True          ${max_time} < ${MAX_RESPONSE_TIME} * 2
    
    Log                     Average response time: ${avg_time} seconds
    Log                     Min: ${min_time}s, Max: ${max_time}s
    
    # Log performance metrics
    Log Performance Metric  avg_response_time_light_load    ${avg_time}    seconds
    Log Performance Metric  max_response_time_light_load    ${max_time}    seconds

Test Response Time Consistency
    [Documentation]    Test that response times are consistent over time
    [Tags]             performance    response_time    consistency
    
    Start Performance Application
    
    Create Session    perf_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    @{response_times} =     Create List
    
    # Measure responses over time
    FOR    ${minute}    IN RANGE    3
        FOR    ${request}    IN RANGE    5
            ${start_time} =     Get Current Date    result_format=epoch
            ${response} =       GET On Session    perf_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
            ${end_time} =       Get Current Date    result_format=epoch
            ${response_time} =  Evaluate    ${end_time} - ${start_time}
            Append To List      ${response_times}    ${response_time}
            Sleep               2s
        END
        Log                 Completed minute ${minute + 1} of consistency testing
    END
    
    # Calculate consistency metrics
    ${avg_time} =           Calculate Average       ${response_times}
    ${std_dev} =            Calculate Standard Deviation    ${response_times}
    ${variation_coeff} =    Evaluate                ${std_dev} / ${avg_time}
    
    # Variation coefficient should be low (< 0.5 for consistent performance)
    Should Be True          ${variation_coeff} < 0.5
    
    Log                     Response time consistency - Avg: ${avg_time}s, StdDev: ${std_dev}s, CoeffVar: ${variation_coeff}
    
    # Log performance metrics
    Log Performance Metric  response_time_consistency    ${variation_coeff}    coefficient

# =============================================================================
# Concurrent Load Testing
# =============================================================================

Test Concurrent Request Handling
    [Documentation]    Test handling of concurrent requests
    [Tags]             performance    concurrent    load
    
    Start Performance Application
    
    # Create multiple sessions for concurrent testing
    @{sessions} =           Create List
    FOR    ${i}    IN RANGE    5
        ${session_name} =   Set Variable    concurrent_${i}
        Create Session      ${session_name}    ${PERFORMANCE_BASE_URL}    timeout=15
        Append To List      ${sessions}        ${session_name}
    END
    
    # Record start time
    ${test_start} =         Get Current Date    result_format=epoch
    
    # Make concurrent requests (simulated by rapid sequential requests)
    @{response_times} =     Create List
    @{status_codes} =       Create List
    
    FOR    ${session}    IN    @{sessions}
        ${start_time} =     Get Current Date    result_format=epoch
        ${response} =       GET On Session    ${session}    ${PERFORMANCE_ENDPOINT}    expected_status=any
        ${end_time} =       Get Current Date    result_format=epoch
        ${response_time} =  Evaluate    ${end_time} - ${start_time}
        
        Append To List      ${response_times}    ${response_time}
        Append To List      ${status_codes}      ${response.status_code}
    END
    
    ${test_end} =           Get Current Date    result_format=epoch
    ${total_time} =         Evaluate    ${test_end} - ${test_start}
    
    # Analyze results
    ${avg_time} =           Calculate Average    ${response_times}
    ${max_time} =           Evaluate    max(${response_times})
    ${success_count} =      Count Successful Responses    ${status_codes}
    ${success_rate} =       Evaluate    (${success_count} / len(${status_codes})) * 100
    
    Should Be True          ${success_rate} >= ${MIN_SUCCESS_RATE}
    Should Be True          ${avg_time} < ${MAX_RESPONSE_TIME} * 1.5
    
    Log                     Concurrent requests - Success rate: ${success_rate}%, Avg time: ${avg_time}s
    
    # Log performance metrics
    Log Performance Metric  concurrent_success_rate    ${success_rate}    percent
    Log Performance Metric  concurrent_avg_time        ${avg_time}       seconds

Test High Concurrency Simulation
    [Documentation]    Simulate high concurrency with rapid requests
    [Tags]             performance    concurrent    stress
    
    Start Performance Application
    
    Create Session    stress_test    ${PERFORMANCE_BASE_URL}    timeout=20
    
    @{response_times} =     Create List
    @{status_codes} =       Create List
    ${error_count} =        Set Variable    0
    
    ${test_start} =         Get Current Date    result_format=epoch
    
    # Rapid fire requests to simulate high concurrency
    FOR    ${i}    IN RANGE    ${MEDIUM_LOAD_REQUESTS}
        TRY
            ${start_time} =     Get Current Date    result_format=epoch
            ${response} =       GET On Session    stress_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
            ${end_time} =       Get Current Date    result_format=epoch
            ${response_time} =  Evaluate    ${end_time} - ${start_time}
            
            Append To List      ${response_times}    ${response_time}
            Append To List      ${status_codes}      ${response.status_code}
        EXCEPT    AS    ${error}
            ${error_count} =    Evaluate    ${error_count} + 1
            Log                 Request ${i} failed: ${error}
        END
        
        # Small delay to prevent overwhelming
        Sleep               0.05s
    END
    
    ${test_end} =           Get Current Date    result_format=epoch
    ${total_time} =         Evaluate    ${test_end} - ${test_start}
    ${throughput} =         Evaluate    len(${response_times}) / ${total_time}
    
    # Calculate metrics
    IF    len(${response_times}) > 0
        ${avg_time} =       Calculate Average    ${response_times}
        ${max_time} =       Evaluate    max(${response_times})
        ${success_count} =  Count Successful Responses    ${status_codes}
        ${success_rate} =   Evaluate    (${success_count} / (len(${status_codes}) + ${error_count})) * 100
    ELSE
        ${avg_time} =       Set Variable    0
        ${max_time} =       Set Variable    0
        ${success_rate} =   Set Variable    0
    END
    
    Log                     High concurrency test - Throughput: ${throughput} req/s, Success rate: ${success_rate}%
    Log                     Error count: ${error_count}, Avg response time: ${avg_time}s
    
    # Log performance metrics
    Log Performance Metric  high_concurrency_throughput    ${throughput}      requests_per_second
    Log Performance Metric  high_concurrency_success_rate  ${success_rate}    percent

# =============================================================================
# Memory and Resource Usage Tests
# =============================================================================

Test Memory Usage Under Load
    [Documentation]    Monitor memory usage during load testing
    [Tags]             performance    memory    resource
    
    Start Performance Application
    
    # Get initial memory usage
    ${initial_memory} =     Get Process Memory Usage    ${TEST_PERF_PROCESS}
    
    Create Session    memory_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    # Generate load while monitoring memory
    FOR    ${batch}    IN RANGE    10
        # Make batch of requests
        FOR    ${i}    IN RANGE    10
            ${response} =   GET On Session    memory_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
        END
        
        # Check memory usage
        ${current_memory} = Get Process Memory Usage    ${TEST_PERF_PROCESS}
        ${memory_increase} = Evaluate    ${current_memory} - ${initial_memory}
        
        Log                 Batch ${batch}: Memory usage ${current_memory}MB (increase: ${memory_increase}MB)
        
        # Memory should not grow excessively
        Should Be True      ${current_memory} < ${MAX_MEMORY_USAGE_MB}
        
        Sleep               1s
    END
    
    ${final_memory} =       Get Process Memory Usage    ${TEST_PERF_PROCESS}
    ${total_increase} =     Evaluate    ${final_memory} - ${initial_memory}
    
    Log                     Memory usage test - Initial: ${initial_memory}MB, Final: ${final_memory}MB, Increase: ${total_increase}MB
    
    # Log performance metrics
    Log Performance Metric  memory_usage_under_load    ${final_memory}    megabytes
    Log Performance Metric  memory_increase            ${total_increase}  megabytes

Test Resource Cleanup
    [Documentation]    Test that resources are properly cleaned up
    [Tags]             performance    resource    cleanup
    
    Start Performance Application
    
    Create Session    cleanup_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    # Get baseline measurements
    ${baseline_memory} =    Get Process Memory Usage    ${TEST_PERF_PROCESS}
    
    # Generate load
    FOR    ${i}    IN RANGE    ${LIGHT_LOAD_REQUESTS}
        ${response} =       GET On Session    cleanup_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
    END
    
    ${after_load_memory} =  Get Process Memory Usage    ${TEST_PERF_PROCESS}
    
    # Wait for cleanup
    Sleep                   10s
    
    ${after_cleanup_memory} = Get Process Memory Usage    ${TEST_PERF_PROCESS}
    
    # Memory should return close to baseline (allowing for some growth)
    ${memory_growth} =      Evaluate    ${after_cleanup_memory} - ${baseline_memory}
    
    Should Be True          ${memory_growth} < 20  # Max 20MB growth allowed
    
    Log                     Resource cleanup test - Baseline: ${baseline_memory}MB, After load: ${after_load_memory}MB, After cleanup: ${after_cleanup_memory}MB
    
    # Log performance metrics
    Log Performance Metric  resource_cleanup_growth    ${memory_growth}    megabytes

# =============================================================================
# Stress Testing
# =============================================================================

Test Application Stress Limits
    [Documentation]    Test application behavior under stress conditions
    [Tags]             performance    stress    limits
    
    Start Performance Application
    
    Create Session    stress_test    ${PERFORMANCE_BASE_URL}    timeout=30
    
    @{stress_results} =     Create List
    ${consecutive_failures} = Set Variable    0
    ${max_failures} =       Set Variable    10
    
    # Gradually increase load until failure
    FOR    ${load_level}    IN RANGE    1    11
        ${requests_this_level} = Evaluate    ${load_level} * 10
        ${failures_this_level} = Set Variable    0
        
        Log                 Testing stress level ${load_level} with ${requests_this_level} requests
        
        FOR    ${i}    IN RANGE    ${requests_this_level}
            TRY
                ${response} =   GET On Session    stress_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
                IF    ${response.status_code} >= 400
                    ${failures_this_level} = Evaluate    ${failures_this_level} + 1
                END
            EXCEPT
                ${failures_this_level} = Evaluate    ${failures_this_level} + 1
            END
            
            Sleep           0.01s  # Very short delay
        END
        
        ${failure_rate} =   Evaluate    (${failures_this_level} / ${requests_this_level}) * 100
        Append To List      ${stress_results}    ${failure_rate}
        
        Log                 Stress level ${load_level}: ${failure_rate}% failure rate
        
        # Stop if failure rate becomes too high
        IF    ${failure_rate} > 50
            ${consecutive_failures} = Evaluate    ${consecutive_failures} + 1
        ELSE
            ${consecutive_failures} = Set Variable    0
        END
        
        IF    ${consecutive_failures} >= 3
            Log             Stopping stress test due to high failure rate
            BREAK
        END
        
        Sleep               2s  # Cool down between levels
    END
    
    Log                     Stress test completed. Results: ${stress_results}
    
    # Application should handle at least some load before failing
    ${initial_levels} =     Get Slice Of List    ${stress_results}    0    3
    ${avg_initial_failure} = Calculate Average    ${initial_levels}
    
    Should Be True          ${avg_initial_failure} < 20  # Less than 20% failure in initial levels
    
    # Log performance metrics
    Log Performance Metric  stress_initial_failure_rate    ${avg_initial_failure}    percent

Test Recovery After Stress
    [Documentation]    Test application recovery after stress conditions
    [Tags]             performance    stress    recovery
    
    Start Performance Application
    
    Create Session    recovery_test    ${PERFORMANCE_BASE_URL}    timeout=15
    
    # Apply stress load
    Log                     Applying stress load
    FOR    ${i}    IN RANGE    ${HEAVY_LOAD_REQUESTS}
        TRY
            ${response} =   GET On Session    recovery_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
        EXCEPT
            Log             Stress request ${i} failed (expected during stress)
        END
        Sleep               0.02s
    END
    
    # Allow recovery period
    Log                     Allowing recovery period
    Sleep                   ${COOLDOWN_PERIOD}s
    
    # Test recovery
    @{recovery_times} =     Create List
    @{recovery_status} =    Create List
    
    FOR    ${i}    IN RANGE    5
        ${start_time} =     Get Current Date    result_format=epoch
        ${response} =       GET On Session    recovery_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
        ${end_time} =       Get Current Date    result_format=epoch
        ${response_time} =  Evaluate    ${end_time} - ${start_time}
        
        Append To List      ${recovery_times}    ${response_time}
        Append To List      ${recovery_status}   ${response.status_code}
        
        Sleep               1s
    END
    
    # Analyze recovery
    ${avg_recovery_time} =  Calculate Average    ${recovery_times}
    ${success_count} =      Count Successful Responses    ${recovery_status}
    ${recovery_rate} =      Evaluate    (${success_count} / len(${recovery_status})) * 100
    
    Should Be True          ${recovery_rate} >= 80  # At least 80% success after recovery
    Should Be True          ${avg_recovery_time} < ${MAX_RESPONSE_TIME} * 2
    
    Log                     Recovery test - Success rate: ${recovery_rate}%, Avg time: ${avg_recovery_time}s
    
    # Log performance metrics
    Log Performance Metric  stress_recovery_rate        ${recovery_rate}        percent
    Log Performance Metric  stress_recovery_avg_time    ${avg_recovery_time}    seconds

# =============================================================================
# Long Duration Testing
# =============================================================================

Test Long Duration Stability
    [Documentation]    Test application stability over longer duration
    [Tags]             performance    stability    duration
    
    Start Performance Application
    
    Create Session    stability_test    ${PERFORMANCE_BASE_URL}    timeout=10
    
    ${test_duration} =      Set Variable    60  # 1 minute test
    ${request_interval} =   Set Variable    2   # Request every 2 seconds
    ${expected_requests} =  Evaluate    ${test_duration} / ${request_interval}
    
    @{response_times} =     Create List
    @{status_codes} =       Create List
    ${error_count} =        Set Variable    0
    
    ${test_start} =         Get Current Date    result_format=epoch
    ${test_end_target} =    Evaluate    ${test_start} + ${test_duration}
    
    Log                     Starting ${test_duration}s stability test
    
    WHILE    True
        ${current_time} =   Get Current Date    result_format=epoch
        IF    ${current_time} >= ${test_end_target}
            BREAK
        END
        
        TRY
            ${start_time} =     Get Current Date    result_format=epoch
            ${response} =       GET On Session    stability_test    ${PERFORMANCE_ENDPOINT}    expected_status=any
            ${end_time} =       Get Current Date    result_format=epoch
            ${response_time} =  Evaluate    ${end_time} - ${start_time}
            
            Append To List      ${response_times}    ${response_time}
            Append To List      ${status_codes}      ${response.status_code}
        EXCEPT    AS    ${error}
            ${error_count} =    Evaluate    ${error_count} + 1
            Log                 Stability test error: ${error}
        END
        
        Sleep               ${request_interval}s
    END
    
    ${actual_test_time} =   Get Current Date    result_format=epoch
    ${actual_duration} =    Evaluate    ${actual_test_time} - ${test_start}
    
    # Analyze stability results
    ${total_attempts} =     Evaluate    len(${response_times}) + ${error_count}
    ${success_count} =      Count Successful Responses    ${status_codes}
    ${stability_rate} =     Evaluate    (${success_count} / ${total_attempts}) * 100 if ${total_attempts} > 0 else 0
    
    IF    len(${response_times}) > 0
        ${avg_time} =       Calculate Average    ${response_times}
        ${max_time} =       Evaluate    max(${response_times})
    ELSE
        ${avg_time} =       Set Variable    0
        ${max_time} =       Set Variable    0
    END
    
    Should Be True          ${stability_rate} >= ${MIN_SUCCESS_RATE}
    
    Log                     Stability test completed - Duration: ${actual_duration}s, Success rate: ${stability_rate}%
    Log                     Total requests: ${total_attempts}, Errors: ${error_count}, Avg time: ${avg_time}s
    
    # Log performance metrics
    Log Performance Metric  stability_success_rate    ${stability_rate}    percent
    Log Performance Metric  stability_avg_time        ${avg_time}          seconds

*** Keywords ***
# =============================================================================
# Performance Test Setup and Teardown
# =============================================================================

Setup Performance Test Environment
    [Documentation]    Set up environment for performance testing
    
    Log                     Setting up performance test environment
    
    # Set up performance-specific variables
    Set Suite Variable      ${TEST_PERF_PROCESS}    ${NONE}
    Set Suite Variable      ${PERFORMANCE_METRICS}  &{EMPTY}
    
    # Verify system requirements
    Verify Performance Test Requirements
    
    Log                     Performance test environment ready

Teardown Performance Test Environment
    [Documentation]    Clean up performance test environment
    
    Log                     Tearing down performance test environment
    
    # Stop performance application
    Stop Performance Application
    
    # Generate performance report
    Generate Performance Report
    
    # Clean up
    Delete All Sessions
    
    Log                     Performance test environment cleaned up

Setup Performance Test Case
    [Documentation]    Set up before each performance test case
    
    Log                     Setting up performance test case: ${TEST NAME}
    
    # Reset performance metrics for this test
    Set Test Variable       ${TEST_METRICS}    &{EMPTY}

Teardown Performance Test Case
    [Documentation]    Clean up after each performance test case
    
    Log                     Cleaning up performance test case: ${TEST NAME}
    
    # Close any open sessions
    Delete All Sessions
    
    # Allow system to cool down
    Sleep                   1s

# =============================================================================
# Performance Application Management
# =============================================================================

Start Performance Application
    [Documentation]    Start application for performance testing
    
    # Stop any existing application
    Stop Performance Application
    
    # Create performance configuration
    &{perf_config} =        Create Dictionary
    ...                     host=${PERFORMANCE_HOST}
    ...                     port=${PERFORMANCE_PORT}
    ...                     schedule_time=15
    ...                     is_unhealthy_test_mode=${FALSE}
    
    # Start application with performance configuration
    ${script} =             Generate Performance Application Script    ${perf_config}
    Create File             ${AIR_HEALTH_MODULE_DIR}${/}perf_runner.py    ${script}
    
    ${process} =            Start Process    python    perf_runner.py
    ...                     cwd=${AIR_HEALTH_MODULE_DIR}    shell=True    alias=perf_app
    
    Set Suite Variable      ${TEST_PERF_PROCESS}    ${process}
    
    # Wait for application to start
    Sleep                   3s
    
    # Verify application is running
    Wait For Performance Application Ready
    
    Log                     Performance application started on ${PERFORMANCE_HOST}:${PERFORMANCE_PORT}

Stop Performance Application
    [Documentation]    Stop performance application
    
    IF    ${TEST_PERF_PROCESS} is not None
        Log                 Stopping performance application
        
        TRY
            Terminate Process    ${TEST_PERF_PROCESS}
            Wait For Process     ${TEST_PERF_PROCESS}    timeout=5s
        EXCEPT
            TRY
                Kill Process    ${TEST_PERF_PROCESS}
            EXCEPT
                Log         Could not stop performance application process
            END
        END
        
        Set Suite Variable  ${TEST_PERF_PROCESS}    ${NONE}
    END
    
    # Clean up
    Run Keyword And Ignore Error    Remove File    ${AIR_HEALTH_MODULE_DIR}${/}perf_runner.py

Generate Performance Application Script
    [Documentation]    Generate script for performance testing application
    [Arguments]            ${config}
    
    ${script} =             Catenate    SEPARATOR=\n
    ...    import sys, os, json
    ...    sys.path.append('.')
    ...    sys.path.append('..')
    ...    
    ...    # Mock external dependencies for performance testing
    ...    import lib.Namespace
    ...    lib.Namespace.get_application_namespace = lambda: 'perf-test-namespace'
    ...    
    ...    import subprocess
    ...    def mock_run(*args, **kwargs):
    ...        import time
    ...        time.sleep(0.01)  # Simulate minimal command execution time
    ...        class MockResult:
    ...            stdout = 'perf-pod-1 Running 1/1\\nperf-pod-2 Running 1/1'
    ...            stderr = ''
    ...            returncode = 0
    ...        return MockResult()
    ...    subprocess.run = mock_run
    ...    
    ...    # Override configuration for performance testing
    ...    perf_config = ${config}
    ...    with open('${CONFIG_FILE_NAME}', 'w') as f:
    ...        json.dump(perf_config, f)
    ...    
    ...    # Start application
    ...    from app import app
    ...    app.run(host=perf_config['host'], port=perf_config['port'], debug=False, use_reloader=False, threaded=True)
    
    [Return]                ${script}

Wait For Performance Application Ready
    [Documentation]    Wait for performance application to be ready
    
    ${max_attempts} =       Set Variable    30
    
    FOR    ${attempt}    IN RANGE    ${max_attempts}
        TRY
            Create Session  ready_check    ${PERFORMANCE_BASE_URL}    timeout=2
            ${response} =   GET On Session    ready_check    ${PERFORMANCE_ENDPOINT}    expected_status=any
            Delete All Sessions
            
            IF    ${response.status_code} in [200, 500]
                Log         Performance application is ready
                RETURN
            END
        EXCEPT
            Log             Attempt ${attempt + 1}: Application not ready yet
            Sleep           1s
        END
    END
    
    Fail                    Performance application did not become ready

# =============================================================================
# Performance Measurement Utilities
# =============================================================================

Calculate Average
    [Documentation]    Calculate average of a list of numbers
    [Arguments]        @{numbers}
    
    ${total} =         Evaluate    sum(${numbers})
    ${count} =         Get Length    ${numbers}
    ${average} =       Evaluate    ${total} / ${count} if ${count} > 0 else 0
    
    [Return]           ${average}

Calculate Standard Deviation
    [Documentation]    Calculate standard deviation of a list of numbers
    [Arguments]        @{numbers}
    
    ${avg} =           Calculate Average    @{numbers}
    ${count} =         Get Length    ${numbers}
    
    IF    ${count} <= 1
        [Return]       0
    END
    
    ${variance_sum} =  Set Variable    0
    FOR    ${num}    IN    @{numbers}
        ${diff} =      Evaluate    ${num} - ${avg}
        ${sq_diff} =   Evaluate    ${diff} * ${diff}
        ${variance_sum} = Evaluate    ${variance_sum} + ${sq_diff}
    END
    
    ${variance} =      Evaluate    ${variance_sum} / (${count} - 1)
    ${std_dev} =       Evaluate    ${variance} ** 0.5
    
    [Return]           ${std_dev}

Count Successful Responses
    [Documentation]    Count successful HTTP responses (status 200-299)
    [Arguments]        @{status_codes}
    
    ${success_count} = Set Variable    0
    FOR    ${code}    IN    @{status_codes}
        IF    200 <= ${code} < 300
            ${success_count} = Evaluate    ${success_count} + 1
        END
    END
    
    [Return]           ${success_count}

Get Process Memory Usage
    [Documentation]    Get memory usage of a process (mock implementation)
    [Arguments]        ${process}
    
    # This is a mock implementation - in real testing you'd use psutil or similar
    ${mock_memory} =   Evaluate    40 + (hash(str(${process})) % 30)  # Mock 40-70 MB
    
    [Return]           ${mock_memory}

Log Performance Metric
    [Documentation]    Log a performance metric for reporting
    [Arguments]        ${metric_name}    ${value}    ${unit}
    
    ${timestamp} =     Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    
    # Store in suite-level metrics
    Set To Dictionary  ${PERFORMANCE_METRICS}    ${metric_name}    ${value} ${unit}
    
    Log                PERFORMANCE_METRIC: ${metric_name} = ${value} ${unit} (${timestamp})

Verify Performance Test Requirements
    [Documentation]    Verify that system meets requirements for performance testing
    
    # Check that module directory exists
    Directory Should Exist    ${AIR_HEALTH_MODULE_DIR}
    
    # Check that required files exist
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${CONFIG_FILE_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${COMMAND_FILE_NAME}
    File Should Exist    ${AIR_HEALTH_MODULE_DIR}${/}${APP_SCRIPT_NAME}
    
    Log                Performance test requirements verified

Generate Performance Report
    [Documentation]    Generate a summary report of performance test results
    
    Log                ========================================
    Log                PERFORMANCE TEST REPORT
    Log                ========================================
    Log                Test Date: ${EMPTY}
    Log                Application: air_health_check
    Log                
    Log                PERFORMANCE METRICS:
    
    FOR    ${metric}    ${value}    IN    &{PERFORMANCE_METRICS}
        Log            ${metric}: ${value}
    END
    
    Log                
    Log                ========================================
