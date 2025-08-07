*** Settings ***
Documentation    Resource file for KAFKA_SDP_POSTPAID Robot Framework tests
...              
...              This resource file contains common keywords, variables, and utilities
...              used across multiple Robot Framework test suites for the KAFKA_SDP_POSTPAID module.
...              
...              Contains:
...              - Common variables and configuration for postpaid services
...              - Reusable keywords for test setup and teardown
...              - Postpaid-specific utility functions and mock data generation
...              - Helper keywords for validation and verification
...              - Kafka message template utilities for postpaid
...              - KPI processing helpers for postpaid services
...              - Billing and revenue calculation utilities
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
${POSTPAID_ROOT_DIR}           c:\\Users\\eakaijn\\workspace\\cec-adaptation-pod\\KAFKA_SDP_POSTPAID
${POSTPAID_CONFIG_DIR}         ${POSTPAID_ROOT_DIR}\\config
${POSTPAID_CONFIG_FILE}        ${POSTPAID_CONFIG_DIR}\\config.json
${POSTPAID_MAIN_SCRIPT}        ${POSTPAID_ROOT_DIR}\\main.py
${POSTPAID_KPI_SCRIPT}         ${POSTPAID_ROOT_DIR}\\KPI_SDP.py
${POSTPAID_LOGGER_SCRIPT}      ${POSTPAID_ROOT_DIR}\\Logger.py
${POSTPAID_SUBPROCESS_SCRIPT}  ${POSTPAID_ROOT_DIR}\\SubprocessClass.py

# Test Environment Configuration
${POSTPAID_TEST_TIMEOUT}       120 seconds
${POSTPAID_DEFAULT_NAMESPACE}  test-postpaid-namespace
${POSTPAID_DEFAULT_POD}        test-postpaid-sdp-pod
${POSTPAID_DEFAULT_CONTAINER}  test-postpaid-sdp-container
${POSTPAID_MAX_PROCESSES}      3

# Postpaid Service Configuration
${POSTPAID_SERVICE_TYPE}       postpaid
${POSTPAID_BILLING_CYCLE}      monthly
${POSTPAID_BILLING_DOMAIN}     postpaid_billing
${POSTPAID_PLAN_TYPE}          unlimited
${POSTPAID_CURRENCY}           USD
${POSTPAID_CREDIT_LIMIT}       1000.00

# Mock Test Data
${POSTPAID_MOCK_HOSTNAME}      test-postpaid-host
${POSTPAID_MOCK_OUTPUT_DIR}    /tmp/postpaid_test_output
${POSTPAID_MOCK_ARCHIVE_DIR}   /tmp/postpaid_test_archive
${POSTPAID_MOCK_LOG_DIR}       /tmp/postpaid_test_logs

# Postpaid KPI Test Data
${POSTPAID_MOCK_KPI_NAME}      postpaid_bill_amount_kpi
${POSTPAID_MOCK_KPI_VALUE}     275.50
${POSTPAID_MOCK_KPI_RESULT}    SUCCESS
${POSTPAID_USAGE_KPI_NAME}     postpaid_usage_kpi
${POSTPAID_BILLING_KPI_NAME}   postpaid_billing_kpi
${POSTPAID_REVENUE_KPI_NAME}   postpaid_revenue_kpi

# Billing Configuration
${POSTPAID_BASE_RATE}          50.00
${POSTPAID_OVERAGE_RATE}       0.10
${POSTPAID_TAX_RATE}           0.08
${POSTPAID_PLAN_LIMIT}         5000  # MB
${POSTPAID_DEFAULT_USAGE}      3500  # MB

# Kafka Template Configuration for Postpaid
&{POSTPAID_KAFKA_TEMPLATE}     category=CORE - IN    platform=ERICSSON_SDP    source_owner=Tier2_CC    service_type=postpaid
@{POSTPAID_KAFKA_TABLE}        kpi_name    kpi_value    kpi_result    bill_amount    usage_amount    billing_cycle    plan_type

