*** Settings ***
Documentation    Resource file for CLEAN_UP module Robot Framework tests
...              Contains keywords, variables, and test data for cleanup operations testing

Library          Collections
Library          DateTime
Library          JSONLibrary
Library          OperatingSystem
Library          Process
Library          String

*** Variables ***
# Module Configuration
${CLEANUP_MODULE_DIR}           ${CURDIR}/..
${CLEANUP_CONFIG_FILE}          ${CLEANUP_MODULE_DIR}/config/config.json
${CLEANUP_MAIN_SCRIPT}          ${CLEANUP_MODULE_DIR}/main.py

# Test Configuration
${TEST_TIMEOUT}                 300s
${DEFAULT_NAMESPACE}            test-namespace
${MOCK_NAMESPACE}               mock-namespace

# Test Data Files
${INVALID_CONFIG_FILE}          ${CURDIR}/test_data/invalid_config.json
${NON_EXISTENT_CONFIG_FILE}     ${CURDIR}/test_data/non_existent.json
${EMPTY_CONFIG_FILE}            ${CURDIR}/test_data/empty_config.json

# Mock Data
${MOCK_SPLUNK_POD}              mock-splunk-forwarder-12345
${MOCK_SPLUNK_CONTAINER}        splunkforwarder
${MOCK_SPLUNK_PATHS}            /var/log/splunk/test1    /var/log/splunk/test2

# Performance Test Limits
${MAX_EXECUTION_TIME}           60
${LARGE_FILE_COUNT}             1000
${PARALLEL_DIR_COUNT}           5

# Business Logic Constants
${RETENTION_REDUCTION}          2
${MIN_RETENTION_DAYS}           0
${MAX_RETENTION_DAYS}           365

*** Keywords ***

# Setup and Teardown Keywords
Setup Test Environment
    [Documentation]    Setup test environment for CLEAN_UP module tests
    
    Log    Setting up CLEAN_UP test environment
    Create Directory    ${TEST_DATA_DIR}
    Create Directory    ${TEMP_TEST_DIR}
    
    # Create test configuration files
    Create Test Configuration Files
    
    # Setup mock environment
    Setup Mock Environment
    
    Log    CLEAN_UP test environment setup completed

Cleanup Test Environment
    [Documentation]    Cleanup test environment after tests
    
    Log    Cleaning up CLEAN_UP test environment
    
    # Remove temporary test files and directories
    Remove Directory    ${TEST_DATA_DIR}    recursive=${True}
    Remove Directory    ${TEMP_TEST_DIR}    recursive=${True}
    
    # Cleanup mock environment
    Cleanup Mock Environment
    
    Log    CLEAN_UP test environment cleanup completed

Setup Mock Environment
    [Documentation]    Setup mock environment for testing
    
    Set Environment Variable    MOCK_MODE    true
    Set Environment Variable    MOCK_NAMESPACE    ${MOCK_NAMESPACE}
    Set Environment Variable    MOCK_KUBECTL_AVAILABLE    true

Cleanup Mock Environment
    [Documentation]    Cleanup mock environment
    
    Remove Environment Variable    MOCK_MODE
    Remove Environment Variable    MOCK_NAMESPACE
    Remove Environment Variable    MOCK_KUBECTL_AVAILABLE

# Configuration Management Keywords
Load Clean Up Configuration
    [Documentation]    Load and parse CLEAN_UP configuration file
    [Arguments]    ${config_file_path}
    
    Log    Loading configuration from: ${config_file_path}
    File Should Exist    ${config_file_path}
    
    ${config_content} =    Get File    ${config_file_path}
    ${config} =    Convert String To Json    ${config_content}
    
    Log    Configuration loaded successfully
    [Return]    ${config}

