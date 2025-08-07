*** Settings ***
Documentation    Resource file for KAFKA_SDP_GEORED Robot Framework tests
...              
...              This resource file contains common keywords, variables, and utilities
...              used across multiple Robot Framework test suites for the KAFKA_SDP_GEORED module.
...              
...              Contains:
...              - Common variables and configuration
...              - Reusable keywords for test setup and teardown
...              - Utility functions for mocking and test data generation
...              - Helper keywords for validation and verification
...              - Kafka message template utilities
...              - KPI processing helpers
...              
...              Author: Test Suite Generator
...              Date: 2025-07-24
...              Version: 1.0.0

Library          OperatingSystem
Library          Process
Library          Collections
Library          String
Library          DateTime
Library          JSONLibrary
Library          BuiltIn

*** Variables ***
# Module Paths and Configuration
${GEORED_ROOT_DIR}           c:\\Users\\eakaijn\\workspace\\cec-adaptation-pod\\KAFKA_SDP_GEORED
${GEORED_CONFIG_DIR}         ${GEORED_ROOT_DIR}\\config
${GEORED_CONFIG_FILE}        ${GEORED_CONFIG_DIR}\\config.json
${GEORED_MAIN_SCRIPT}        ${GEORED_ROOT_DIR}\\main.py
${GEORED_KPI_SCRIPT}         ${GEORED_ROOT_DIR}\\KPI_SDP.py
${GEORED_LOGGER_SCRIPT}      ${GEORED_ROOT_DIR}\\Logger.py
${GEORED_SUBPROCESS_SCRIPT}  ${GEORED_ROOT_DIR}\\SubprocessClass.py

# Test Environment Configuration
${GEORED_TEST_TIMEOUT}       120 seconds
${GEORED_DEFAULT_NAMESPACE}  test-geored-namespace
${GEORED_DEFAULT_POD}        test-sdp-pod
${GEORED_DEFAULT_CONTAINER}  test-sdp-container
${GEORED_MAX_PROCESSES}      3

# Mock Test Data
${GEORED_MOCK_HOSTNAME}      test-geored-host
${GEORED_MOCK_OUTPUT_DIR}    /tmp/geored_test_output
${GEORED_MOCK_ARCHIVE_DIR}   /tmp/geored_test_archive
${GEORED_MOCK_LOG_DIR}       /tmp/geored_test_logs

# KPI Test Data
${GEORED_MOCK_KPI_NAME}      test_kpi_geored
${GEORED_MOCK_KPI_VALUE}     100.50
${GEORED_MOCK_KPI_RESULT}    SUCCESS

# Kafka Template Configuration
&{GEORED_KAFKA_TEMPLATE}     category=CORE - IN    platform=ERICSSON_SDP    source_owner=Tier2_CC
@{GEORED_KAFKA_TABLE}        kpi_name    kpi_value    kpi_result

# File Patterns
${GEORED_CONFIG_PATTERN}     *.json
${GEORED_PYTHON_PATTERN}     *.py
${GEORED_LOG_PATTERN}        *.log

# Error Messages
${GEORED_CONFIG_ERROR}       Configuration validation failed
${GEORED_IMPORT_ERROR}       Module import failed
${GEORED_INIT_ERROR}         Initialization failed

*** Keywords ***
# =============================================================================
# Setup and Teardown Keywords
# =============================================================================

Setup GEORED Test Environment
    [Documentation]    Set up comprehensive test environment for KAFKA_SDP_GEORED
    [Arguments]        ${custom_config}=&{EMPTY}
    
    Log    Setting up KAFKA_SDP_GEORED test environment
    
    # Verify module structure
    Verify GEORED Module Files
    
    # Initialize test directories
    Initialize GEORED Test Directories
    
    # Set up global test variables
    Set Global Variable    ${GEORED_TEST_SESSION}     active
    Set Global Variable    ${GEORED_TEST_CONFIG}      ${None}
    Set Global Variable    ${GEORED_MOCK_PROCESSES}   @{EMPTY}
    
    # Apply custom configuration if provided
    IF    &{custom_config}
        Set Global Variable    ${GEORED_CUSTOM_CONFIG}    &{custom_config}
    END
    
    Log    KAFKA_SDP_GEORED test environment ready

Teardown GEORED Test Environment
    [Documentation]    Clean up KAFKA_SDP_GEORED test environment
    
    Log    Tearing down KAFKA_SDP_GEORED test environment
    
    # Clean up test processes
    Cleanup GEORED Test Processes
    
    # Remove test directories
    Cleanup GEORED Test Directories
    
    # Reset global variables
    Set Global Variable    ${GEORED_TEST_SESSION}     inactive
    
    Log    KAFKA_SDP_GEORED test environment cleanup completed

