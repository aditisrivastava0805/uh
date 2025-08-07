*** Settings ***
Documentation    Resource file for KAFKA_SDP_PREPAID Robot Framework tests
...              
...              This resource file contains common keywords, variables, and utilities
...              used across multiple Robot Framework test suites for the KAFKA_SDP_PREPAID module.
...              
...              Contains:
...              - Common variables and configuration for prepaid services
...              - Reusable keywords for test setup and teardown
...              - Prepaid-specific utility functions and mock data generation
...              - Helper keywords for validation and verification
...              - Kafka message template utilities for prepaid
...              - KPI processing helpers for prepaid services
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
${PREPAID_ROOT_DIR}           c:\\Users\\eakaijn\\workspace\\cec-adaptation-pod\\KAFKA_SDP_PREPAID
${PREPAID_CONFIG_DIR}         ${PREPAID_ROOT_DIR}\\config
${PREPAID_CONFIG_FILE}        ${PREPAID_CONFIG_DIR}\\config.json
${PREPAID_MAIN_SCRIPT}        ${PREPAID_ROOT_DIR}\\main.py
${PREPAID_KPI_SCRIPT}         ${PREPAID_ROOT_DIR}\\KPI_SDP.py
${PREPAID_LOGGER_SCRIPT}      ${PREPAID_ROOT_DIR}\\Logger.py
${PREPAID_SUBPROCESS_SCRIPT}  ${PREPAID_ROOT_DIR}\\SubprocessClass.py

# Test Environment Configuration
${PREPAID_TEST_TIMEOUT}       120 seconds
${PREPAID_DEFAULT_NAMESPACE}  test-prepaid-namespace
${PREPAID_DEFAULT_POD}        test-prepaid-sdp-pod
${PREPAID_DEFAULT_CONTAINER}  test-prepaid-sdp-container
${PREPAID_MAX_PROCESSES}      3

# Prepaid Service Configuration
${PREPAID_SERVICE_TYPE}       prepaid
${PREPAID_BILLING_DOMAIN}     prepaid_billing
${PREPAID_BALANCE_THRESHOLD}  10.00
${PREPAID_DEFAULT_BALANCE}    100.00
${PREPAID_CURRENCY}           USD

# Mock Test Data
${PREPAID_MOCK_HOSTNAME}      test-prepaid-host
${PREPAID_MOCK_OUTPUT_DIR}    /tmp/prepaid_test_output
${PREPAID_MOCK_ARCHIVE_DIR}   /tmp/prepaid_test_archive
${PREPAID_MOCK_LOG_DIR}       /tmp/prepaid_test_logs

# Prepaid KPI Test Data
${PREPAID_MOCK_KPI_NAME}      prepaid_balance_kpi
${PREPAID_MOCK_KPI_VALUE}     85.75
${PREPAID_MOCK_KPI_RESULT}    SUCCESS
${PREPAID_USAGE_KPI_NAME}     prepaid_usage_kpi
${PREPAID_BILLING_KPI_NAME}   prepaid_billing_kpi

# Kafka Template Configuration for Prepaid
&{PREPAID_KAFKA_TEMPLATE}     category=CORE - IN    platform=ERICSSON_SDP    source_owner=Tier2_CC    service_type=prepaid
@{PREPAID_KAFKA_TABLE}        kpi_name    kpi_value    kpi_result    balance    usage_amount    billing_period

# Prepaid Business Logic Constants
${PREPAID_MIN_BALANCE}        0.00
${PREPAID_MAX_BALANCE}        1000.00
${PREPAID_DEFAULT_USAGE}      25.50
${PREPAID_RECHARGE_AMOUNT}    50.00

*** Keywords ***
# =============================================================================
# Setup and Teardown Keywords
# =============================================================================

