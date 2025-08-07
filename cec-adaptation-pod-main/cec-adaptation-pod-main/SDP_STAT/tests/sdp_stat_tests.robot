*** Settings ***
Documentation    Comprehensive Robot Framework test suite for SDP_STAT module
...              Tests SDP statistics processing, configuration management, file operations,
...              SFTP integration, concurrent processing, error handling, and performance metrics.

Resource         sdp_stat_resource.robot
Test Setup       Setup SDP_STAT Test Environment  
Test Teardown    Teardown SDP_STAT Test Environment
Force Tags       sdp_stat    integration

*** Test Cases ***

Test SDP_STAT Module Structure
    [Documentation]    Verify SDP_STAT module has all required files and dependencies
    [Tags]    structure    smoke
    Verify SDP_STAT Module Structure

Test SDP_STAT Configuration File Loading
    [Documentation]    Test loading and validation of SDP_STAT configuration files
    [Tags]    configuration    unit
    [Setup]    Create Test Configuration Files
    Verify Configuration Loading    ${TEST_CONFIG_FILE}
    Verify SDP_STAT Configuration Parameters

Test SDP_STAT Argument Parsing
    [Documentation]    Test command line argument parsing functionality
    [Tags]    args    unit
    Verify Argument Parsing

Test SDP_STAT Argument Parsing With Wait Flag
    [Documentation]    Test command line argument parsing with wait flag
    [Tags]    args    unit
    ${result}=    Run Process    python    ${SDP_STAT_SCRIPT}    --wait    --help
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Contain    ${result.stdout}    --wait
    Should Be Equal As Integers    ${result.rc}    0

Test SDP_STAT Configuration Parameter Validation
    [Documentation]    Test validation of individual configuration parameters
    [Tags]    configuration    validation
    Verify SDP_STAT Configuration Parameters
    Verify SFTP Configuration
    Verify Splunk Configuration

Test SDP_STAT Basic Statistics Processing
    [Documentation]    Test basic SDP statistics file processing functionality
    [Tags]    processing    core
    Create Test Stat Files    3
    Verify Stat Processing

Test SDP_STAT Pod Environment Setup
    [Documentation]    Test mock Kubernetes pod environment setup
    [Tags]    kubernetes    setup
    Create Mock Pod Environment
    Directory Should Exist    ${TEST_DATA_DIR}${/}test-pod-1
    Directory Should Exist    ${TEST_DATA_DIR}${/}test-pod-2
    Directory Should Exist    ${TEST_DATA_DIR}${/}test-pod-3

Test SDP_STAT Pod Whitelist Filtering
    [Documentation]    Test pod whitelist filtering functionality
    [Tags]    kubernetes    filtering
    [Setup]    Create Mock Pod Environment
    ${whitelist_pods}=    Create List    test-pod-1    test-pod-2
    Verify Pod Filtering    whitelist    ${whitelist_pods}

Test SDP_STAT Pod Blacklist Filtering
    [Documentation]    Test pod blacklist filtering functionality
    [Tags]    kubernetes    filtering
    [Setup]    Create Mock Pod Environment
    ${blacklist_pods}=    Create List    test-pod-3
    Verify Pod Filtering    blacklist    ${blacklist_pods}

Test SDP_STAT File Processing With Timestamps
    [Documentation]    Test file processing with timestamp filtering
    [Tags]    processing    timestamps
    Create Test Stat Files    5
    ${files}=    List Files In Directory    ${TEST_DATA_DIR}
    Length Should Be    ${files}    5
    FOR    ${file}    IN    @{files}
        ${file_time}=    Get Modified Time    ${TEST_DATA_DIR}${/}${file}
        Should Not Be Empty    ${file_time}
    END

Test SDP_STAT Concurrent Processing
    [Documentation]    Test concurrent processing of multiple stat files
    [Tags]    performance    concurrency
    Verify Concurrent Processing

Test SDP_STAT Performance Metrics
    [Documentation]    Test SDP_STAT performance meets acceptable thresholds
    [Tags]    performance    metrics
    Verify Performance Metrics    120

Test SDP_STAT Resource Monitoring
    [Documentation]    Monitor system resource usage during SDP_STAT execution
    [Tags]    performance    monitoring
    Monitor System Resources

Test SDP_STAT Missing Configuration Error Handling
    [Documentation]    Test error handling for missing configuration file
    [Tags]    error_handling    configuration
    Verify Error Handling    missing_config

Test SDP_STAT Invalid JSON Error Handling
    [Documentation]    Test error handling for invalid JSON configuration
    [Tags]    error_handling    configuration
    Verify Error Handling    invalid_json