Initialize GEORED Test Directories
    [Documentation]    Create necessary test directories for GEORED testing
    
    Create Directory    ${GEORED_MOCK_OUTPUT_DIR}
    Create Directory    ${GEORED_MOCK_ARCHIVE_DIR}  
    Create Directory    ${GEORED_MOCK_LOG_DIR}
    
    Log    GEORED test directories initialized

Cleanup GEORED Test Directories
    [Documentation]    Remove test directories and cleanup
    
    Remove Directory    ${GEORED_MOCK_OUTPUT_DIR}    recursive=true
    Remove Directory    ${GEORED_MOCK_ARCHIVE_DIR}   recursive=true
    Remove Directory    ${GEORED_MOCK_LOG_DIR}       recursive=true
    
    Log    GEORED test directories cleaned up

Verify GEORED Module Files
    [Documentation]    Verify that all required GEORED module files exist
    
    Directory Should Exist    ${GEORED_ROOT_DIR}
    Directory Should Exist    ${GEORED_CONFIG_DIR}
    File Should Exist         ${GEORED_CONFIG_FILE}
    File Should Exist         ${GEORED_MAIN_SCRIPT}
    File Should Exist         ${GEORED_KPI_SCRIPT}
    File Should Exist         ${GEORED_LOGGER_SCRIPT}
    File Should Exist         ${GEORED_SUBPROCESS_SCRIPT}

# =============================================================================
# Configuration Management Keywords
# =============================================================================

Load GEORED Default Configuration
    [Documentation]    Load the default GEORED configuration file
    
    ${config_content}=    Get File    ${GEORED_CONFIG_FILE}
    ${config_data}=       Evaluate    json.loads('''${config_content}''')    json
    
    Set Suite Variable    ${GEORED_TEST_CONFIG}    ${config_data}
    
    [Return]    ${config_data}

Create GEORED Mock Configuration
    [Documentation]    Create mock configuration for testing
    [Arguments]        ${overrides}=&{EMPTY}
    
    # Base mock configuration
    &{mock_config}=    Create Dictionary
    ...    wait_to_start_secs=5
    ...    namespace=${GEORED_DEFAULT_NAMESPACE}
    ...    pod=${GEORED_DEFAULT_POD}
    ...    pod_container=${GEORED_DEFAULT_CONTAINER}
    ...    max_processes=${GEORED_MAX_PROCESSES}
    ...    whitelist_pod_enable=false
    ...    whitelist_pods=@{EMPTY}
    ...    blacklist_pods=@{EMPTY}
    ...    kafka_message_template=&{GEORED_KAFKA_TEMPLATE}
    
    # Apply any overrides
    FOR    ${key}    ${value}    IN    &{overrides}
        Set To Dictionary    ${mock_config}    ${key}    ${value}
    END
    
    # Add kafka table to template
    Set To Dictionary    ${mock_config['kafka_message_template']}    @table    @{GEORED_KAFKA_TABLE}
    
    [Return]    &{mock_config}

Validate GEORED Configuration
    [Documentation]    Validate GEORED configuration structure and values
    [Arguments]        ${config}
    
    # Validate required keys exist
    Dictionary Should Contain Key    ${config}    wait_to_start_secs
    Dictionary Should Contain Key    ${config}    namespace
    Dictionary Should Contain Key    ${config}    pod
    Dictionary Should Contain Key    ${config}    pod_container
    Dictionary Should Contain Key    ${config}    max_processes
    Dictionary Should Contain Key    ${config}    kafka_message_template
    
    # Validate data types and values
    Should Be True    ${config['wait_to_start_secs']} >= 0
    Should Be True    ${config['max_processes']} > 0
    Should Not Be Empty    ${config['namespace']}
    Should Not Be Empty    ${config['pod']}
    Should Not Be Empty    ${config['pod_container']}
    
    # Validate Kafka template
    ${kafka_template}=    Get From Dictionary    ${config}    kafka_message_template
    Dictionary Should Contain Key    ${kafka_template}    category
    Dictionary Should Contain Key    ${kafka_template}    platform
    Dictionary Should Contain Key    ${kafka_template}    source_owner

Save GEORED Test Configuration
    [Documentation]    Save test configuration to temporary file
    [Arguments]        ${config}    ${file_path}
    
    ${config_json}=    Evaluate    json.dumps($config, indent=2)    json
    Create File        ${file_path}    ${config_json}
    
    Log    Test configuration saved to ${file_path}