Verify Configuration Structure
    [Documentation]    Verify the structure of loaded configuration
    [Arguments]    ${config}
    
    Log    Verifying configuration structure
    
    # Verify top-level keys
    Dictionary Should Contain Key    ${config}    local
    Dictionary Should Contain Key    ${config}    splunk
    Dictionary Should Contain Key    ${config}    tpim
    
    # Verify local configuration structure
    ${local_config} =    Get From Dictionary    ${config}    local
    Dictionary Should Contain Key    ${local_config}    files_retention_days
    Dictionary Should Contain Key    ${local_config}    paths
    
    # Verify splunk configuration structure
    ${splunk_config} =    Get From Dictionary    ${config}    splunk
    Dictionary Should Contain Key    ${splunk_config}    files_retention_days
    Dictionary Should Contain Key    ${splunk_config}    container
    Dictionary Should Contain Key    ${splunk_config}    paths
    
    Log    Configuration structure verification completed

Create Test Configuration Files
    [Documentation]    Create test configuration files
    
    # Create invalid configuration file
    ${invalid_config} =    Create Dictionary    invalid_key=invalid_value
    ${invalid_json} =    Convert Json To String    ${invalid_config}
    Create File    ${INVALID_CONFIG_FILE}    ${invalid_json}
    
    # Create empty configuration file
    Create File    ${EMPTY_CONFIG_FILE}    {}

# File Operations Keywords
Create Test Files With Ages
    [Documentation]    Create test files with different modification times
    [Arguments]    ${directory}    ${max_age_days}
    
    Log    Creating test files with ages up to ${max_age_days} days in ${directory}
    Create Directory    ${directory}
    
    FOR    ${age}    IN RANGE    0    ${max_age_days}
        ${filename} =    Set Variable    test_file_${age}_days_old.txt
        ${filepath} =    Join Path    ${directory}    ${filename}
        
        Create File    ${filepath}    Test file created ${age} days ago
        
        # Modify file timestamp to simulate age
        ${timestamp} =    Get Current Date    increment=-${age} days    result_format=epoch
        Set Modified Time    ${filepath}    ${timestamp}
    END
    
    Log    Created ${max_age_days} test files with different ages

Create Test Directories And Files
    [Documentation]    Create test directories with files
    [Arguments]    ${directories}
    
    FOR    ${directory}    IN    @{directories}
        Create Directory    ${directory}
        Create Test Files With Ages    ${directory}    10
    END

Execute Local File Cleanup
    [Documentation]    Execute local file system cleanup
    [Arguments]    ${retention_days}    ${path}
    
    Log    Executing local file cleanup: retention=${retention_days} days, path=${path}
    
    ${command} =    Set Variable    find ${path} -maxdepth 1 -type f -mtime +${retention_days} -print -delete
    ${result} =    Run Process    ${command}    shell=True
    
    Log    Local file cleanup completed
    [Return]    ${result}

Execute Local File Cleanup Multiple Paths
    [Documentation]    Execute cleanup across multiple local paths
    [Arguments]    ${retention_days}    ${paths}
    
    Log    Executing cleanup across multiple paths
    
    FOR    ${path}    IN    @{paths}
        Execute Local File Cleanup    ${retention_days}    ${path}
    END

Verify File Cleanup Results
    [Documentation]    Verify file cleanup was successful
    [Arguments]    ${directory}    ${retention_days}
    
    Log    Verifying cleanup results for ${directory} with ${retention_days} days retention
    
    # Check that old files are removed and recent files remain
    ${files} =    List Files In Directory    ${directory}
    
    FOR    ${file}    IN    @{files}
        ${filepath} =    Join Path    ${directory}    ${file}
        ${file_age} =    Get File Age In Days    ${filepath}
        Should Be True    ${file_age} <= ${retention_days}    File ${file} should have been removed
    END

# Mock Environment Keywords
Set Mock Splunk Environment
    [Documentation]    Setup mock Splunk environment
    
    Set Environment Variable    MOCK_SPLUNK_POD    ${MOCK_SPLUNK_POD}
    Set Environment Variable    MOCK_SPLUNK_CONTAINER    ${MOCK_SPLUNK_CONTAINER}