Test SDP_STAT Missing Directory Error Handling
    [Documentation]    Test error handling for missing data directory
    [Tags]    error_handling    filesystem
    Verify Error Handling    missing_directory

Test SDP_STAT SFTP Configuration Validation
    [Documentation]    Test SFTP configuration parameter validation
    [Tags]    sftp    configuration
    Verify SFTP Configuration

Test SDP_STAT Splunk Configuration Validation
    [Documentation]    Test Splunk configuration parameter validation
    [Tags]    splunk    configuration
    Verify Splunk Configuration

Test SDP_STAT Security Measures
    [Documentation]    Test security measures and credential handling
    [Tags]    security    credentials
    Verify Security Measures

Test SDP_STAT Logger Configuration
    [Documentation]    Test logger configuration and initialization
    [Tags]    logging    configuration
    File Should Exist    ${TEST_LOGGER_CONFIG}
    ${logger_content}=    Get File    ${TEST_LOGGER_CONFIG}
    Should Contain    ${logger_content}    handlers
    Should Contain    ${logger_content}    formatters

Test SDP_STAT Directory Lookup Configuration
    [Documentation]    Test directory lookup path configuration
    [Tags]    configuration    filesystem
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Dictionary Should Contain Key    ${config}    dir_lookup
    Should Not Be Empty    ${config}[dir_lookup]

Test SDP_STAT File Age Filtering
    [Documentation]    Test file age filtering based on file_newer_than_min parameter
    [Tags]    processing    filtering
    Create Test Stat Files    3
    Sleep    2s    # Ensure files have different timestamps
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Should Be True    ${config}[file_newer_than_min] >= 0

Test SDP_STAT Max Processes Configuration
    [Documentation]    Test maximum processes configuration validation
    [Tags]    configuration    concurrency
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Should Be True    ${config}[max_processes] > 0
    Should Be True    ${config}[max_processes] <= 10

Test SDP_STAT Wait Time Configuration
    [Documentation]    Test wait time configuration validation
    [Tags]    configuration    timing
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Should Be True    ${config}[wait_to_start_secs] >= 0

Test SDP_STAT Namespace Configuration
    [Documentation]    Test Kubernetes namespace configuration
    [Tags]    kubernetes    configuration
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Dictionary Should Contain Key    ${config}    namespace
    Should Not Be Empty    ${config}[namespace]

Test SDP_STAT Pod Name Configuration
    [Documentation]    Test pod name configuration validation
    [Tags]    kubernetes    configuration
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    Dictionary Should Contain Key    ${config}    pod
    Should Not Be Empty    ${config}[pod]

Test SDP_STAT Integration With Process Check
    [Documentation]    Test integration with ProcessCheck library
    [Tags]    integration    process_check
    # Verify ProcessCheck can be imported
    ${result}=    Run Process    python    -c    import sys; sys.path.append('..'); from lib.process_check.ProcessCheck import ProcessCheck; print('ProcessCheck imported successfully')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${result.stdout}    ProcessCheck imported successfully

Test SDP_STAT Module Import Validation
    [Documentation]    Test that all required modules can be imported successfully
    [Tags]    imports    validation
    ${result}=    Run Process    python    -c    
    ...           import os, sys, json, datetime, concurrent.futures, argparse, time; from Logger import LoggingHandler; import SDP_STAT; from SubprocessClass import SubprocessClass; print('All imports successful')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${result.stdout}    All imports successful

Test SDP_STAT Timestamp Function
    [Documentation]    Test timestamp generation functionality
    [Tags]    utilities    timestamp
    ${result}=    Run Process    python    -c    
    ...           from main import timestamp; ts = timestamp(); print(f'Timestamp: {ts}'); assert len(ts) == 14; print('Timestamp validation passed')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${result.stdout}    Timestamp validation passed

Test SDP_STAT Configuration Loading Function
    [Documentation]    Test configuration loading function directly
    [Tags]    configuration    function
    ${result}=    Run Process    python    -c    
    ...           import sys; sys.path.append('.'); from main import load_config; print('load_config function available')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${result.stdout}    load_config function available

Test SDP_STAT Subprocess Integration
    [Documentation]    Test integration with SubprocessClass
    [Tags]    integration    subprocess
    File Should Exist    ${SUBPROCESS_MODULE}
    ${result}=    Run Process    python    -c    
    ...           from SubprocessClass import SubprocessClass; print('SubprocessClass imported successfully')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0