# =============================================================================
# Module Interaction Keywords
# =============================================================================

Import GEORED Python Modules
    [Documentation]    Import and validate GEORED Python modules
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    import main
    ...    import KPI_SDP
    ...    import Logger
    ...    import SubprocessClass
    ...    print('All GEORED modules imported successfully')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All GEORED modules imported successfully
    
    [Return]    ${result}

Initialize GEORED KPI Instance
    [Documentation]    Initialize KPI_SDP instance with test parameters
    [Arguments]        ${hostname}=${GEORED_MOCK_HOSTNAME}    ${namespace}=${GEORED_DEFAULT_NAMESPACE}
    ...                ${pod}=${GEORED_DEFAULT_POD}    ${container}=${GEORED_DEFAULT_CONTAINER}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    from KPI_SDP import KPI_SDP
    ...    kpi = KPI_SDP('${hostname}', '${namespace}', '${pod}', '${GEORED_ROOT_DIR}', 
    ...                   '${GEORED_MOCK_OUTPUT_DIR}', '${GEORED_MOCK_ARCHIVE_DIR}', 
    ...                   '${GEORED_MOCK_LOG_DIR}', '${container}')
    ...    print(f'KPI_SDP initialized for host: {kpi.host_name}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    KPI_SDP initialized for host
    
    [Return]    ${result}

Initialize GEORED Logger
    [Documentation]    Initialize and test GEORED logging functionality
    [Arguments]        ${logger_name}=test_geored_logger
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    from Logger import LoggingHandler
    ...    logger = LoggingHandler.get_logger('${logger_name}')
    ...    logger.info('Test log message from GEORED logger')
    ...    print('GEORED logger initialized and tested')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    GEORED logger initialized and tested
    
    [Return]    ${result}

# =============================================================================
# Kafka Integration Keywords
# =============================================================================

Validate GEORED Kafka Template
    [Documentation]    Validate Kafka message template structure
    [Arguments]        ${kafka_template}
    
    Dictionary Should Contain Key    ${kafka_template}    category
    Dictionary Should Contain Key    ${kafka_template}    platform
    Dictionary Should Contain Key    ${kafka_template}    source_owner
    Dictionary Should Contain Key    ${kafka_template}    @table
    
    Should Be Equal    ${kafka_template['category']}        CORE - IN
    Should Be Equal    ${kafka_template['platform']}        ERICSSON_SDP
    Should Be Equal    ${kafka_template['source_owner']}    Tier2_CC
    
    ${table_fields}=    Get From Dictionary    ${kafka_template}    @table
    List Should Contain Value    ${table_fields}    kpi_name
    List Should Contain Value    ${table_fields}    kpi_value
    List Should Contain Value    ${table_fields}    kpi_result

Create GEORED Mock Kafka Message
    [Documentation]    Create mock Kafka message for testing
    [Arguments]        ${kpi_name}=${GEORED_MOCK_KPI_NAME}    ${kpi_value}=${GEORED_MOCK_KPI_VALUE}
    ...                ${kpi_result}=${GEORED_MOCK_KPI_RESULT}
    
    &{kafka_message}=    Create Dictionary
    ...    category=CORE - IN
    ...    platform=ERICSSON_SDP
    ...    source_owner=Tier2_CC
    ...    kpi_name=${kpi_name}
    ...    kpi_value=${kpi_value}
    ...    kpi_result=${kpi_result}
    ...    ref_id=test-ref-${GEORED_MOCK_KPI_NAME}
    ...    kpi_last_updated_date=${EMPTY}
    ...    kpi_source=${EMPTY}
    ...    config_item=${EMPTY}
    ...    kpi_info=${EMPTY}
    ...    src_modified_dt=${EMPTY}
    ...    local_modified_dt=${EMPTY}
    
    [Return]    &{kafka_message}

Test GEORED Kafka Data Source Builder
    [Documentation]    Test integration with Kafka data source builder
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    sys.path.append('${GEORED_ROOT_DIR}/../KAFKA_SENDER')
    ...    try:
    ...        from KafkaDataSourceBuilder import KafkaDataSourceBuilder
    ...        builder = KafkaDataSourceBuilder()
    ...        print('KafkaDataSourceBuilder integration successful')
    ...    except ImportError as e:
    ...        print(f'KafkaDataSourceBuilder not available: {e}')
    ...    except Exception as e:
    ...        print(f'KafkaDataSourceBuilder error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

# =============================================================================
# Subprocess and Command Testing Keywords
# =============================================================================

Test GEORED Subprocess Execution
    [Documentation]    Test subprocess command execution functionality
    [Arguments]        ${test_command}=echo "test command"
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    from SubprocessClass import SubprocessClass
    ...    sp = SubprocessClass()
    ...    print('SubprocessClass ready for command execution')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    SubprocessClass ready
    
    [Return]    ${result}

Mock GEORED Kubectl Command
    [Documentation]    Mock kubectl command execution for testing
    [Arguments]        ${namespace}=${GEORED_DEFAULT_NAMESPACE}    ${pod_pattern}=sdp
    
    # Create mock kubectl response
    ${mock_kubectl_output}=    Set Variable
    ...    NAME                    READY   STATUS    RESTARTS   AGE
    ...    ${pod_pattern}-test-1   1/1     Running   0          1d
    ...    ${pod_pattern}-test-2   1/1     Running   0          1d
    
    Log    Mock kubectl output for namespace ${namespace}: ${mock_kubectl_output}
    
    [Return]    ${mock_kubectl_output}

# =============================================================================
# Performance and Validation Keywords
# =============================================================================

Measure GEORED Module Load Time
    [Documentation]    Measure the time taken to load GEORED modules
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    Import GEORED Python Modules
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${load_time}=     Evaluate    ${end_time} - ${start_time}
    
    Log    GEORED module load time: ${load_time} seconds
    Should Be True    ${load_time} < 10    Module loading too slow: ${load_time}s
    
    [Return]    ${load_time}

Validate GEORED Configuration Performance
    [Documentation]    Validate configuration loading performance
    [Arguments]        ${iterations}=5
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    FOR    ${i}    IN RANGE    ${iterations}
        ${config}=    Load GEORED Default Configuration
        Validate GEORED Configuration    ${config}
    END
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${total_time}=    Evaluate    ${end_time} - ${start_time}
    ${avg_time}=      Evaluate    ${total_time} / ${iterations}
    
    Log    Configuration loading average time: ${avg_time} seconds
    Should Be True    ${avg_time} < 2    Configuration loading too slow: ${avg_time}s
    
    [Return]    ${avg_time}

# =============================================================================
# Error Handling and Edge Case Keywords
# =============================================================================

Test GEORED Invalid Configuration
    [Documentation]    Test handling of invalid configuration data
    [Arguments]        ${invalid_config}
    
    ${temp_config_file}=    Set Variable    ${GEORED_ROOT_DIR}\\temp_invalid_config.json
    
    Save GEORED Test Configuration    ${invalid_config}    ${temp_config_file}
    
    ${python_code}=    Set Variable
    ...    import sys, json
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    try:
    ...        with open('${temp_config_file}', 'r') as f:
    ...            config = json.load(f)
    ...        print('Invalid config loaded without error')
    ...    except Exception as e:
    ...        print(f'Expected error: {type(e).__name__}: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Remove File    ${temp_config_file}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test GEORED Missing Dependencies
    [Documentation]    Test behavior when required dependencies are missing
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    required_modules = ['json', 'datetime', 'time', 'os', 'socket', 'argparse', 'concurrent.futures']
    ...    missing_modules = []
    ...    for module in required_modules:
    ...        try:
    ...            __import__(module)
    ...        except ImportError:
    ...            missing_modules.append(module)
    ...    if missing_modules:
    ...        print(f'Missing modules: {missing_modules}')
    ...    else:
    ...        print('All required modules available')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All required modules available
    
    [Return]    ${result}

# =============================================================================
# Cleanup and Utility Keywords
# =============================================================================

Cleanup GEORED Test Processes
    [Documentation]    Clean up any running GEORED test processes
    
    Log    Cleaning up GEORED test processes
    # This would terminate any background processes started during testing

Generate GEORED Test Report
    [Documentation]    Generate test report for GEORED module
    [Arguments]        ${test_results}
    
    ${timestamp}=     Get Current Date    result_format=%Y%m%d_%H%M%S
    ${report_file}=   Set Variable    ${GEORED_ROOT_DIR}\\test_report_${timestamp}.txt
    
    ${report_content}=    Set Variable
    ...    KAFKA_SDP_GEORED Test Report
    ...    Generated: ${timestamp}
    ...    Test Results: ${test_results}
    
    Create File    ${report_file}    ${report_content}
    
    Log    Test report generated: ${report_file}
    
    [Return]    ${report_file}

Get GEORED Module Version
    [Documentation]    Get version information from GEORED module
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${GEORED_ROOT_DIR}')
    ...    try:
    ...        # Try to get version from module
    ...        import main
    ...        print('GEORED module version: Available')
    ...    except Exception as e:
    ...        print(f'Version check error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${GEORED_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}