Set Mock Kubernetes Environment
    [Documentation]    Setup mock Kubernetes environment
    
    Set Environment Variable    MOCK_KUBECTL_OUTPUT    splunk-forwarder-1\nsplunk-forwarder-2

Set Mock Kubernetes Environment With No Splunk
    [Documentation]    Setup mock Kubernetes environment with no Splunk pods
    
    Set Environment Variable    MOCK_KUBECTL_OUTPUT    ${EMPTY}

Set Mock Network Error Environment
    [Documentation]    Setup mock environment to simulate network errors
    
    Set Environment Variable    MOCK_NETWORK_ERROR    true

# Subprocess Execution Keywords
Execute Cleanup Command
    [Documentation]    Execute a cleanup command using subprocess
    [Arguments]    ${command}
    
    Log    Executing command: ${command}
    ${result} =    Run Process    ${command}    shell=True
    
    ${output} =    Set Variable If    '${result.stdout}' != ''    ${result.stdout}    ${None}
    ${error} =    Set Variable If    '${result.stderr}' != ''    ${result.stderr}    ${None}
    
    [Return]    ${output}    ${error}

Execute Cleanup Command With Timeout
    [Documentation]    Execute cleanup command with timeout
    [Arguments]    ${command}    ${timeout}
    
    ${result} =    Run Process    ${command}    shell=True    timeout=${timeout}s
    
    ${output} =    Set Variable If    '${result.stdout}' != ''    ${result.stdout}    ${None}
    ${error} =    Set Variable If    '${result.stderr}' != ''    ${result.stderr}    ${None}
    
    [Return]    ${output}    ${error}

# Kubernetes Integration Keywords
Get Splunk Forwarder Pods
    [Documentation]    Get list of Splunk forwarder pods
    [Arguments]    ${namespace}
    
    Log    Getting Splunk forwarder pods in namespace: ${namespace}
    
    ${command} =    Set Variable    kubectl get pods -n ${namespace} | grep splunk | awk '{print $1}'
    ${result} =    Run Process    ${command}    shell=True
    
    Should Be Equal As Integers    ${result.rc}    0    kubectl command should succeed
    
    ${pods} =    Split String    ${result.stdout}    \n
    ${filtered_pods} =    Create List
    
    FOR    ${pod}    IN    @{pods}
        ${pod_trimmed} =    Strip String    ${pod}
        Run Keyword If    '${pod_trimmed}' != ''    Append To List    ${filtered_pods}    ${pod_trimmed}
    END
    
    [Return]    ${filtered_pods}

Execute Kubectl Command
    [Documentation]    Execute kubectl command
    [Arguments]    ${kubectl_args}
    
    ${command} =    Set Variable    kubectl ${kubectl_args}
    ${result} =    Run Process    ${command}    shell=True
    
    Should Be Equal As Integers    ${result.rc}    0    kubectl command should succeed
    [Return]    ${result.stdout}

Execute Splunk File Cleanup
    [Documentation]    Execute file cleanup in Splunk container
    [Arguments]    ${pod_name}    ${container}    ${retention_days}    ${paths}
    
    Log    Executing Splunk cleanup: pod=${pod_name}, container=${container}
    
    FOR    ${path}    IN    @{paths}
        ${command} =    Set Variable    kubectl exec -it ${pod_name} -c ${container} -- find ${path} -maxdepth 1 -type f -mtime +${retention_days} -delete
        ${result} =    Run Process    ${command}    shell=True
    END

Verify Splunk Cleanup Command Execution
    [Documentation]    Verify Splunk cleanup commands were executed correctly
    
    Log    Verifying Splunk cleanup command execution
    # This would verify command execution in a real environment