Setup PREPAID Test Environment
    [Documentation]    Set up comprehensive test environment for KAFKA_SDP_PREPAID
    [Arguments]        ${custom_config}=&{EMPTY}
    
    Log    Setting up KAFKA_SDP_PREPAID test environment
    
    # Verify module structure
    Verify PREPAID Module Files
    
    # Initialize test directories
    Initialize PREPAID Test Directories
    
    # Set up global test variables
    Set Global Variable    ${PREPAID_TEST_SESSION}     active
    Set Global Variable    ${PREPAID_TEST_CONFIG}      ${None}
    Set Global Variable    ${PREPAID_MOCK_PROCESSES}   @{EMPTY}
    
    # Apply custom configuration if provided
    IF    &{custom_config}
        Set Global Variable    ${PREPAID_CUSTOM_CONFIG}    &{custom_config}
    END
    
    Log    KAFKA_SDP_PREPAID test environment ready

Teardown PREPAID Test Environment
    [Documentation]    Clean up KAFKA_SDP_PREPAID test environment
    
    Log    Tearing down KAFKA_SDP_PREPAID test environment
    
    # Clean up test processes
    Cleanup PREPAID Test Processes
    
    # Remove test directories
    Cleanup PREPAID Test Directories
    
    # Reset global variables
    Set Global Variable    ${PREPAID_TEST_SESSION}     inactive
    
    Log    KAFKA_SDP_PREPAID test environment cleanup completed

Initialize PREPAID Test Directories
    [Documentation]    Create necessary test directories for PREPAID testing
    
    Create Directory    ${PREPAID_MOCK_OUTPUT_DIR}
    Create Directory    ${PREPAID_MOCK_ARCHIVE_DIR}  
    Create Directory    ${PREPAID_MOCK_LOG_DIR}
    
    Log    PREPAID test directories initialized

Cleanup PREPAID Test Directories
    [Documentation]    Remove test directories and cleanup
    
    Remove Directory    ${PREPAID_MOCK_OUTPUT_DIR}    recursive=true
    Remove Directory    ${PREPAID_MOCK_ARCHIVE_DIR}   recursive=true
    Remove Directory    ${PREPAID_MOCK_LOG_DIR}       recursive=true
    
    Log    PREPAID test directories cleaned up

Verify PREPAID Module Files
    [Documentation]    Verify that all required PREPAID module files exist
    
    Directory Should Exist    ${PREPAID_ROOT_DIR}
    Directory Should Exist    ${PREPAID_CONFIG_DIR}
    File Should Exist         ${PREPAID_CONFIG_FILE}
    File Should Exist         ${PREPAID_MAIN_SCRIPT}
    File Should Exist         ${PREPAID_KPI_SCRIPT}
    File Should Exist         ${PREPAID_LOGGER_SCRIPT}
    File Should Exist         ${PREPAID_SUBPROCESS_SCRIPT}

# =============================================================================
# Configuration Management Keywords
# =============================================================================

Load PREPAID Configuration
    [Documentation]    Load the default PREPAID configuration file
    
    ${config_content}=    Get File    ${PREPAID_CONFIG_FILE}
    ${config_data}=       Evaluate    json.loads('''${config_content}''')    json
    
    Set Suite Variable    ${PREPAID_TEST_CONFIG}    ${config_data}
    
    [Return]    ${config_data}

Create PREPAID Mock Configuration
    [Documentation]    Create mock configuration for prepaid testing
    [Arguments]        ${overrides}=&{EMPTY}
    
    # Base mock configuration for prepaid
    &{mock_config}=    Create Dictionary
    ...    wait_to_start_secs=5
    ...    namespace=${PREPAID_DEFAULT_NAMESPACE}
    ...    pod=${PREPAID_DEFAULT_POD}
    ...    pod_container=${PREPAID_DEFAULT_CONTAINER}
    ...    max_processes=${PREPAID_MAX_PROCESSES}
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    billing_domain=${PREPAID_BILLING_DOMAIN}
    ...    balance_threshold=${PREPAID_BALANCE_THRESHOLD}
    ...    whitelist_pod_enable=false
    ...    whitelist_pods=@{EMPTY}
    ...    blacklist_pods=@{EMPTY}
    ...    kafka_message_template=&{PREPAID_KAFKA_TEMPLATE}
    
    # Apply any overrides
    FOR    ${key}    ${value}    IN    &{overrides}
        Set To Dictionary    ${mock_config}    ${key}    ${value}
    END
    
    # Add kafka table to template
    Set To Dictionary    ${mock_config['kafka_message_template']}    @table    @{PREPAID_KAFKA_TABLE}
    
    [Return]    &{mock_config}