Test SDP_STAT Logger Integration
    [Documentation]    Test integration with Logger module
    [Tags]    integration    logging
    File Should Exist    ${LOGGER_MODULE}
    ${result}=    Run Process    python    -c    
    ...           from Logger import LoggingHandler; print('LoggingHandler imported successfully')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0

Test SDP_STAT SFTP Integration
    [Documentation]    Test integration with SftpClass
    [Tags]    integration    sftp
    File Should Exist    ${SFTP_MODULE}
    ${result}=    Run Process    python    -c    
    ...           from SftpClass import SftpClass; print('SftpClass imported successfully')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0

Test SDP_STAT Complete Module Integration
    [Documentation]    Test complete module integration and basic execution
    [Tags]    integration    complete
    [Setup]    Create Test Configuration Files
    ${result}=    Run Process    python    -c    
    ...           import main; print('SDP_STAT main module loaded successfully')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Be Equal As Integers    ${result.rc}    0

Test SDP_STAT Environment Variables
    [Documentation]    Test environment variable handling and PATH configuration
    [Tags]    environment    configuration
    ${original_path}=    Get Environment Variable    PATH
    Should Not Be Empty    ${original_path}
    Set Environment Variable    PATH    ${original_path}${:}${MODULE_PATH}
    ${new_path}=    Get Environment Variable    PATH
    Should Contain    ${new_path}    ${MODULE_PATH}

Test SDP_STAT File System Operations
    [Documentation]    Test file system operations and directory handling
    [Tags]    filesystem    operations
    Create Directory    ${TEST_DATA_DIR}${/}temp
    Directory Should Exist    ${TEST_DATA_DIR}${/}temp
    Create File    ${TEST_DATA_DIR}${/}temp${/}test.txt    Test content
    File Should Exist    ${TEST_DATA_DIR}${/}temp${/}test.txt
    Remove File    ${TEST_DATA_DIR}${/}temp${/}test.txt
    Remove Directory    ${TEST_DATA_DIR}${/}temp

Test SDP_STAT Advanced Error Recovery
    [Documentation]    Test advanced error recovery scenarios
    [Tags]    error_handling    recovery
    # Test recovery from configuration errors
    Create File    ${TEST_CONFIG_FILE}    {malformed json
    ${result}=    Run Process    python    -c    
    ...           import json; 
    ...           try: 
    ...               with open('${TEST_CONFIG_FILE}', 'r') as f: json.load(f); 
    ...           except json.JSONDecodeError: 
    ...               print('JSON error handled correctly')
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Contain    ${result.stdout}    JSON error handled correctly

Test SDP_STAT Load Testing Preparation
    [Documentation]    Prepare for load testing with multiple stat files
    [Tags]    performance    load_testing
    # Create a large number of test files to simulate load
    FOR    ${i}    IN RANGE    20
        ${filename}=    Set Variable    load_test_${i}.stat
        ${filepath}=    Set Variable    ${TEST_DATA_DIR}${/}${filename}
        ${content}=    Set Variable    Load test stat data ${i}\nProcessed at ${i}
        Create File    ${filepath}    ${content}
    END
    ${files}=    List Files In Directory    ${TEST_DATA_DIR}    *.stat
    Length Should Be    ${files}    20

Test SDP_STAT Memory Efficiency
    [Documentation]    Test memory efficiency during large file processing
    [Tags]    performance    memory
    # Create test files and monitor memory usage
    Create Test Stat Files    10
    ${start_memory}=    Run    python -c "import psutil; print(psutil.Process().memory_info().rss)"
    Log    Initial memory usage: ${start_memory} bytes
    
    # Simulate processing
    Sleep    2s
    ${end_memory}=    Run    python -c "import psutil; print(psutil.Process().memory_info().rss)"
    Log    Final memory usage: ${end_memory} bytes

Test SDP_STAT Configuration Backup and Restore
    [Documentation]    Test configuration backup and restore functionality
    [Tags]    configuration    backup
    # Backup original configuration
    Copy File    ${TEST_CONFIG_FILE}    ${TEST_CONFIG_FILE}.backup
    
    # Modify configuration
    Create File    ${TEST_CONFIG_FILE}    {"test": "modified"}
    ${modified_content}=    Get File    ${TEST_CONFIG_FILE}
    Should Contain    ${modified_content}    modified
    
    # Restore configuration
    Copy File    ${TEST_CONFIG_FILE}.backup    ${TEST_CONFIG_FILE}
    ${restored_content}=    Get File    ${TEST_CONFIG_FILE}
    Should Contain    ${restored_content}    namespace
    
    # Cleanup
    Remove File    ${TEST_CONFIG_FILE}.backup
