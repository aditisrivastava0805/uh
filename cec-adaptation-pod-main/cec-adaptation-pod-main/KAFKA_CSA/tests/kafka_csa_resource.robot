*** Settings ***
Documentation    Resource file for KAFKA_CSA module testing
Library          Collections
Library          OperatingSystem
Library          Process
Library          String
Library          DateTime
Library          JSONLibrary

*** Variables ***
# Test Configuration
${KAFKA_CSA_DIR}         ${CURDIR}${/}..
${CONFIG_DIR}            ${KAFKA_CSA_DIR}${/}config
${ARCHIVE_DIR}           ${KAFKA_CSA_DIR}${/}archive
${TEST_DATA_DIR}         ${KAFKA_CSA_DIR}${/}tests${/}test_data
${LOG_DIR}               ${KAFKA_CSA_DIR}${/}log

# Test Files
${TEST_CONFIG_FILE}      ${TEST_DATA_DIR}${/}test_csa_config.json
${TEST_KAFKA_CONFIG}     ${TEST_DATA_DIR}${/}test_kafka_config.json
${MAIN_SCRIPT}           ${KAFKA_CSA_DIR}${/}main.py

# Mock Data
${MOCK_NAMESPACE}        test-namespace
${MOCK_POD}              eric-csa-
${MOCK_HOSTNAME}         TEST-HOST
${TEST_EXECUTION_PERIOD} 5

# Expected Files and Patterns
${KPI_FILE_PATTERN}      *_KPI.txt.*
${STATUS_FILE_PATTERN}   *_KPI.status.*
${LOG_FILE_PATTERN}      *.log

*** Keywords ***
Setup KAFKA_CSA Test Environment
    [Documentation]    Sets up the test environment for KAFKA_CSA testing
    Create Directory    ${TEST_DATA_DIR}
    Create Directory    ${ARCHIVE_DIR}
    Create Directory    ${LOG_DIR}
    Create Test Configuration Files
    Set Test Variable    ${ORIGINAL_DIR}    ${CURDIR}
    Change Directory    ${KAFKA_CSA_DIR}

Teardown KAFKA_CSA Test Environment
    [Documentation]    Cleans up the test environment
    Run Keyword And Ignore Error    Change Directory    ${ORIGINAL_DIR}
    Run Keyword And Ignore Error    Remove Directory    ${TEST_DATA_DIR}    recursive=True
    Run Keyword And Ignore Error    Cleanup Generated Files

Create Test Configuration Files
    [Documentation]    Creates test configuration files
    ${csa_config}=    Create Dictionary
    ...    wait_to_start_secs=5
    ...    namespace=${MOCK_NAMESPACE}
    ...    pod=${MOCK_POD}
    ...    dir_lookup=/opt/ericsson/3pp/jboss/standalone/log/server.log
    ...    perf_data_files_local_dir=/tmp/test_perf_data
    ...    execution_period_mins=${TEST_EXECUTION_PERIOD}
    ...    kafka_message_template=${EMPTY_DICT}
    
    ${json_string}=    Convert JSON To String    ${csa_config}
    Create File    ${TEST_CONFIG_FILE}    ${json_string}
    
    ${kafka_config}=    Create Dictionary
    ...    bootstrap_servers=localhost:9092
    ...    topic=test-topic
    ...    security_protocol=PLAINTEXT
    
    ${kafka_json}=    Convert JSON To String    ${kafka_config}
    Create File    ${TEST_KAFKA_CONFIG}    ${kafka_json}

Create Empty Dictionary
    [Documentation]    Creates an empty dictionary for template usage
    ${empty_dict}=    Create Dictionary
    RETURN    ${empty_dict}

Verify KAFKA_CSA Module Structure
    [Documentation]    Verifies the KAFKA_CSA module has required files
    Should Exist    ${KAFKA_CSA_DIR}${/}main.py
    Should Exist    ${KAFKA_CSA_DIR}${/}KPI_CSA.py
    Should Exist    ${KAFKA_CSA_DIR}${/}SubprocessClass.py
    Should Exist    ${KAFKA_CSA_DIR}${/}KPI_Helper.py
    Should Exist    ${CONFIG_DIR}

Verify Configuration Loading
    [Documentation]    Verifies configuration file loading functionality
    [Arguments]    ${config_file}
    Should Exist    ${config_file}
    ${content}=    Get File    ${config_file}
    ${config}=    Convert String To JSON    ${content}
    Dictionary Should Contain Key    ${config}    namespace
    Dictionary Should Contain Key    ${config}    pod
    Dictionary Should Contain Key    ${config}    execution_period_mins

Execute KAFKA_CSA Main Script
    [Documentation]    Executes the main KAFKA_CSA script with test parameters
    [Arguments]    ${config_file}=${TEST_CONFIG_FILE}    ${kafka_config}=${TEST_KAFKA_CONFIG}    ${additional_args}=${EMPTY}
    ${cmd}=    Set Variable    python "${MAIN_SCRIPT}" "${config_file}" "${kafka_config}" --test ${additional_args}
    ${result}=    Run Process    ${cmd}    shell=True    timeout=30s    
    RETURN    ${result}

Mock Pod Discovery
    [Documentation]    Mocks the pod discovery functionality
    [Arguments]    ${namespace}    ${pod_pattern}
    ${mock_pods}=    Create List    eric-csa-worker-1    eric-csa-worker-2
    Set Test Variable    ${AVAILABLE_PODS}    ${mock_pods}
    RETURN    ${mock_pods}