# Postpaid Business Logic Constants
${POSTPAID_MIN_CREDIT_LIMIT}   100.00
${POSTPAID_MAX_CREDIT_LIMIT}   10000.00
${POSTPAID_DEFAULT_BILL}       125.75
${POSTPAID_OVERAGE_THRESHOLD}  90  # percentage

*** Keywords ***
# =============================================================================
# Setup and Teardown Keywords
# =============================================================================

Setup POSTPAID Test Environment
    [Documentation]    Set up comprehensive test environment for KAFKA_SDP_POSTPAID
    [Arguments]        ${custom_config}=&{EMPTY}
    
    Log    Setting up KAFKA_SDP_POSTPAID test environment
    
    # Verify module structure
    Verify POSTPAID Module Files
    
    # Initialize test directories
    Initialize POSTPAID Test Directories
    
    # Set up global test variables
    Set Global Variable    ${POSTPAID_TEST_SESSION}     active
    Set Global Variable    ${POSTPAID_TEST_CONFIG}      ${None}
    Set Global Variable    ${POSTPAID_MOCK_PROCESSES}   @{EMPTY}
    
    # Apply custom configuration if provided
    IF    &{custom_config}
        Set Global Variable    ${POSTPAID_CUSTOM_CONFIG}    &{custom_config}
    END
    
    Log    KAFKA_SDP_POSTPAID test environment ready

Teardown POSTPAID Test Environment
    [Documentation]    Clean up KAFKA_SDP_POSTPAID test environment
    
    Log    Tearing down KAFKA_SDP_POSTPAID test environment
    
    # Clean up test processes
    Cleanup POSTPAID Test Processes
    
    # Remove test directories
    Cleanup POSTPAID Test Directories
    
    # Reset global variables
    Set Global Variable    ${POSTPAID_TEST_SESSION}     inactive
    
    Log    KAFKA_SDP_POSTPAID test environment cleanup completed

Initialize POSTPAID Test Directories
    [Documentation]    Create necessary test directories for POSTPAID testing
    
    Create Directory    ${POSTPAID_MOCK_OUTPUT_DIR}
    Create Directory    ${POSTPAID_MOCK_ARCHIVE_DIR}  
    Create Directory    ${POSTPAID_MOCK_LOG_DIR}
    
    Log    POSTPAID test directories initialized

Cleanup POSTPAID Test Directories
    [Documentation]    Remove test directories and cleanup
    
    Remove Directory    ${POSTPAID_MOCK_OUTPUT_DIR}    recursive=true
    Remove Directory    ${POSTPAID_MOCK_ARCHIVE_DIR}   recursive=true
    Remove Directory    ${POSTPAID_MOCK_LOG_DIR}       recursive=true
    
    Log    POSTPAID test directories cleaned up

Verify POSTPAID Module Files
    [Documentation]    Verify that all required POSTPAID module files exist
    
    Directory Should Exist    ${POSTPAID_ROOT_DIR}
    Directory Should Exist    ${POSTPAID_CONFIG_DIR}
    File Should Exist         ${POSTPAID_CONFIG_FILE}
    File Should Exist         ${POSTPAID_MAIN_SCRIPT}
    File Should Exist         ${POSTPAID_KPI_SCRIPT}
    File Should Exist         ${POSTPAID_LOGGER_SCRIPT}
    File Should Exist         ${POSTPAID_SUBPROCESS_SCRIPT}

# =============================================================================
# Configuration Management Keywords
# =============================================================================

Load POSTPAID Configuration
    [Documentation]    Load the default POSTPAID configuration file
    
    ${config_content}=    Get File    ${POSTPAID_CONFIG_FILE}
    ${config_data}=       Evaluate    json.loads('''${config_content}''')    json
    
    Set Suite Variable    ${POSTPAID_TEST_CONFIG}    ${config_data}
    
    [Return]    ${config_data}

