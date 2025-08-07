*** Settings ***
Documentation    Resource file for SDP_STAT module tests providing keywords and variables
Library          Collections
Library          OperatingSystem
Library          String
Library          DateTime
Library          Process
Library          JSONLibrary

*** Variables ***
# Test configuration paths
${MODULE_PATH}              ${CURDIR}${/}..
${CONFIG_PATH}              ${MODULE_PATH}${/}config
${TEST_CONFIG_FILE}         ${CONFIG_PATH}${/}test_config.json
${TEST_LOGGER_CONFIG}       ${CONFIG_PATH}${/}test_logger_config.json

# Test data directories
${TEST_DATA_DIR}            ${MODULE_PATH}${/}tests${/}test_data
${TEST_OUTPUT_DIR}          ${MODULE_PATH}${/}tests${/}test_output
${TEST_LOGS_DIR}            ${MODULE_PATH}${/}tests${/}test_logs

# SDP_STAT specific variables
${SDP_STAT_SCRIPT}          ${MODULE_PATH}${/}main.py
${SDP_STAT_MODULE}          ${MODULE_PATH}${/}SDP_STAT.py
${LOGGER_MODULE}            ${MODULE_PATH}${/}Logger.py
${SFTP_MODULE}              ${MODULE_PATH}${/}SftpClass.py
${SUBPROCESS_MODULE}        ${MODULE_PATH}${/}SubprocessClass.py

# Test configuration templates
${BASIC_CONFIG}             {
...                             "namespace": "test-namespace",
...                             "wait_to_start_secs": 10,
...                             "pod": "test-pod",
...                             "file_newer_than_min": 5,
...                             "max_processes": 2,
...                             "whitelist_pod_enable": false,
...                             "whitelist_pods": [],
...                             "splunk": {
...                                 "splunk_user_group": "test-group",
...                                 "splunk_container": "test-container"
...                             },
...                             "sftp": {
...                                 "user": "test-user",
...                                 "password": "test-password"
...                             },
...                             "dir_lookup": "/test/path",
...                             "blacklist_pods": []
...                         }

*** Keywords ***
Setup SDP_STAT Test Environment
    [Documentation]    Setup test environment for SDP_STAT tests
    Create Directory    ${TEST_DATA_DIR}
    Create Directory    ${TEST_OUTPUT_DIR}
    Create Directory    ${TEST_LOGS_DIR}
    Create Test Configuration Files
    Set Test Variable    ${ORIGINAL_PATH}    %{PATH}

Teardown SDP_STAT Test Environment
    [Documentation]    Clean up test environment after SDP_STAT tests
    Remove Directory    ${TEST_DATA_DIR}    recursive=True
    Remove Directory    ${TEST_OUTPUT_DIR}    recursive=True
    Remove Directory    ${TEST_LOGS_DIR}    recursive=True
    Set Environment Variable    PATH    ${ORIGINAL_PATH}

Create Test Configuration Files
    [Documentation]    Create test configuration files for SDP_STAT testing
    Create File    ${TEST_CONFIG_FILE}    ${BASIC_CONFIG}
    
    ${logger_config}=    Set Variable    {
    ...    "version": 1,
    ...    "handlers": {
    ...        "console": {
    ...            "class": "logging.StreamHandler",
    ...            "level": "INFO",
    ...            "formatter": "standard"
    ...        }
    ...    },
    ...    "formatters": {
    ...        "standard": {
    ...            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ...        }
    ...    },
    ...    "root": {
    ...        "level": "INFO",
    ...        "handlers": ["console"]
    ...    }
    ...}
    Create File    ${TEST_LOGGER_CONFIG}    ${logger_config}

Verify SDP_STAT Module Structure
    [Documentation]    Verify that all required SDP_STAT module files exist
    File Should Exist    ${SDP_STAT_SCRIPT}
    File Should Exist    ${SDP_STAT_MODULE}
    File Should Exist    ${LOGGER_MODULE}
    File Should Exist    ${SFTP_MODULE}
    File Should Exist    ${SUBPROCESS_MODULE}
    Directory Should Exist    ${CONFIG_PATH}

