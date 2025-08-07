*** Settings ***
Documentation    Comprehensive test suite for CLEAN_UP module
...              Tests file cleanup operations including local system, Splunk, and TPIM cleanup
...              Covers configuration management, file operations, subprocess execution, and error handling

Resource         cleanup_resource.robot
Suite Setup      Setup Test Environment
Suite Teardown   Cleanup Test Environment
Test Timeout     5 minutes

*** Variables ***
${MODULE_NAME}              CLEAN_UP
${TEST_DATA_DIR}           ${CURDIR}/test_data
${TEMP_TEST_DIR}           ${CURDIR}/temp_test_files

*** Test Cases ***

# Configuration Management Tests
Test Configuration Loading
    [Documentation]    Test loading configuration from config.json file
    [Tags]    config    basic    cleanup
    
    ${config} =    Load Clean Up Configuration    ${CLEANUP_CONFIG_FILE}
    Should Not Be Empty    ${config}
    Verify Configuration Structure    ${config}
    
    # Verify required configuration keys
    Should Contain    ${config}    local
    Should Contain    ${config}    splunk
    Should Contain    ${config}    tpim

Test Configuration Validation
    [Documentation]    Test configuration parameter validation
    [Tags]    config    validation    cleanup
    
    ${config} =    Load Clean Up Configuration    ${CLEANUP_CONFIG_FILE}
    
    # Validate local configuration
    ${local_config} =    Get From Dictionary    ${config}    local
    Should Contain    ${local_config}    files_retention_days
    Should Contain    ${local_config}    paths
    
    # Validate splunk configuration
    ${splunk_config} =    Get From Dictionary    ${config}    splunk
    Should Contain    ${splunk_config}    files_retention_days
    Should Contain    ${splunk_config}    container
    Should Contain    ${splunk_config}    paths

Test Invalid Configuration File
    [Documentation]    Test handling of invalid configuration file
    [Tags]    config    error    cleanup
    
    Run Keyword And Expect Error    *    Load Clean Up Configuration    ${INVALID_CONFIG_FILE}

Test Missing Configuration File
    [Documentation]    Test handling of missing configuration file
    [Tags]    config    error    cleanup
    
    Run Keyword And Expect Error    *    Load Clean Up Configuration    ${NON_EXISTENT_CONFIG_FILE}

# File Cleanup Operations Tests
Test Local File Cleanup
    [Documentation]    Test local file system cleanup operations
    [Tags]    file    local    cleanup    basic
    
    # Create test files with different ages
    Create Test Files With Ages    ${TEMP_TEST_DIR}    10
    
    # Execute cleanup for files older than 5 days
    ${result} =    Execute Local File Cleanup    5    ${TEMP_TEST_DIR}
    
    # Verify old files are removed
    Verify File Cleanup Results    ${TEMP_TEST_DIR}    5

Test Local File Cleanup With Multiple Paths
    [Documentation]    Test cleanup across multiple local directories
    [Tags]    file    local    cleanup    integration
    
    # Create multiple test directories
    ${test_dirs} =    Create List    ${TEMP_TEST_DIR}/dir1    ${TEMP_TEST_DIR}/dir2    ${TEMP_TEST_DIR}/dir3
    Create Test Directories And Files    ${test_dirs}
    
    # Execute cleanup
    ${result} =    Execute Local File Cleanup Multiple Paths    7    ${test_dirs}
    
    # Verify cleanup across all directories
    FOR    ${dir}    IN    @{test_dirs}
        Verify File Cleanup Results    ${dir}    7
    END

Test Local File Cleanup With No Files
    [Documentation]    Test cleanup when no files match criteria
    [Tags]    file    local    cleanup    edge
    
    Create Directory    ${TEMP_TEST_DIR}/empty
    ${result} =    Execute Local File Cleanup    5    ${TEMP_TEST_DIR}/empty
    Should Be Equal    ${result}    ${None}

Test Splunk File Cleanup
    [Documentation]    Test Splunk container file cleanup operations
    [Tags]    file    splunk    cleanup    integration
    
    # Mock Splunk pod and container
    Set Mock Splunk Environment
    
    # Execute Splunk cleanup
    ${result} =    Execute Splunk File Cleanup    ${MOCK_SPLUNK_POD}    ${MOCK_SPLUNK_CONTAINER}    7    ${MOCK_SPLUNK_PATHS}
    
    # Verify kubectl command execution
    Verify Splunk Cleanup Command Execution