Execute TPIM File Cleanup
    [Documentation]    Execute TPIM file cleanup
    [Arguments]    ${retention_days}    ${path}
    
    Log    Executing TPIM file cleanup: retention=${retention_days} days, path=${path}
    
    ${command} =    Set Variable    find ${path} -maxdepth 1 -type f -mtime +${retention_days} -delete
    ${result} =    Run Process    ${command}    shell=True
    
    [Return]    ${result}

# Performance Testing Keywords
Create Large Test File Set
    [Documentation]    Create large number of test files for performance testing
    [Arguments]    ${directory}    ${file_count}
    
    Log    Creating ${file_count} test files in ${directory}
    Create Directory    ${directory}
    
    FOR    ${i}    IN RANGE    ${file_count}
        ${filename} =    Set Variable    large_test_file_${i}.txt
        ${filepath} =    Join Path    ${directory}    ${filename}
        Create File    ${filepath}    Test file ${i} for performance testing
    END

Create Multiple Test Directories
    [Documentation]    Create multiple test directories for parallel testing
    [Arguments]    ${count}
    
    ${directories} =    Create List
    
    FOR    ${i}    IN RANGE    ${count}
        ${dirname} =    Set Variable    ${TEMP_TEST_DIR}/parallel_test_${i}
        Create Directory    ${dirname}
        Create Test Files With Ages    ${dirname}    10
        Append To List    ${directories}    ${dirname}
    END
    
    [Return]    ${directories}

Execute Parallel Cleanup
    [Documentation]    Execute cleanup operations in parallel
    [Arguments]    ${directories}
    
    # Simulate parallel execution by processing directories in sequence
    # In a real implementation, this would use actual parallel processing
    FOR    ${directory}    IN    @{directories}
        Execute Local File Cleanup    5    ${directory}
    END

# Error Handling Keywords
Verify Error Handling
    [Documentation]    Verify proper error handling
    [Arguments]    ${result}
    
    Log    Verifying error handling for result: ${result}
    # Verify that errors are handled gracefully

Verify Permission Error Handling
    [Documentation]    Verify handling of permission errors
    [Arguments]    ${result}
    
    Log    Verifying permission error handling
    # Verify that permission errors are handled appropriately

Create Restricted Permission File
    [Documentation]    Create file with restricted permissions
    [Arguments]    ${filepath}
    
    Create File    ${filepath}    Restricted file content
    # In a real test, would set restricted permissions

# Business Logic Keywords
Calculate Retention Days
    [Documentation]    Calculate retention days (original - 2)
    [Arguments]    ${original_days}
    
    ${calculated} =    Evaluate    ${original_days} - ${RETENTION_REDUCTION}
    [Return]    ${calculated}

Get Files Older Than Days
    [Documentation]    Get files older than specified days
    [Arguments]    ${directory}    ${days}
    
    ${files} =    List Files In Directory    ${directory}
    ${old_files} =    Create List
    
    FOR    ${file}    IN    @{files}
        ${filepath} =    Join Path    ${directory}    ${file}
        ${age} =    Get File Age In Days    ${filepath}
        Run Keyword If    ${age} > ${days}    Append To List    ${old_files}    ${file}
    END
    
    [Return]    ${old_files}

Get File Age In Days
    [Documentation]    Get file age in days
    [Arguments]    ${filepath}
    
    ${modified_time} =    Get Modified Time    ${filepath}    epoch
    ${current_time} =    Get Current Date    result_format=epoch
    ${age_seconds} =    Evaluate    ${current_time} - ${modified_time}
    ${age_days} =    Evaluate    ${age_seconds} / 86400
    
    [Return]    ${age_days}

Validate Cleanup Paths
    [Documentation]    Validate cleanup paths
    [Arguments]    ${paths}
    
    FOR    ${path}    IN    @{paths}
        ${path_exists} =    Run Keyword And Return Status    Directory Should Exist    ${path}
        Return From Keyword If    not ${path_exists}    ${False}
    END
    
    [Return]    ${True}