Verify Configuration Loading
    [Documentation]    Verify SDP_STAT configuration file loading
    [Arguments]    ${config_file}
    File Should Exist    ${config_file}
    ${config_content}=    Get File    ${config_file}
    ${json_valid}=    Run Keyword And Return Status    
    ...                Evaluate    json.loads('''${config_content}''')    json
    Should Be True    ${json_valid}    Configuration file should contain valid JSON

Verify SDP_STAT Configuration Parameters
    [Documentation]    Verify all required configuration parameters exist
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    
    Dictionary Should Contain Key    ${config}    namespace
    Dictionary Should Contain Key    ${config}    wait_to_start_secs
    Dictionary Should Contain Key    ${config}    pod
    Dictionary Should Contain Key    ${config}    file_newer_than_min
    Dictionary Should Contain Key    ${config}    max_processes
    Dictionary Should Contain Key    ${config}    whitelist_pod_enable
    Dictionary Should Contain Key    ${config}    splunk
    Dictionary Should Contain Key    ${config}    sftp
    Dictionary Should Contain Key    ${config}    dir_lookup

Verify Argument Parsing
    [Documentation]    Verify command line argument parsing
    [Arguments]    @{args}
    ${result}=    Run Process    python    ${SDP_STAT_SCRIPT}    --help
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Contain    ${result.stdout}    usage:
    Should Be Equal As Integers    ${result.rc}    0

Run SDP_STAT With Configuration
    [Documentation]    Run SDP_STAT with test configuration
    [Arguments]    ${config_file}=None    ${wait_flag}=False    ${timeout}=60s
    
    ${args}=    Create List    python    ${SDP_STAT_SCRIPT}
    Run Keyword If    ${wait_flag}    Append To List    ${args}    --wait
    
    ${result}=    Run Process    @{args}    cwd=${MODULE_PATH}    timeout=${timeout}
    [Return]    ${result}

Create Test Stat Files
    [Documentation]    Create test stat files for processing
    [Arguments]    ${count}=3
    FOR    ${i}    IN RANGE    ${count}
        ${filename}=    Set Variable    test_stat_${i}.txt
        ${filepath}=    Set Variable    ${TEST_DATA_DIR}${/}${filename}
        ${content}=    Set Variable    Test stat data ${i}\nTimestamp: ${i}
        Create File    ${filepath}    ${content}
    END

Verify Stat Processing
    [Documentation]    Verify stat file processing functionality
    Create Test Stat Files    5
    ${files}=    List Files In Directory    ${TEST_DATA_DIR}
    Length Should Be    ${files}    5
    FOR    ${file}    IN    @{files}
        File Should Exist    ${TEST_DATA_DIR}${/}${file}
    END

Verify SFTP Configuration
    [Documentation]    Verify SFTP configuration parameters
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    ${sftp_config}=    Get From Dictionary    ${config}    sftp
    
    Dictionary Should Contain Key    ${sftp_config}    user
    Dictionary Should Contain Key    ${sftp_config}    password
    Should Not Be Empty    ${sftp_config}[user]
    Should Not Be Empty    ${sftp_config}[password]

Verify Splunk Configuration
    [Documentation]    Verify Splunk configuration parameters
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    ${splunk_config}=    Get From Dictionary    ${config}    splunk
    
    Dictionary Should Contain Key    ${splunk_config}    splunk_user_group
    Dictionary Should Contain Key    ${splunk_config}    splunk_container
    Should Not Be Empty    ${splunk_config}[splunk_user_group]
    Should Not Be Empty    ${splunk_config}[splunk_container]