Test TPIM File Cleanup
    [Documentation]    Test TPIM file cleanup operations
    [Tags]    file    tpim    cleanup    basic
    
    # Create TPIM test environment
    Create TPIM Test Files    ${TEMP_TEST_DIR}/tpim
    
    # Execute TPIM cleanup
    ${result} =    Execute TPIM File Cleanup    5    ${TEMP_TEST_DIR}/tpim
    
    # Verify cleanup results
    Verify TPIM Cleanup Results    ${TEMP_TEST_DIR}/tpim    5

# Subprocess Execution Tests
Test Command Execution
    [Documentation]    Test subprocess command execution functionality
    [Tags]    subprocess    basic    cleanup
    
    ${output}    ${error} =    Execute Cleanup Command    echo "test"
    Should Be Equal    ${output}    test\n
    Should Be Equal    ${error}    ${None}

Test Command Execution With Error
    [Documentation]    Test subprocess command execution with errors
    [Tags]    subprocess    error    cleanup
    
    ${output}    ${error} =    Execute Cleanup Command    ls /non_existent_directory
    Should Not Be Equal    ${error}    ${None}
    Should Contain    ${error}    No such file or directory

Test Command Timeout Handling
    [Documentation]    Test handling of long-running commands
    [Tags]    subprocess    timeout    cleanup
    
    ${output}    ${error} =    Execute Cleanup Command With Timeout    sleep 10    5
    Should Not Be Equal    ${error}    ${None}

# Kubernetes Integration Tests
Test Get Splunk Pods
    [Documentation]    Test retrieval of Splunk forwarder pods
    [Tags]    kubernetes    splunk    integration    cleanup
    
    Set Mock Kubernetes Environment
    ${splunk_pods} =    Get Splunk Forwarder Pods    ${MOCK_NAMESPACE}
    Should Not Be Empty    ${splunk_pods}
    
    FOR    ${pod}    IN    @{splunk_pods}
        Should Contain    ${pod}    splunk
    END

Test Get Splunk Pods No Results
    [Documentation]    Test handling when no Splunk pods are found
    [Tags]    kubernetes    splunk    error    cleanup
    
    Set Mock Kubernetes Environment With No Splunk
    Run Keyword And Expect Error    *    Get Splunk Forwarder Pods    ${MOCK_NAMESPACE}

Test Kubectl Command Execution
    [Documentation]    Test kubectl command execution
    [Tags]    kubernetes    integration    cleanup
    
    Set Mock Kubernetes Environment
    ${result} =    Execute Kubectl Command    get pods -n ${MOCK_NAMESPACE}
    Should Not Be Empty    ${result}

# Performance Tests
Test Large Directory Cleanup Performance
    [Documentation]    Test performance with large number of files
    [Tags]    performance    file    cleanup
    
    # Create large number of test files
    Create Large Test File Set    ${TEMP_TEST_DIR}/large    1000
    
    ${start_time} =    Get Current Date    result_format=epoch
    ${result} =    Execute Local File Cleanup    5    ${TEMP_TEST_DIR}/large
    ${end_time} =    Get Current Date    result_format=epoch
    
    ${duration} =    Evaluate    ${end_time} - ${start_time}
    Should Be True    ${duration} < 60    Cleanup should complete within 60 seconds

Test Parallel Cleanup Operations
    [Documentation]    Test parallel cleanup across multiple directories
    [Tags]    performance    parallel    cleanup
    
    # Create multiple test directories
    ${test_dirs} =    Create Multiple Test Directories    5
    
    ${start_time} =    Get Current Date    result_format=epoch
    Execute Parallel Cleanup    ${test_dirs}
    ${end_time} =    Get Current Date    result_format=epoch
    
    ${duration} =    Evaluate    ${end_time} - ${start_time}
    Should Be True    ${duration} < 30    Parallel cleanup should be faster

# Error Handling Tests
Test Invalid Path Handling
    [Documentation]    Test handling of invalid file paths
    [Tags]    error    file    cleanup
    
    ${result} =    Execute Local File Cleanup    5    /invalid/path/does/not/exist
    Verify Error Handling    ${result}

Test Permission Denied Handling
    [Documentation]    Test handling of permission denied errors
    [Tags]    error    permission    cleanup
    
    # Create file with restricted permissions
    Create Restricted Permission File    ${TEMP_TEST_DIR}/restricted
    
    ${result} =    Execute Local File Cleanup    5    ${TEMP_TEST_DIR}/restricted
    Verify Permission Error Handling    ${result}

Test Network Error Handling
    [Documentation]    Test handling of network connectivity issues
    [Tags]    error    network    cleanup
    
    Set Mock Network Error Environment
    Run Keyword And Expect Error    *    Get Splunk Forwarder Pods    ${MOCK_NAMESPACE}