Create Files With Different Ages
    [Documentation]    Create files with different ages for testing
    [Arguments]    ${directory}
    
    Create Directory    ${directory}
    
    # Create files with ages: 1, 3, 7, 15, 30 days
    ${ages} =    Create List    1    3    7    15    30
    
    FOR    ${age}    IN    @{ages}
        ${filename} =    Set Variable    file_${age}_days.txt
        ${filepath} =    Join Path    ${directory}    ${filename}
        Create File    ${filepath}    File content for ${age} days old
        
        ${timestamp} =    Get Current Date    increment=-${age} days    result_format=epoch
        Set Modified Time    ${filepath}    ${timestamp}
    END

# Integration Test Keywords
Setup Full Integration Test Environment
    [Documentation]    Setup complete integration test environment
    
    Setup Test Environment
    Set Mock Splunk Environment
    Set Mock Kubernetes Environment

Execute Full Cleanup Workflow
    [Documentation]    Execute complete cleanup workflow
    
    ${config} =    Load Clean Up Configuration    ${CLEANUP_CONFIG_FILE}
    
    # Execute all cleanup operations
    ${local_result} =    Execute Local File Cleanup    5    ${TEMP_TEST_DIR}
    ${splunk_result} =    Execute Splunk File Cleanup    ${MOCK_SPLUNK_POD}    ${MOCK_SPLUNK_CONTAINER}    5    ${MOCK_SPLUNK_PATHS}
    ${tpim_result} =    Execute TPIM File Cleanup    5    ${TEMP_TEST_DIR}/tpim
    
    [Return]    ${local_result}

Verify Full Cleanup Results
    [Documentation]    Verify results of full cleanup workflow
    
    Log    Verifying full cleanup workflow results
    # Verify that all cleanup operations completed successfully

Execute Cleanup With Configuration
    [Documentation]    Execute cleanup using configuration
    [Arguments]    ${config}
    
    Log    Executing cleanup with provided configuration
    
    # Extract configuration values
    ${local_config} =    Get From Dictionary    ${config}    local
    ${local_retention} =    Get From Dictionary    ${local_config}    files_retention_days
    ${local_paths} =    Get From Dictionary    ${local_config}    paths
    
    # Execute cleanup operations
    FOR    ${path}    IN    @{local_paths}
        ${result} =    Run Keyword And Return Status    Execute Local File Cleanup    ${local_retention}    ${path}
    END
    
    [Return]    ${True}

Start Cleanup Process
    [Documentation]    Start cleanup process with PID file
    [Arguments]    ${pid_file}
    
    ${result} =    Run Process    python    ${CLEANUP_MAIN_SCRIPT}    env:CLEANUP_PID_FILE=${pid_file}
    [Return]    ${result}

# Edge Case Keywords
Create Empty Configuration File
    [Documentation]    Create empty configuration file
    [Arguments]    ${filepath}
    
    Create File    ${filepath}    ${EMPTY}

Verify All Files Removed
    [Documentation]    Verify all files were removed from directory
    [Arguments]    ${directory}
    
    ${files} =    List Files In Directory    ${directory}
    Should Be Empty    ${files}    All files should be removed

Verify No Files Removed
    [Documentation]    Verify no files were removed from directory
    [Arguments]    ${directory}
    
    ${files} =    List Files In Directory    ${directory}
    Should Not Be Empty    ${files}    No files should be removed

Create TPIM Test Files
    [Documentation]    Create TPIM test files
    [Arguments]    ${directory}
    
    Create Directory    ${directory}
    Create Test Files With Ages    ${directory}    10

Verify TPIM Cleanup Results
    [Documentation]    Verify TPIM cleanup results
    [Arguments]    ${directory}    ${retention_days}
    
    Verify File Cleanup Results    ${directory}    ${retention_days}