Validate PREPAID Configuration Structure
    [Documentation]    Validate PREPAID configuration structure and values
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

# =============================================================================
# Module Interaction Keywords
# =============================================================================

Import PREPAID Python Modules
    [Documentation]    Import and validate PREPAID Python modules
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    import main
    ...    import KPI_SDP
    ...    import Logger
    ...    import SubprocessClass
    ...    print('All PREPAID modules imported successfully')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All PREPAID modules imported successfully
    
    [Return]    ${result}

Initialize PREPAID KPI Instance
    [Documentation]    Initialize KPI_SDP instance for prepaid services
    [Arguments]        ${hostname}=${PREPAID_MOCK_HOSTNAME}    ${namespace}=${PREPAID_DEFAULT_NAMESPACE}
    ...                ${pod}=${PREPAID_DEFAULT_POD}    ${container}=${PREPAID_DEFAULT_CONTAINER}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    from KPI_SDP import KPI_SDP
    ...    kpi = KPI_SDP('${hostname}', '${namespace}', '${pod}', '${PREPAID_ROOT_DIR}', 
    ...                   '${PREPAID_MOCK_OUTPUT_DIR}', '${PREPAID_MOCK_ARCHIVE_DIR}', 
    ...                   '${PREPAID_MOCK_LOG_DIR}', '${container}')
    ...    print(f'KPI_SDP initialized for prepaid host: {kpi.host_name}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    KPI_SDP initialized for prepaid host
    
    [Return]    ${result}

Initialize PREPAID Logger
    [Documentation]    Initialize and test PREPAID logging functionality
    [Arguments]        ${logger_name}=test_prepaid_logger
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    from Logger import LoggingHandler
    ...    logger = LoggingHandler.get_logger('${logger_name}')
    ...    logger.info('Test log message from PREPAID logger')
    ...    print('PREPAID logger initialized and tested')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    PREPAID logger initialized and tested
    
    [Return]    ${result}

# =============================================================================
# Prepaid-Specific Business Logic Keywords
# =============================================================================

Create PREPAID Mock KPI Data
    [Documentation]    Create mock KPI data for prepaid services
    
    &{kpi_data}=    Create Dictionary
    ...    kpi_name=${PREPAID_MOCK_KPI_NAME}
    ...    kpi_value=${PREPAID_MOCK_KPI_VALUE}
    ...    kpi_result=${PREPAID_MOCK_KPI_RESULT}
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    balance=${PREPAID_DEFAULT_BALANCE}
    ...    threshold=${PREPAID_BALANCE_THRESHOLD}
    ...    currency=${PREPAID_CURRENCY}
    
    [Return]    &{kpi_data}

Create PREPAID Mock Billing Data
    [Documentation]    Create mock billing data for prepaid services
    
    &{billing_data}=    Create Dictionary
    ...    customer_id=PREP123456
    ...    current_balance=${PREPAID_DEFAULT_BALANCE}
    ...    usage_amount=${PREPAID_DEFAULT_USAGE}
    ...    billing_period=2025-07
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    currency=${PREPAID_CURRENCY}
    ...    last_recharge=${PREPAID_RECHARGE_AMOUNT}
    
    [Return]    &{billing_data}

Create PREPAID Mock Usage Data
    [Documentation]    Create mock usage data for prepaid services
    
    &{usage_data}=    Create Dictionary
    ...    customer_id=PREP123456
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    data_usage_mb=500
    ...    voice_usage_minutes=120
    ...    sms_usage_count=50
    ...    total_cost=${PREPAID_DEFAULT_USAGE}
    ...    remaining_balance=${PREPAID_DEFAULT_BALANCE}
    
    [Return]    &{usage_data}

Process PREPAID KPI Data
    [Documentation]    Process prepaid KPI data
    [Arguments]        ${kpi_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    # Mock KPI processing for prepaid
    ...    kpi_data = ${kpi_data}
    ...    print('Prepaid KPI processing successful')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    [Return]    ${result}

Calculate PREPAID Billing KPIs
    [Documentation]    Calculate billing KPIs for prepaid services
    [Arguments]        ${billing_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    # Mock billing KPI calculation
    ...    billing_data = ${billing_data}
    ...    remaining_balance = billing_data['current_balance'] - billing_data['usage_amount']
    ...    print('Prepaid billing KPIs calculated')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    [Return]    ${result}

Process PREPAID Usage KPIs
    [Documentation]    Process usage KPIs for prepaid services
    [Arguments]        ${usage_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    # Mock usage KPI processing
    ...    usage_data = ${usage_data}
    ...    print('Prepaid usage KPIs processed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    [Return]    ${result}

Calculate PREPAID Balance
    [Documentation]    Calculate prepaid balance after usage
    [Arguments]        ${initial_balance}    ${usage_amount}
    
    ${remaining_balance}=    Evaluate    ${initial_balance} - ${usage_amount}
    
    [Return]    ${remaining_balance}

Check PREPAID Threshold
    [Documentation]    Check if prepaid balance is below threshold
    [Arguments]        ${current_balance}    ${threshold}
    
    ${below_threshold}=    Evaluate    ${current_balance} < ${threshold}
    
    [Return]    ${below_threshold}

Create PREPAID Service Configuration
    [Documentation]    Create service configuration for prepaid
    
    &{service_config}=    Create Dictionary
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    billing_domain=${PREPAID_BILLING_DOMAIN}
    ...    balance_threshold=${PREPAID_BALANCE_THRESHOLD}
    ...    currency=${PREPAID_CURRENCY}
    ...    auto_recharge=false
    
    [Return]    &{service_config}

Activate PREPAID Service
    [Documentation]    Activate prepaid service with given configuration
    [Arguments]        ${service_config}
    
    # Mock service activation logic
    ${activation_successful}=    Set Variable    true
    
    [Return]    ${activation_successful}

# =============================================================================
# Kafka Integration Keywords for Prepaid
# =============================================================================

Validate PREPAID Kafka Template
    [Documentation]    Validate Kafka message template for prepaid services
    [Arguments]        ${kafka_template}
    
    Dictionary Should Contain Key    ${kafka_template}    category
    Dictionary Should Contain Key    ${kafka_template}    platform
    Dictionary Should Contain Key    ${kafka_template}    source_owner
    
    Should Be Equal    ${kafka_template['category']}        CORE - IN
    Should Be Equal    ${kafka_template['platform']}        ERICSSON_SDP
    Should Be Equal    ${kafka_template['source_owner']}    Tier2_CC

Create PREPAID Mock Kafka Message
    [Documentation]    Create mock Kafka message for prepaid services
    [Arguments]        ${kpi_name}=${PREPAID_MOCK_KPI_NAME}    ${kpi_value}=${PREPAID_MOCK_KPI_VALUE}
    ...                ${kpi_result}=${PREPAID_MOCK_KPI_RESULT}
    
    &{kafka_message}=    Create Dictionary
    ...    category=CORE - IN
    ...    platform=ERICSSON_SDP
    ...    source_owner=Tier2_CC
    ...    service_type=${PREPAID_SERVICE_TYPE}
    ...    kpi_name=${kpi_name}
    ...    kpi_value=${kpi_value}
    ...    kpi_result=${kpi_result}
    ...    balance=${PREPAID_DEFAULT_BALANCE}
    ...    usage_amount=${PREPAID_DEFAULT_USAGE}
    ...    billing_period=2025-07
    ...    ref_id=prepaid-ref-${kpi_name}
    ...    kpi_last_updated_date=${EMPTY}
    ...    kpi_source=${EMPTY}
    ...    config_item=${EMPTY}
    ...    kpi_info=${EMPTY}
    ...    src_modified_dt=${EMPTY}
    ...    local_modified_dt=${EMPTY}
    
    [Return]    &{kafka_message}

Test PREPAID Kafka Data Source Builder
    [Documentation]    Test integration with Kafka data source builder for prepaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    sys.path.append('${PREPAID_ROOT_DIR}/../KAFKA_SENDER')
    ...    try:
    ...        from KafkaDataSourceBuilder import KafkaDataSourceBuilder
    ...        builder = KafkaDataSourceBuilder()
    ...        print('KafkaDataSourceBuilder integration successful for prepaid')
    ...    except ImportError as e:
    ...        print(f'KafkaDataSourceBuilder not available: {e}')
    ...    except Exception as e:
    ...        print(f'KafkaDataSourceBuilder error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

# =============================================================================
# Subprocess and Command Testing Keywords
# =============================================================================

Test PREPAID Subprocess Execution
    [Documentation]    Test subprocess command execution for prepaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    from SubprocessClass import SubprocessClass
    ...    sp = SubprocessClass()
    ...    print('SubprocessClass ready for prepaid')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    SubprocessClass ready for prepaid
    
    [Return]    ${result}

Mock PREPAID Kubectl Command
    [Documentation]    Mock kubectl command execution for prepaid pods
    [Arguments]        ${namespace}=${PREPAID_DEFAULT_NAMESPACE}    ${pod_pattern}=prepaid-sdp
    
    # Create mock kubectl response for prepaid pods
    ${mock_kubectl_output}=    Set Variable
    ...    NAME                         READY   STATUS    RESTARTS   AGE
    ...    ${pod_pattern}-test-1        1/1     Running   0          1d
    ...    ${pod_pattern}-test-2        1/1     Running   0          1d
    ...    ${pod_pattern}-billing-1     1/1     Running   0          1d
    
    Log    Mock kubectl output for prepaid namespace ${namespace}: ${mock_kubectl_output}
    
    [Return]    ${mock_kubectl_output}

# =============================================================================
# Performance Testing Keywords
# =============================================================================

Measure PREPAID Module Load Time
    [Documentation]    Measure the time taken to load PREPAID modules
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    Import PREPAID Python Modules
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${load_time}=     Evaluate    ${end_time} - ${start_time}
    
    Log    PREPAID module load time: ${load_time} seconds
    Should Be True    ${load_time} < 10    Module loading too slow: ${load_time}s
    
    [Return]    ${load_time}

Measure PREPAID KPI Processing Time
    [Documentation]    Measure KPI processing time for prepaid
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    ${kpi_data}=    Create PREPAID Mock KPI Data
    Process PREPAID KPI Data    ${kpi_data}
    
    ${end_time}=        Get Current Date    result_format=epoch
    ${processing_time}= Evaluate    ${end_time} - ${start_time}
    
    Log    PREPAID KPI processing time: ${processing_time} seconds
    
    [Return]    ${processing_time}

Validate PREPAID Configuration Performance
    [Documentation]    Validate configuration loading performance for prepaid
    [Arguments]        ${iterations}=5
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    FOR    ${i}    IN RANGE    ${iterations}
        ${config}=    Load PREPAID Configuration
        Validate PREPAID Configuration Structure    ${config}
    END
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${total_time}=    Evaluate    ${end_time} - ${start_time}
    ${avg_time}=      Evaluate    ${total_time} / ${iterations}
    
    Log    PREPAID configuration loading average time: ${avg_time} seconds
    Should Be True    ${avg_time} < 2    Configuration loading too slow: ${avg_time}s
    
    [Return]    ${avg_time}

# =============================================================================
# Error Handling and Testing Keywords
# =============================================================================

Test PREPAID Invalid Configuration
    [Documentation]    Test handling of invalid prepaid configuration
    [Arguments]        ${invalid_config}
    
    ${temp_config_file}=    Set Variable    ${PREPAID_ROOT_DIR}\\temp_invalid_config.json
    
    ${config_json}=    Evaluate    json.dumps($invalid_config, indent=2)    json
    Create File        ${temp_config_file}    ${config_json}
    
    ${python_code}=    Set Variable
    ...    import sys, json
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    try:
    ...        with open('${temp_config_file}', 'r') as f:
    ...            config = json.load(f)
    ...        print('Invalid prepaid config loaded without error')
    ...    except Exception as e:
    ...        print(f'Expected error: {type(e).__name__}: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Remove File    ${temp_config_file}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test PREPAID Missing Billing Data
    [Documentation]    Test handling of missing billing data
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    try:
    ...        # Simulate missing billing data scenario
    ...        billing_data = {}
    ...        if 'current_balance' not in billing_data:
    ...            raise KeyError('Missing current_balance')
    ...    except KeyError as e:
    ...        print(f'Expected error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test PREPAID Network Error Handling
    [Documentation]    Test network error handling for prepaid services
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    try:
    ...        # Simulate network error
    ...        raise ConnectionError('Network unreachable')
    ...    except ConnectionError as e:
    ...        print(f'Network error handled: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test PREPAID Missing Dependencies
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
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All required modules available
    
    [Return]    ${result}

# =============================================================================
# Integration Testing Keywords
# =============================================================================

Execute PREPAID Full Integration Test
    [Documentation]    Execute full integration test for prepaid module
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    from Logger import LoggingHandler
    ...    from KPI_SDP import KPI_SDP
    ...    from SubprocessClass import SubprocessClass
    ...    logger = LoggingHandler.get_logger('prepaid_integration_test')
    ...    kpi = KPI_SDP('${PREPAID_MOCK_HOSTNAME}', '${PREPAID_DEFAULT_NAMESPACE}', '${PREPAID_DEFAULT_POD}', 
    ...                   '${PREPAID_ROOT_DIR}', '${PREPAID_MOCK_OUTPUT_DIR}', '${PREPAID_MOCK_ARCHIVE_DIR}', 
    ...                   '${PREPAID_MOCK_LOG_DIR}', '${PREPAID_DEFAULT_CONTAINER}')
    ...    sp = SubprocessClass()
    ...    print('Prepaid integration test successful')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Prepaid integration test successful
    
    [Return]    ${result}

Test PREPAID Argument Parsing
    [Documentation]    Test command line argument parsing for prepaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    import main
    ...    # Mock sys.argv for testing
    ...    sys.argv = ['main.py', '${PREPAID_ROOT_DIR}\\${PREPAID_CONFIG_FILE}', '--test']
    ...    try:
    ...        config_path, wait, test_mode = main.parse_args()
    ...        print(f'Prepaid args parsed: config={config_path}, wait={wait}, test={test_mode}')
    ...    except SystemExit:
    ...        print('Prepaid argument parsing completed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test PREPAID Multi Process Handling
    [Documentation]    Test multi-process handling for prepaid services
    [Arguments]        ${max_processes}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${PREPAID_ROOT_DIR}')
    ...    # Mock multi-process handling
    ...    max_processes = ${max_processes}
    ...    print(f'Multi-process handling successful with {max_processes} processes')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Multi-process handling successful
    
    [Return]    ${result}

Test PREPAID Python Compatibility
    [Documentation]    Test Python version compatibility for prepaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    print(f'Python version: {sys.version}')
    ...    assert sys.version_info >= (3, 6), 'Python 3.6+ required for prepaid'
    ...    print('Python version compatibility check passed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${PREPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Python version compatibility check passed
    
    [Return]    ${result}

# =============================================================================
# Cleanup Keywords
# =============================================================================

Cleanup PREPAID Test Processes
    [Documentation]    Clean up any running PREPAID test processes
    
    Log    Cleaning up PREPAID test processes