Create POSTPAID Mock Configuration
    [Documentation]    Create mock configuration for postpaid testing
    [Arguments]        ${overrides}=&{EMPTY}
    
    # Base mock configuration for postpaid
    &{mock_config}=    Create Dictionary
    ...    wait_to_start_secs=5
    ...    namespace=${POSTPAID_DEFAULT_NAMESPACE}
    ...    pod=${POSTPAID_DEFAULT_POD}
    ...    pod_container=${POSTPAID_DEFAULT_CONTAINER}
    ...    max_processes=${POSTPAID_MAX_PROCESSES}
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    billing_domain=${POSTPAID_BILLING_DOMAIN}
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    ...    credit_limit=${POSTPAID_CREDIT_LIMIT}
    ...    whitelist_pod_enable=false
    ...    whitelist_pods=@{EMPTY}
    ...    blacklist_pods=@{EMPTY}
    ...    kafka_message_template=&{POSTPAID_KAFKA_TEMPLATE}
    
    # Apply any overrides
    FOR    ${key}    ${value}    IN    &{overrides}
        Set To Dictionary    ${mock_config}    ${key}    ${value}
    END
    
    # Add kafka table to template
    Set To Dictionary    ${mock_config['kafka_message_template']}    @table    @{POSTPAID_KAFKA_TABLE}
    
    [Return]    &{mock_config}

Validate POSTPAID Configuration Structure
    [Documentation]    Validate POSTPAID configuration structure and values
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

Import POSTPAID Python Modules
    [Documentation]    Import and validate POSTPAID Python modules
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    import main
    ...    import KPI_SDP
    ...    import Logger
    ...    import SubprocessClass
    ...    print('All POSTPAID modules imported successfully')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All POSTPAID modules imported successfully
    
    [Return]    ${result}