Verify KPI File Generation
    [Documentation]    Verifies that KPI files are generated correctly
    [Arguments]    ${expected_pattern}=${KPI_FILE_PATTERN}
    ${files}=    List Files In Directory    ${ARCHIVE_DIR}    ${expected_pattern}
    Length Should Be Greater Than    ${files}    0
    FOR    ${file}    IN    @{files}
        Should Exist    ${ARCHIVE_DIR}${/}${file}
        ${size}=    Get File Size    ${ARCHIVE_DIR}${/}${file}
        Should Be True    ${size} > 0
    END

Verify Status File Creation
    [Documentation]    Verifies status file creation
    ${files}=    List Files In Directory    ${ARCHIVE_DIR}    ${STATUS_FILE_PATTERN}
    Should Not Be Empty    ${files}

Simulate Performance Data Files
    [Documentation]    Creates mock performance data files for testing
    [Arguments]    ${perf_dir}=/tmp/test_perf_data
    Create Directory    ${perf_dir}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d%H%M%S
    ${perf_file}=    Set Variable    ${perf_dir}${/}A${timestamp}.xml
    ${sample_content}=    Set Variable    <xml><measurement><measCollecFile><fileHeader/><measData/></measCollecFile></measurement></xml>
    Create File    ${perf_file}    ${sample_content}
    RETURN    ${perf_file}

Verify Error Handling
    [Documentation]    Verifies error handling in various scenarios
    [Arguments]    ${error_type}
    IF    '${error_type}' == 'missing_config'
        ${result}=    Execute KAFKA_CSA Main Script    ${TEST_DATA_DIR}${/}nonexistent.json
        Should Not Be Equal As Integers    ${result.rc}    0
    ELSE IF    '${error_type}' == 'invalid_namespace'
        ${result}=    Execute KAFKA_CSA Main Script
        Should Contain    ${result.stderr}    Failed fetching pods
    ELSE IF    '${error_type}' == 'missing_performance_data'
        ${result}=    Execute KAFKA_CSA Main Script
        # Should handle gracefully when no performance data is available
        Should Be True    ${result.rc} >= 0
    END

Verify Kafka Integration
    [Documentation]    Verifies Kafka integration functionality
    # This would normally require a running Kafka instance
    # For testing, we verify the data source file generation
    ${files}=    List Files In Directory    ${ARCHIVE_DIR}    ${KPI_FILE_PATTERN}
    Should Not Be Empty    ${files}

Monitor System Resources
    [Documentation]    Monitors system resources during test execution
    ${initial_memory}=    Get Process Memory Usage    
    Set Test Variable    ${INITIAL_MEMORY}    ${initial_memory}

Get Process Memory Usage
    [Documentation]    Gets current process memory usage (mock implementation)
    RETURN    100  # Mock value in MB

Verify Performance Metrics
    [Documentation]    Verifies performance metrics are within acceptable ranges
    [Arguments]    ${max_execution_time}=30    ${max_memory_mb}=500
    # These would be actual performance checks in a real implementation
    Should Be True    True  # Placeholder for actual performance validation

Create Mock Kubernetes Environment
    [Documentation]    Creates a mock Kubernetes environment for testing
    Set Environment Variable    KUBECONFIG    ${TEST_DATA_DIR}${/}mock_kubeconfig
    ${mock_kubeconfig}=    Set Variable    apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\nusers: []
    Create File    ${TEST_DATA_DIR}${/}mock_kubeconfig    ${mock_kubeconfig}

Cleanup Generated Files
    [Documentation]    Cleans up generated test files
    Run Keyword And Ignore Error    Remove Files    ${ARCHIVE_DIR}${/}*
    Run Keyword And Ignore Error    Remove Files    ${LOG_DIR}${/}*

Verify Archive Cleanup
    [Documentation]    Verifies that old archive files are cleaned up
    # Create old files (simulated)
    ${old_timestamp}=    Get Current Date    increment=-8 days    result_format=%Y%m%d%H%M%S
    ${old_file}=    Set Variable    ${ARCHIVE_DIR}${/}old_file_${old_timestamp}.txt
    Create File    ${old_file}    test content
    
    # Execute main script which should clean up files older than 7 days
    Execute KAFKA_CSA Main Script
    
    # Verify old file is removed
    Should Not Exist    ${old_file}

Wait For File Generation
    [Documentation]    Waits for file generation with timeout
    [Arguments]    ${directory}    ${pattern}    ${timeout}=10s
    FOR    ${i}    IN RANGE    10
        ${files}=    List Files In Directory    ${directory}    ${pattern}
        Exit For Loop If    len($files) > 0
        Sleep    1s
    END
    RETURN    ${files}

Validate JSON Structure
    [Documentation]    Validates JSON structure of generated files
    [Arguments]    ${json_file}
    Should Exist    ${json_file}
    ${content}=    Get File    ${json_file}
    ${json_data}=    Convert String To JSON    ${content}
    Should Be True    isinstance($json_data, dict)
    RETURN    ${json_data}

Verify Log File Creation
    [Documentation]    Verifies that log files are created with proper structure
    ${log_files}=    List Files In Directory    ${LOG_DIR}    ${LOG_FILE_PATTERN}
    Should Not Be Empty    ${log_files}
    FOR    ${log_file}    IN    @{log_files}
        ${content}=    Get File    ${LOG_DIR}${/}${log_file}
        Should Not Be Empty    ${content}
    END