Simulate Error Condition
    [Documentation]    Simulate various error conditions
    [Arguments]    ${error_type}
    
    Run Keyword If    '${error_type}' == 'missing_config'
    ...               Remove File    ${TEST_CONFIG_FILE}
    Run Keyword If    '${error_type}' == 'invalid_json'
    ...               Create File    ${TEST_CONFIG_FILE}    {invalid json content
    Run Keyword If    '${error_type}' == 'missing_directory'
    ...               Remove Directory    ${TEST_DATA_DIR}    recursive=True

Verify Error Handling
    [Documentation]    Verify error handling for various failure scenarios
    [Arguments]    ${error_type}
    
    Simulate Error Condition    ${error_type}
    ${result}=    Run Process    python    ${SDP_STAT_SCRIPT}
    ...           cwd=${MODULE_PATH}    timeout=30s
    Should Not Be Equal As Integers    ${result.rc}    0

Verify Performance Metrics
    [Documentation]    Verify performance meets acceptable thresholds
    [Arguments]    ${max_execution_time}=120
    
    ${start_time}=    Get Current Date    result_format=epoch
    ${result}=    Run SDP_STAT With Configuration    timeout=180s
    ${end_time}=    Get Current Date    result_format=epoch
    ${execution_time}=    Evaluate    ${end_time} - ${start_time}
    
    Should Be True    ${execution_time} < ${max_execution_time}
    ...               Execution time should be under ${max_execution_time} seconds

Monitor System Resources
    [Documentation]    Monitor system resource usage during SDP_STAT execution
    ${start_memory}=    Run    python -c "import psutil; print(psutil.virtual_memory().percent)"
    ${start_cpu}=       Run    python -c "import psutil; print(psutil.cpu_percent())"
    
    ${result}=    Run SDP_STAT With Configuration    timeout=60s
    
    ${end_memory}=      Run    python -c "import psutil; print(psutil.virtual_memory().percent)"
    ${end_cpu}=         Run    python -c "import psutil; print(psutil.cpu_percent())"
    
    Log    Memory usage: ${start_memory}% -> ${end_memory}%
    Log    CPU usage: ${start_cpu}% -> ${end_cpu}%

Create Mock Pod Environment
    [Documentation]    Create mock Kubernetes pod environment for testing
    ${mock_pods}=    Create List    test-pod-1    test-pod-2    test-pod-3
    Set Test Variable    ${MOCK_PODS}    ${mock_pods}
    
    FOR    ${pod}    IN    @{mock_pods}
        ${pod_dir}=    Set Variable    ${TEST_DATA_DIR}${/}${pod}
        Create Directory    ${pod_dir}
        ${stat_file}=    Set Variable    ${pod_dir}${/}stat.txt
        Create File    ${stat_file}    Mock stat data for ${pod}
    END

Verify Pod Filtering
    [Documentation]    Verify pod whitelist/blacklist filtering functionality
    [Arguments]    ${filter_type}    ${pod_list}
    
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    ${config}=    Evaluate    json.loads('''${config_content}''')    json
    
    Run Keyword If    '${filter_type}' == 'whitelist'
    ...               Set To Dictionary    ${config}    whitelist_pod_enable=${True}
    Run Keyword If    '${filter_type}' == 'whitelist'
    ...               Set To Dictionary    ${config}    whitelist_pods=${pod_list}
    Run Keyword If    '${filter_type}' == 'blacklist'
    ...               Set To Dictionary    ${config}    blacklist_pods=${pod_list}
    
    ${updated_config}=    Evaluate    json.dumps(${config})    json
    Create File    ${TEST_CONFIG_FILE}    ${updated_config}

Verify Concurrent Processing
    [Documentation]    Verify concurrent processing capabilities
    Create Test Stat Files    10
    ${start_time}=    Get Current Date    result_format=epoch
    ${result}=    Run SDP_STAT With Configuration    timeout=180s
    ${end_time}=    Get Current Date    result_format=epoch
    ${execution_time}=    Evaluate    ${end_time} - ${start_time}
    
    Log    Concurrent processing completed in ${execution_time} seconds
    Should Be True    ${execution_time} < 120    Concurrent processing should complete within 2 minutes

Verify Security Measures
    [Documentation]    Verify security measures and credential handling
    ${config_content}=    Get File    ${TEST_CONFIG_FILE}
    Should Not Contain    ${config_content}    password    
    ...                   Configuration should not contain plaintext passwords in logs

Cleanup Test Environment
    [Documentation]    Cleanup test environment and temporary files
    Run Keyword And Ignore Error    Remove Directory    ${TEST_DATA_DIR}    recursive=True
    Run Keyword And Ignore Error    Remove Directory    ${TEST_OUTPUT_DIR}    recursive=True
    Run Keyword And Ignore Error    Remove Directory    ${TEST_LOGS_DIR}    recursive=True
    Run Keyword And Ignore Error    Remove File    ${TEST_CONFIG_FILE}
    Run Keyword And Ignore Error    Remove File    ${TEST_LOGGER_CONFIG}