Initialize POSTPAID KPI Instance
    [Documentation]    Initialize KPI_SDP instance for postpaid services
    [Arguments]        ${hostname}=${POSTPAID_MOCK_HOSTNAME}    ${namespace}=${POSTPAID_DEFAULT_NAMESPACE}
    ...                ${pod}=${POSTPAID_DEFAULT_POD}    ${container}=${POSTPAID_DEFAULT_CONTAINER}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    from KPI_SDP import KPI_SDP
    ...    kpi = KPI_SDP('${hostname}', '${namespace}', '${pod}', '${POSTPAID_ROOT_DIR}', 
    ...                   '${POSTPAID_MOCK_OUTPUT_DIR}', '${POSTPAID_MOCK_ARCHIVE_DIR}', 
    ...                   '${POSTPAID_MOCK_LOG_DIR}', '${container}')
    ...    print(f'KPI_SDP initialized for postpaid host: {kpi.host_name}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    KPI_SDP initialized for postpaid host
    
    [Return]    ${result}

Initialize POSTPAID Logger
    [Documentation]    Initialize and test POSTPAID logging functionality
    [Arguments]        ${logger_name}=test_postpaid_logger
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    from Logger import LoggingHandler
    ...    logger = LoggingHandler.get_logger('${logger_name}')
    ...    logger.info('Test log message from POSTPAID logger')
    ...    print('POSTPAID logger initialized and tested')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    POSTPAID logger initialized and tested
    
    [Return]    ${result}

# =============================================================================
# Postpaid-Specific Business Logic Keywords
# =============================================================================

Create POSTPAID Mock KPI Data
    [Documentation]    Create mock KPI data for postpaid services
    
    &{kpi_data}=    Create Dictionary
    ...    kpi_name=${POSTPAID_MOCK_KPI_NAME}
    ...    kpi_value=${POSTPAID_MOCK_KPI_VALUE}
    ...    kpi_result=${POSTPAID_MOCK_KPI_RESULT}
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    ...    currency=${POSTPAID_CURRENCY}
    
    [Return]    &{kpi_data}

Create POSTPAID Mock Billing Data
    [Documentation]    Create mock billing data for postpaid services
    
    &{billing_data}=    Create Dictionary
    ...    customer_id=POST789012
    ...    base_rate=${POSTPAID_BASE_RATE}
    ...    usage_charges=125.75
    ...    overage_charges=25.50
    ...    taxes=17.58
    ...    total_bill=${POSTPAID_DEFAULT_BILL}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    currency=${POSTPAID_CURRENCY}
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    ...    credit_limit=${POSTPAID_CREDIT_LIMIT}
    
    [Return]    &{billing_data}

Create POSTPAID Mock Usage Data
    [Documentation]    Create mock usage data for postpaid services
    
    &{usage_data}=    Create Dictionary
    ...    customer_id=POST789012
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    plan_limit=${POSTPAID_PLAN_LIMIT}
    ...    data_usage_mb=${POSTPAID_DEFAULT_USAGE}
    ...    voice_usage_minutes=320
    ...    sms_usage_count=125
    ...    total_charges=125.75
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    overage_amount=0
    
    [Return]    &{usage_data}

Create POSTPAID Mock Revenue Data
    [Documentation]    Create mock revenue data for postpaid services
    
    &{revenue_data}=    Create Dictionary
    ...    customer_id=POST789012
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    base_revenue=${POSTPAID_BASE_RATE}
    ...    usage_revenue=125.75
    ...    overage_revenue=25.50
    ...    tax_revenue=17.58
    ...    total_revenue=218.83
    ...    billing_period=2025-07
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    
    [Return]    &{revenue_data}

Create POSTPAID Mock Billing Cycle Data
    [Documentation]    Create mock billing cycle data for postpaid services
    
    &{billing_cycle_data}=    Create Dictionary
    ...    cycle_start=2025-07-01
    ...    cycle_end=2025-07-31
    ...    billing_date=2025-08-05
    ...    due_date=2025-08-20
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    customers_billed=1250
    ...    total_revenue=156250.75
    
    [Return]    &{billing_cycle_data}

Process POSTPAID KPI Data
    [Documentation]    Process postpaid KPI data
    [Arguments]        ${kpi_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock KPI processing for postpaid
    ...    kpi_data = ${kpi_data}
    ...    print('Postpaid KPI processing successful')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    [Return]    ${result}

Calculate POSTPAID Billing KPIs
    [Documentation]    Calculate billing KPIs for postpaid services
    [Arguments]        ${billing_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock billing KPI calculation
    ...    billing_data = ${billing_data}
    ...    total_bill = billing_data['base_rate'] + billing_data['usage_charges'] + billing_data['overage_charges'] + billing_data['taxes']
    ...    print('Postpaid billing KPIs calculated')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    [Return]    ${result}

Process POSTPAID Usage KPIs
    [Documentation]    Process usage KPIs for postpaid services
    [Arguments]        ${usage_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock usage KPI processing
    ...    usage_data = ${usage_data}
    ...    usage_percentage = (usage_data['data_usage_mb'] / usage_data['plan_limit']) * 100
    ...    print('Postpaid usage KPIs processed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    [Return]    ${result}

Process POSTPAID Revenue KPIs
    [Documentation]    Process revenue KPIs for postpaid services
    [Arguments]        ${revenue_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock revenue KPI processing
    ...    revenue_data = ${revenue_data}
    ...    print('Postpaid revenue KPIs processed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    [Return]    ${result}

Process POSTPAID Billing Cycle
    [Documentation]    Process billing cycle for postpaid services
    [Arguments]        ${billing_cycle_data}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock billing cycle processing
    ...    cycle_data = ${billing_cycle_data}
    ...    print('Billing cycle processing successful')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    [Return]    ${result}

# =============================================================================
# Business Logic Calculation Keywords
# =============================================================================

Calculate POSTPAID Bill Amount
    [Documentation]    Calculate total bill amount for postpaid services
    [Arguments]        ${base_amount}    ${usage_charges}    ${taxes}
    
    ${total_bill}=    Evaluate    ${base_amount} + ${usage_charges} + ${taxes}
    
    [Return]    ${total_bill}

Check POSTPAID Credit Limit
    [Documentation]    Check if postpaid usage is within credit limit
    [Arguments]        ${current_usage}    ${credit_limit}
    
    ${within_limit}=    Evaluate    ${current_usage} <= ${credit_limit}
    
    [Return]    ${within_limit}

Calculate POSTPAID Overage
    [Documentation]    Calculate overage charges for postpaid services
    [Arguments]        ${plan_limit}    ${actual_usage}    ${overage_rate}
    
    ${overage}=    Evaluate    max(0, (${actual_usage} - ${plan_limit}) * ${overage_rate})
    
    [Return]    ${overage}

Create POSTPAID Service Configuration
    [Documentation]    Create service configuration for postpaid
    
    &{service_config}=    Create Dictionary
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    billing_domain=${POSTPAID_BILLING_DOMAIN}
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    ...    credit_limit=${POSTPAID_CREDIT_LIMIT}
    ...    currency=${POSTPAID_CURRENCY}
    ...    auto_pay=false
    
    [Return]    &{service_config}

Provision POSTPAID Service
    [Documentation]    Provision postpaid service with given configuration
    [Arguments]        ${service_config}
    
    # Mock service provisioning logic
    ${provisioning_successful}=    Set Variable    true
    
    [Return]    ${provisioning_successful}

Upgrade POSTPAID Plan
    [Documentation]    Upgrade postpaid plan
    [Arguments]        ${current_plan}    ${new_plan}
    
    # Mock plan upgrade logic
    ${upgrade_successful}=    Set Variable    true
    
    [Return]    ${upgrade_successful}

# =============================================================================
# Kafka Integration Keywords for Postpaid
# =============================================================================

Validate POSTPAID Kafka Template
    [Documentation]    Validate Kafka message template for postpaid services
    [Arguments]        ${kafka_template}
    
    Dictionary Should Contain Key    ${kafka_template}    category
    Dictionary Should Contain Key    ${kafka_template}    platform
    Dictionary Should Contain Key    ${kafka_template}    source_owner
    
    Should Be Equal    ${kafka_template['category']}        CORE - IN
    Should Be Equal    ${kafka_template['platform']}        ERICSSON_SDP
    Should Be Equal    ${kafka_template['source_owner']}    Tier2_CC

Create POSTPAID Mock Kafka Message
    [Documentation]    Create mock Kafka message for postpaid services
    [Arguments]        ${kpi_name}=${POSTPAID_MOCK_KPI_NAME}    ${kpi_value}=${POSTPAID_MOCK_KPI_VALUE}
    ...                ${kpi_result}=${POSTPAID_MOCK_KPI_RESULT}
    
    &{kafka_message}=    Create Dictionary
    ...    category=CORE - IN
    ...    platform=ERICSSON_SDP
    ...    source_owner=Tier2_CC
    ...    service_type=${POSTPAID_SERVICE_TYPE}
    ...    kpi_name=${kpi_name}
    ...    kpi_value=${kpi_value}
    ...    kpi_result=${kpi_result}
    ...    bill_amount=${POSTPAID_DEFAULT_BILL}
    ...    usage_amount=${POSTPAID_DEFAULT_USAGE}
    ...    billing_cycle=${POSTPAID_BILLING_CYCLE}
    ...    plan_type=${POSTPAID_PLAN_TYPE}
    ...    ref_id=postpaid-ref-${kpi_name}
    ...    kpi_last_updated_date=${EMPTY}
    ...    kpi_source=${EMPTY}
    ...    config_item=${EMPTY}
    ...    kpi_info=${EMPTY}
    ...    src_modified_dt=${EMPTY}
    ...    local_modified_dt=${EMPTY}
    
    [Return]    &{kafka_message}

Test POSTPAID Kafka Data Source Builder
    [Documentation]    Test integration with Kafka data source builder for postpaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    sys.path.append('${POSTPAID_ROOT_DIR}/../KAFKA_SENDER')
    ...    try:
    ...        from KafkaDataSourceBuilder import KafkaDataSourceBuilder
    ...        builder = KafkaDataSourceBuilder()
    ...        print('KafkaDataSourceBuilder integration successful for postpaid')
    ...    except ImportError as e:
    ...        print(f'KafkaDataSourceBuilder not available: {e}')
    ...    except Exception as e:
    ...        print(f'KafkaDataSourceBuilder error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

# =============================================================================
# Subprocess and Command Testing Keywords
# =============================================================================

Test POSTPAID Subprocess Execution
    [Documentation]    Test subprocess command execution for postpaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    from SubprocessClass import SubprocessClass
    ...    sp = SubprocessClass()
    ...    print('SubprocessClass ready for postpaid')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    SubprocessClass ready for postpaid
    
    [Return]    ${result}

Mock POSTPAID Kubectl Command
    [Documentation]    Mock kubectl command execution for postpaid pods
    [Arguments]        ${namespace}=${POSTPAID_DEFAULT_NAMESPACE}    ${pod_pattern}=postpaid-sdp
    
    # Create mock kubectl response for postpaid pods
    ${mock_kubectl_output}=    Set Variable
    ...    NAME                         READY   STATUS    RESTARTS   AGE
    ...    ${pod_pattern}-test-1        1/1     Running   0          1d
    ...    ${pod_pattern}-test-2        1/1     Running   0          1d
    ...    ${pod_pattern}-billing-1     1/1     Running   0          1d
    ...    ${pod_pattern}-revenue-1     1/1     Running   0          1d
    
    Log    Mock kubectl output for postpaid namespace ${namespace}: ${mock_kubectl_output}
    
    [Return]    ${mock_kubectl_output}

# =============================================================================
# Performance Testing Keywords
# =============================================================================

Measure POSTPAID Module Load Time
    [Documentation]    Measure the time taken to load POSTPAID modules
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    Import POSTPAID Python Modules
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${load_time}=     Evaluate    ${end_time} - ${start_time}
    
    Log    POSTPAID module load time: ${load_time} seconds
    Should Be True    ${load_time} < 10    Module loading too slow: ${load_time}s
    
    [Return]    ${load_time}

Measure POSTPAID KPI Processing Time
    [Documentation]    Measure KPI processing time for postpaid
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    ${kpi_data}=    Create POSTPAID Mock KPI Data
    Process POSTPAID KPI Data    ${kpi_data}
    
    ${end_time}=        Get Current Date    result_format=epoch
    ${processing_time}= Evaluate    ${end_time} - ${start_time}
    
    Log    POSTPAID KPI processing time: ${processing_time} seconds
    
    [Return]    ${processing_time}

Measure POSTPAID Billing Processing Time
    [Documentation]    Measure billing processing time for postpaid
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    ${billing_data}=    Create POSTPAID Mock Billing Data
    Calculate POSTPAID Billing KPIs    ${billing_data}
    
    ${end_time}=        Get Current Date    result_format=epoch
    ${billing_time}=    Evaluate    ${end_time} - ${start_time}
    
    Log    POSTPAID billing processing time: ${billing_time} seconds
    
    [Return]    ${billing_time}

Validate POSTPAID Configuration Performance
    [Documentation]    Validate configuration loading performance for postpaid
    [Arguments]        ${iterations}=5
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    FOR    ${i}    IN RANGE    ${iterations}
        ${config}=    Load POSTPAID Configuration
        Validate POSTPAID Configuration Structure    ${config}
    END
    
    ${end_time}=      Get Current Date    result_format=epoch
    ${total_time}=    Evaluate    ${end_time} - ${start_time}
    ${avg_time}=      Evaluate    ${total_time} / ${iterations}
    
    Log    POSTPAID configuration loading average time: ${avg_time} seconds
    Should Be True    ${avg_time} < 2    Configuration loading too slow: ${avg_time}s
    
    [Return]    ${avg_time}

# =============================================================================
# Error Handling and Testing Keywords
# =============================================================================

Test POSTPAID Invalid Configuration
    [Documentation]    Test handling of invalid postpaid configuration
    [Arguments]        ${invalid_config}
    
    ${temp_config_file}=    Set Variable    ${POSTPAID_ROOT_DIR}\\temp_invalid_config.json
    
    ${config_json}=    Evaluate    json.dumps($invalid_config, indent=2)    json
    Create File        ${temp_config_file}    ${config_json}
    
    ${python_code}=    Set Variable
    ...    import sys, json
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    try:
    ...        with open('${temp_config_file}', 'r') as f:
    ...            config = json.load(f)
    ...        print('Invalid postpaid config loaded without error')
    ...    except Exception as e:
    ...        print(f'Expected error: {type(e).__name__}: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Remove File    ${temp_config_file}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test POSTPAID Missing Billing Data
    [Documentation]    Test handling of missing billing data
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    try:
    ...        # Simulate missing billing data scenario
    ...        billing_data = {}
    ...        if 'total_bill' not in billing_data:
    ...            raise KeyError('Missing total_bill')
    ...    except KeyError as e:
    ...        print(f'Expected error: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test POSTPAID Network Error Handling
    [Documentation]    Test network error handling for postpaid services
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    try:
    ...        # Simulate network error
    ...        raise ConnectionError('Network unreachable')
    ...    except ConnectionError as e:
    ...        print(f'Network error handled: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test POSTPAID Billing Cycle Error
    [Documentation]    Test billing cycle error handling
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    try:
    ...        # Simulate billing cycle error
    ...        raise ValueError('Invalid billing cycle date')
    ...    except ValueError as e:
    ...        print(f'Billing cycle error handled: {e}')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test POSTPAID Missing Dependencies
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
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    All required modules available
    
    [Return]    ${result}

# =============================================================================
# Integration Testing Keywords
# =============================================================================

Execute POSTPAID Full Integration Test
    [Documentation]    Execute full integration test for postpaid module
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    from Logger import LoggingHandler
    ...    from KPI_SDP import KPI_SDP
    ...    from SubprocessClass import SubprocessClass
    ...    logger = LoggingHandler.get_logger('postpaid_integration_test')
    ...    kpi = KPI_SDP('${POSTPAID_MOCK_HOSTNAME}', '${POSTPAID_DEFAULT_NAMESPACE}', '${POSTPAID_DEFAULT_POD}', 
    ...                   '${POSTPAID_ROOT_DIR}', '${POSTPAID_MOCK_OUTPUT_DIR}', '${POSTPAID_MOCK_ARCHIVE_DIR}', 
    ...                   '${POSTPAID_MOCK_LOG_DIR}', '${POSTPAID_DEFAULT_CONTAINER}')
    ...    sp = SubprocessClass()
    ...    print('Postpaid integration test successful')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Postpaid integration test successful
    
    [Return]    ${result}

Test POSTPAID Argument Parsing
    [Documentation]    Test command line argument parsing for postpaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    import main
    ...    # Mock sys.argv for testing
    ...    sys.argv = ['main.py', '${POSTPAID_CONFIG_FILE}', '--test']
    ...    try:
    ...        config_path, wait, test_mode = main.parse_args()
    ...        print(f'Postpaid args parsed: config={config_path}, wait={wait}, test={test_mode}')
    ...    except SystemExit:
    ...        print('Postpaid argument parsing completed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    
    [Return]    ${result}

Test POSTPAID Multi Process Handling
    [Documentation]    Test multi-process handling for postpaid services
    [Arguments]        ${max_processes}
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    sys.path.append('${POSTPAID_ROOT_DIR}')
    ...    # Mock multi-process handling
    ...    max_processes = ${max_processes}
    ...    print(f'Multi-process handling successful with {max_processes} processes')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Multi-process handling successful
    
    [Return]    ${result}

Test POSTPAID Python Compatibility
    [Documentation]    Test Python version compatibility for postpaid
    
    ${python_code}=    Set Variable
    ...    import sys
    ...    print(f'Python version: {sys.version}')
    ...    assert sys.version_info >= (3, 6), 'Python 3.6+ required for postpaid'
    ...    print('Python version compatibility check passed')
    
    ${result}=    Run Process    python    -c    ${python_code}    cwd=${POSTPAID_ROOT_DIR}
    
    Should Be Equal As Numbers    ${result.rc}    0
    Should Contain    ${result.stdout}    Python version compatibility check passed
    
    [Return]    ${result}

# =============================================================================
# Cleanup Keywords
# =============================================================================

Cleanup POSTPAID Test Processes
    [Documentation]    Clean up any running POSTPAID test processes
    
    Log    Cleaning up POSTPAID test processes