# Integration Tests
Test Full Cleanup Workflow
    [Documentation]    Test complete cleanup workflow with all components
    [Tags]    integration    workflow    cleanup
    
    # Setup test environment
    Setup Full Integration Test Environment
    
    # Execute main cleanup workflow
    ${result} =    Execute Full Cleanup Workflow
    
    # Verify all cleanup operations completed
    Verify Full Cleanup Results

Test Cleanup With Real Configuration
    [Documentation]    Test cleanup using actual configuration file
    [Tags]    integration    config    cleanup
    
    ${config} =    Load Clean Up Configuration    ${CLEANUP_CONFIG_FILE}
    
    # Execute cleanup with real configuration (using mock data)
    ${result} =    Execute Cleanup With Configuration    ${config}
    
    # Verify execution completed successfully
    Should Not Be Equal    ${result}    ${None}

Test Process Check Integration
    [Documentation]    Test integration with process check functionality
    [Tags]    integration    process    cleanup
    
    # Verify process check prevents multiple instances
    ${pid_file} =    Set Variable    ${TEMP_TEST_DIR}/cleanup_test.pid
    
    ${result1} =    Start Cleanup Process    ${pid_file}
    ${result2} =    Start Cleanup Process    ${pid_file}
    
    # Second process should fail due to existing PID file
    Should Not Be Equal    ${result1}    ${result2}

# Business Logic Tests
Test Retention Period Calculation
    [Documentation]    Test retention period calculation (days - 2)
    [Tags]    business    calculation    cleanup
    
    ${config} =    Load Clean Up Configuration    ${CLEANUP_CONFIG_FILE}
    
    # Verify retention days are reduced by 2
    ${local_config} =    Get From Dictionary    ${config}    local
    ${original_days} =    Get From Dictionary    ${local_config}    files_retention_days
    
    ${calculated_days} =    Calculate Retention Days    ${original_days}
    ${expected_days} =    Evaluate    ${original_days} - 2
    
    Should Be Equal As Numbers    ${calculated_days}    ${expected_days}

Test File Age Filtering
    [Documentation]    Test filtering files based on modification time
    [Tags]    business    filtering    cleanup
    
    # Create files with different ages
    Create Files With Different Ages    ${TEMP_TEST_DIR}/age_test
    
    # Test filtering with different retention periods
    ${files_5_days} =    Get Files Older Than Days    ${TEMP_TEST_DIR}/age_test    5
    ${files_10_days} =    Get Files Older Than Days    ${TEMP_TEST_DIR}/age_test    10
    
    # More files should match longer retention period
    ${count_5} =    Get Length    ${files_5_days}
    ${count_10} =    Get Length    ${files_10_days}
    
    Should Be True    ${count_5} >= ${count_10}

Test Cleanup Path Validation
    [Documentation]    Test validation of cleanup paths
    [Tags]    business    validation    cleanup
    
    ${valid_paths} =    Create List    /tmp/test1    /tmp/test2
    ${invalid_paths} =    Create List    /invalid/path    ${EMPTY}
    
    ${valid_result} =    Validate Cleanup Paths    ${valid_paths}
    ${invalid_result} =    Validate Cleanup Paths    ${invalid_paths}
    
    Should Be True    ${valid_result}
    Should Be True    ${invalid_result} == ${False}

# Edge Cases and Boundary Tests
Test Empty Configuration
    [Documentation]    Test handling of empty configuration
    [Tags]    edge    config    cleanup
    
    Create Empty Configuration File    ${TEMP_TEST_DIR}/empty_config.json
    Run Keyword And Expect Error    *    Load Clean Up Configuration    ${TEMP_TEST_DIR}/empty_config.json

Test Zero Retention Days
    [Documentation]    Test cleanup with zero retention days
    [Tags]    edge    retention    cleanup
    
    Create Test Files With Ages    ${TEMP_TEST_DIR}/zero_retention    5
    ${result} =    Execute Local File Cleanup    0    ${TEMP_TEST_DIR}/zero_retention
    
    # All files should be removed with zero retention
    Verify All Files Removed    ${TEMP_TEST_DIR}/zero_retention

Test Very Large Retention Period
    [Documentation]    Test cleanup with very large retention period
    [Tags]    edge    retention    cleanup
    
    Create Test Files With Ages    ${TEMP_TEST_DIR}/large_retention    30
    ${result} =    Execute Local File Cleanup    9999    ${TEMP_TEST_DIR}/large_retention
    
    # No files should be removed with very large retention
    Verify No Files Removed    ${TEMP_TEST_DIR}/large_retention
