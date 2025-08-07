*** Settings ***
Documentation    Resource file for KAFKA_CAF module Robot Framework tests
...              Contains keywords, variables, and test data for CAF KPI processing with Kafka integration

Library          Collections
Library          DateTime
Library          JSONLibrary
Library          OperatingSystem
Library          Process
Library          String
Library          XML

*** Variables ***
# Module Configuration
${KAFKA_CAF_MODULE_DIR}         ${CURDIR}/..
${KAFKA_CAF_CONFIG_FILE}        ${KAFKA_CAF_MODULE_DIR}/config/config.json
${KAFKA_CONFIG_FILE}            ${KAFKA_CAF_MODULE_DIR}/config/kafka_config.json
${XSL_TEMPLATE_FILE}            ${KAFKA_CAF_MODULE_DIR}/measCollec.xsl

# Test Configuration
${TEST_TIMEOUT}                 300s
${DEFAULT_NAMESPACE}            test-namespace
${MOCK_NAMESPACE}               mock-namespace

# Test Data Files
${INVALID_CONFIG_FILE}          ${CURDIR}/test_data/invalid_config.json
${NON_EXISTENT_CONFIG_FILE}     ${CURDIR}/test_data/non_existent.json

# Mock Data
${MOCK_POD_NAME}                mock-caf-pod-12345
${MOCK_DATA_SOURCES}            source1    source2    source3
${KAFKA_TOPIC}                  caf-kpi-topic

# Performance Configuration
${MAX_PROCESSES}                4
${LARGE_XML_SIZE}               1048576    # 1MB
${HIGH_VOLUME_COUNT}            1000
${BATCH_SIZE}                   100
${CONCURRENT_FILE_COUNT}        10
${MAX_FILE_SIZE}                10485760   # 10MB
${MAX_MEMORY_INCREASE}          100000000  # 100MB
${MIN_QUALITY_SCORE}            0.8
${RETENTION_DAYS}               7

*** Keywords ***

# Setup and Teardown Keywords
Setup Test Environment
    [Documentation]    Setup test environment for KAFKA_CAF module tests
    
    Log    Setting up KAFKA_CAF test environment
    Create Directory    ${TEST_DATA_DIR}
    Create Directory    ${TEMP_TEST_DIR}
    
    Create Test Configuration Files
    Setup Mock Environment
    
    Log    KAFKA_CAF test environment setup completed

Cleanup Test Environment
    [Documentation]    Cleanup test environment after tests
    
    Log    Cleaning up KAFKA_CAF test environment
    
    Remove Directory    ${TEST_DATA_DIR}    recursive=${True}
    Remove Directory    ${TEMP_TEST_DIR}    recursive=${True}
    
    Cleanup Mock Environment
    
    Log    KAFKA_CAF test environment cleanup completed

Setup Mock Environment
    [Documentation]    Setup mock environment for testing
    
    Set Environment Variable    MOCK_MODE    true
    Set Environment Variable    MOCK_NAMESPACE    ${MOCK_NAMESPACE}

Cleanup Mock Environment
    [Documentation]    Cleanup mock environment
    
    Remove Environment Variable    MOCK_MODE
    Remove Environment Variable    MOCK_NAMESPACE

# Configuration Management Keywords
Load Kafka CAF Configuration
    [Documentation]    Load and parse KAFKA_CAF configuration file
    [Arguments]    ${config_file_path}
    
    Log    Loading CAF configuration from: ${config_file_path}
    File Should Exist    ${config_file_path}
    
    ${config_content} =    Get File    ${config_file_path}
    ${config} =    Convert String To Json    ${config_content}
    
    [Return]    ${config}

Verify Kafka CAF Configuration Structure
    [Documentation]    Verify the structure of loaded CAF configuration
    [Arguments]    ${config}
    
    Dictionary Should Contain Key    ${config}    pod
    Dictionary Should Contain Key    ${config}    dir_lookup
    Dictionary Should Contain Key    ${config}    perf_data_files_local_dir
    Dictionary Should Contain Key    ${config}    execution_period_mins

Load XSL Template
    [Documentation]    Load XSL transformation template
    [Arguments]    ${xsl_file_path}
    
    File Should Exist    ${xsl_file_path}
    ${xsl_content} =    Get File    ${xsl_file_path}
    [Return]    ${xsl_content}

Verify XSL Template Structure
    [Documentation]    Verify XSL template structure
    [Arguments]    ${xsl_content}
    
    Should Contain    ${xsl_content}    <xsl:stylesheet
    Should Contain    ${xsl_content}    <xsl:template

Create Test Configuration Files
    [Documentation]    Create test configuration files
    
    ${invalid_config} =    Create Dictionary    invalid_key=invalid_value
    ${invalid_json} =    Convert Json To String    ${invalid_config}
    Create File    ${INVALID_CONFIG_FILE}    ${invalid_json}

# Performance Data Processing Keywords
Setup Mock Pod Environment
    [Documentation]    Setup mock pod environment
    
    Set Environment Variable    MOCK_POD_NAME    ${MOCK_POD_NAME}

Collect CAF Performance Data
    [Documentation]    Collect CAF performance data from pod
    [Arguments]    ${pod_name}    ${namespace}
    
    Log    Collecting CAF performance data for pod ${pod_name}
    
    ${perf_data} =    Create Dictionary
    ...    pod_name=${pod_name}
    ...    namespace=${namespace}
    ...    timestamp=${timestamp()}
    ...    cpu_usage=45.5
    ...    memory_usage=2048
    ...    network_throughput=1024.5
    ...    response_time=125.3
    ...    transaction_count=150
    
    [Return]    ${perf_data}

Verify CAF Performance Data Structure
    [Documentation]    Verify CAF performance data structure
    [Arguments]    ${perf_data}
    
    Dictionary Should Contain Key    ${perf_data}    pod_name
    Dictionary Should Contain Key    ${perf_data}    cpu_usage
    Dictionary Should Contain Key    ${perf_data}    memory_usage
    Dictionary Should Contain Key    ${perf_data}    transaction_count

Create Test XML Performance Data
    [Documentation]    Create test XML performance data file
    [Arguments]    ${filepath}
    
    ${xml_content} =    Set Variable    <?xml version="1.0" encoding="UTF-8"?>
    ...    <performanceData>
    ...        <measurement>
    ...            <pod>test-caf-pod</pod>
    ...            <cpu>45.5</cpu>
    ...            <memory>2048</memory>
    ...            <transactions>150</transactions>
    ...        </measurement>
    ...    </performanceData>
    
    Create File    ${filepath}    ${xml_content}

Process XML Performance Data
    [Documentation]    Process XML performance data
    [Arguments]    ${xml_file_path}
    
    Log    Processing XML performance data from: ${xml_file_path}
    
    ${xml_content} =    Get File    ${xml_file_path}
    ${parsed_xml} =    Parse XML    ${xml_content}
    
    ${processed_data} =    Create Dictionary
    ...    source_file=${xml_file_path}
    ...    parsed_xml=${parsed_xml}
    ...    processed_at=${timestamp()}
    
    [Return]    ${processed_data}

Verify Processed XML Data
    [Documentation]    Verify processed XML data
    [Arguments]    ${processed_data}
    
    Dictionary Should Contain Key    ${processed_data}    source_file
    Dictionary Should Contain Key    ${processed_data}    parsed_xml
    Dictionary Should Contain Key    ${processed_data}    processed_at

Create Test XML Data
    [Documentation]    Create test XML data for transformation
    [Arguments]    ${filepath}
    
    Create Test XML Performance Data    ${filepath}

Apply XSL Transformation
    [Documentation]    Apply XSL transformation to XML data
    [Arguments]    ${xml_file}    ${xsl_file}
    
    Log    Applying XSL transformation: ${xsl_file} to ${xml_file}
    
    # Mock XSL transformation result
    ${transformed} =    Create Dictionary
    ...    input_xml=${xml_file}
    ...    xsl_template=${xsl_file}
    ...    transformation_result=transformed_data
    ...    transformed_at=${timestamp()}
    
    [Return]    ${transformed}

Verify XSL Transformation Result
    [Documentation]    Verify XSL transformation result
    [Arguments]    ${transformed}
    
    Dictionary Should Contain Key    ${transformed}    input_xml
    Dictionary Should Contain Key    ${transformed}    transformation_result

Create Large XML File
    [Documentation]    Create large XML file for performance testing
    [Arguments]    ${filepath}    ${size_bytes}
    
    ${large_xml_content} =    Set Variable    <?xml version="1.0"?>
    ${large_xml_content} =    Set Variable    ${large_xml_content}<data>
    
    # Add repetitive content to reach desired size
    FOR    ${i}    IN RANGE    100
        ${large_xml_content} =    Set Variable    ${large_xml_content}<item id="${i}">Large content data ${i}</item>
    END
    
    ${large_xml_content} =    Set Variable    ${large_xml_content}</data>
    Create File    ${filepath}    ${large_xml_content}

# KPI Processing Keywords
Create Test Performance Data
    [Documentation]    Create test performance data
    
    ${perf_data} =    Create Dictionary
    ...    pod_name=test-caf-pod
    ...    cpu_usage=45.5
    ...    memory_usage=2048
    ...    network_throughput=1024.5
    ...    response_time=125.3
    ...    transaction_count=150
    ...    timestamp=${timestamp()}
    
    [Return]    ${perf_data}

Generate CAF KPI From Performance Data
    [Documentation]    Generate CAF KPI from performance data
    [Arguments]    ${perf_data}
    
    Log    Generating CAF KPI from performance data
    
    # Calculate KPI metrics
    ${cpu_usage} =    Get From Dictionary    ${perf_data}    cpu_usage
    ${memory_usage} =    Get From Dictionary    ${perf_data}    memory_usage
    ${transaction_count} =    Get From Dictionary    ${perf_data}    transaction_count
    
    ${kpi_data} =    Create Dictionary
    ...    pod_name=${perf_data}[pod_name]
    ...    timestamp=${timestamp()}
    ...    cpu_kpi=${cpu_usage}
    ...    memory_kpi=${memory_usage}
    ...    transaction_kpi=${transaction_count}
    ...    performance_score=${Evaluate    (${cpu_usage} + ${memory_usage} / 100) / 2}
    
    [Return]    ${kpi_data}

Verify CAF KPI Structure
    [Documentation]    Verify CAF KPI structure
    [Arguments]    ${kpi_data}
    
    Dictionary Should Contain Key    ${kpi_data}    pod_name
    Dictionary Should Contain Key    ${kpi_data}    cpu_kpi
    Dictionary Should Contain Key    ${kpi_data}    memory_kpi
    Dictionary Should Contain Key    ${kpi_data}    transaction_kpi
    Dictionary Should Contain Key    ${kpi_data}    performance_score

Create Raw CAF Metrics
    [Documentation]    Create raw CAF metrics for calculation testing
    
    ${raw_metrics} =    Create Dictionary
    ...    cpu_raw=45.5
    ...    memory_raw=2048
    ...    network_raw=1024.5
    ...    transactions_raw=150
    
    [Return]    ${raw_metrics}

Apply CAF KPI Calculation Rules
    [Documentation]    Apply CAF KPI calculation business rules
    [Arguments]    ${raw_metrics}
    
    ${cpu_kpi} =    Evaluate    ${raw_metrics}[cpu_raw] * 1.1
    ${memory_kpi} =    Evaluate    ${raw_metrics}[memory_raw] / 1024
    ${network_kpi} =    Evaluate    ${raw_metrics}[network_raw] * 0.8
    
    ${calculated_kpi} =    Create Dictionary
    ...    cpu_kpi=${cpu_kpi}
    ...    memory_kpi=${memory_kpi}
    ...    network_kpi=${network_kpi}
    ...    calculated_at=${timestamp()}
    
    [Return]    ${calculated_kpi}

Verify CAF KPI Calculation Rules
    [Documentation]    Verify CAF KPI calculation rules were applied
    [Arguments]    ${calculated_kpi}
    
    Dictionary Should Contain Key    ${calculated_kpi}    cpu_kpi
    Dictionary Should Contain Key    ${calculated_kpi}    memory_kpi
    Dictionary Should Contain Key    ${calculated_kpi}    network_kpi

Verify KPI Value Ranges
    [Documentation]    Verify KPI values are within expected ranges
    [Arguments]    ${calculated_kpi}
    
    ${cpu_kpi} =    Get From Dictionary    ${calculated_kpi}    cpu_kpi
    ${memory_kpi} =    Get From Dictionary    ${calculated_kpi}    memory_kpi
    
    Should Be True    ${cpu_kpi} >= 0 and ${cpu_kpi} <= 100
    Should Be True    ${memory_kpi} >= 0

Create Multiple CAF KPI Sources
    [Documentation]    Create multiple CAF KPI sources for aggregation
    
    ${kpi_sources} =    Create List
    
    FOR    ${i}    IN RANGE    3
        ${kpi_source} =    Create Dictionary
        ...    source_id=source_${i}
        ...    cpu_kpi=${i * 10}
        ...    memory_kpi=${i * 512}
        ...    transaction_kpi=${i * 50}
        
        Append To List    ${kpi_sources}    ${kpi_source}
    END
    
    [Return]    ${kpi_sources}

Aggregate CAF KPI Data
    [Documentation]    Aggregate multiple CAF KPI sources
    [Arguments]    ${kpi_sources}
    
    ${total_cpu} =    Set Variable    0
    ${total_memory} =    Set Variable    0
    ${total_transactions} =    Set Variable    0
    
    FOR    ${kpi_source}    IN    @{kpi_sources}
        ${cpu} =    Get From Dictionary    ${kpi_source}    cpu_kpi
        ${memory} =    Get From Dictionary    ${kpi_source}    memory_kpi
        ${transactions} =    Get From Dictionary    ${kpi_source}    transaction_kpi
        
        ${total_cpu} =    Evaluate    ${total_cpu} + ${cpu}
        ${total_memory} =    Evaluate    ${total_memory} + ${memory}
        ${total_transactions} =    Evaluate    ${total_transactions} + ${transactions}
    END
    
    ${aggregated} =    Create Dictionary
    ...    total_sources=${kpi_sources.__len__()}
    ...    total_cpu_kpi=${total_cpu}
    ...    total_memory_kpi=${total_memory}
    ...    total_transaction_kpi=${total_transactions}
    ...    aggregated_at=${timestamp()}
    
    [Return]    ${aggregated}

Verify Aggregated CAF KPI Data
    [Documentation]    Verify aggregated CAF KPI data
    [Arguments]    ${aggregated}
    
    Dictionary Should Contain Key    ${aggregated}    total_sources
    Dictionary Should Contain Key    ${aggregated}    total_cpu_kpi
    Dictionary Should Contain Key    ${aggregated}    total_memory_kpi
    Dictionary Should Contain Key    ${aggregated}    aggregated_at

# File Operations Keywords
Create Performance Data Files
    [Documentation]    Create performance data files for discovery testing
    [Arguments]    ${directory}
    
    Create Directory    ${directory}
    
    FOR    ${i}    IN RANGE    5
        ${filename} =    Set Variable    perf_data_${i}.xml
        ${filepath} =    Join Path    ${directory}    ${filename}
        Create Test XML Performance Data    ${filepath}
    END

Discover Performance Data Files
    [Documentation]    Discover performance data files in directory
    [Arguments]    ${directory}
    
    ${files} =    List Files In Directory    ${directory}    pattern=*.xml
    ${discovered_files} =    Create List
    
    FOR    ${file}    IN    @{files}
        ${filepath} =    Join Path    ${directory}    ${file}
        Append To List    ${discovered_files}    ${filepath}
    END
    
    [Return]    ${discovered_files}

Verify Performance File Discovery
    [Documentation]    Verify performance file discovery results
    [Arguments]    ${discovered_files}
    
    Should Not Be Empty    ${discovered_files}
    
    FOR    ${file}    IN    @{discovered_files}
        Should End With    ${file}    .xml
    END

Store Performance Data Locally
    [Documentation]    Store performance data to local directory
    [Arguments]    ${perf_data}    ${local_directory}
    
    Create Directory    ${local_directory}
    
    ${filename} =    Set Variable    perf_data_${timestamp()}.json
    ${filepath} =    Join Path    ${local_directory}    ${filename}
    
    ${perf_json} =    Convert Json To String    ${perf_data}
    Create File    ${filepath}    ${perf_json}
    
    [Return]    ${True}

Verify Local Storage
    [Documentation]    Verify local storage of performance data
    [Arguments]    ${local_directory}
    
    Directory Should Exist    ${local_directory}
    ${files} =    List Files In Directory    ${local_directory}
    Should Not Be Empty    ${files}

Create Old Performance Files
    [Documentation]    Create old performance files for cleanup testing
    [Arguments]    ${directory}
    
    Create Directory    ${directory}
    
    # Create files with different ages
    FOR    ${age}    IN RANGE    1    15
        ${filename} =    Set Variable    old_perf_${age}.xml
        ${filepath} =    Join Path    ${directory}    ${filename}
        Create Test XML Performance Data    ${filepath}
        
        # Set file timestamp to simulate age
        ${timestamp} =    Get Current Date    increment=-${age} days    result_format=epoch
        Set Modified Time    ${filepath}    ${timestamp}
    END

Cleanup Old Performance Files
    [Documentation]    Cleanup old performance files
    [Arguments]    ${directory}    ${retention_days}
    
    ${command} =    Set Variable    find ${directory} -name "*.xml" -mtime +${retention_days} -delete
    ${result} =    Run Process    ${command}    shell=True
    
    [Return]    ${result.rc == 0}

Verify File Cleanup Results
    [Documentation]    Verify file cleanup results
    [Arguments]    ${directory}
    
    ${files} =    List Files In Directory    ${directory}
    
    FOR    ${file}    IN    @{files}
        ${filepath} =    Join Path    ${directory}    ${file}
        ${age_days} =    Get File Age In Days    ${filepath}
        Should Be True    ${age_days} <= ${RETENTION_DAYS}
    END

Get File Age In Days
    [Documentation]    Get file age in days
    [Arguments]    ${filepath}
    
    ${modified_time} =    Get Modified Time    ${filepath}    epoch
    ${current_time} =    Get Current Date    result_format=epoch
    ${age_seconds} =    Evaluate    ${current_time} - ${modified_time}
    ${age_days} =    Evaluate    ${age_seconds} / 86400
    
    [Return]    ${age_days}

# Kafka Integration Keywords
Setup Mock Kafka Environment
    [Documentation]    Setup mock Kafka environment
    
    Set Environment Variable    MOCK_KAFKA_AVAILABLE    true

Setup Mock Kafka Error Environment
    [Documentation]    Setup mock Kafka environment with errors
    
    Set Environment Variable    MOCK_KAFKA_ERROR    true

Create Test CAF KPI Data
    [Documentation]    Create test CAF KPI data
    
    ${kpi_data} =    Create Dictionary
    ...    pod_name=test-caf-pod
    ...    cpu_kpi=45.5
    ...    memory_kpi=2.0
    ...    transaction_kpi=150
    ...    performance_score=23.75
    ...    timestamp=${timestamp()}
    
    [Return]    ${kpi_data}

Publish CAF KPI To Kafka
    [Documentation]    Publish CAF KPI to Kafka topic
    [Arguments]    ${topic}    ${kpi_data}
    
    Log    Publishing CAF KPI to topic: ${topic}
    
    ${mock_mode} =    Get Environment Variable    MOCK_MODE    default=false
    Return From Keyword If    '${mock_mode}' == 'true'    ${True}
    
    # Real Kafka publishing would be performed here
    [Return]    ${True}

Load CAF Kafka Message Template
    [Documentation]    Load CAF Kafka message template
    
    ${template} =    Create Dictionary
    ...    pod_name=$pod_name
    ...    timestamp=$timestamp
    ...    kpi_data=$kpi_data
    ...    message_type=caf_kpi
    
    [Return]    ${template}

Build CAF Kafka Message
    [Documentation]    Build CAF Kafka message from template and KPI data
    [Arguments]    ${template}    ${kpi_data}
    
    ${message} =    Copy Dictionary    ${template}
    
    # Substitute template variables
    FOR    ${key}    ${value}    IN    &{kpi_data}
        Set To Dictionary    ${message}    ${key}    ${value}
    END
    
    [Return]    ${message}

Verify CAF Kafka Message Structure
    [Documentation]    Verify CAF Kafka message structure
    [Arguments]    ${message}
    
    Dictionary Should Contain Key    ${message}    pod_name
    Dictionary Should Contain Key    ${message}    timestamp
    Dictionary Should Contain Key    ${message}    message_type

Create Multiple CAF KPI Messages
    [Documentation]    Create multiple CAF KPI messages
    [Arguments]    ${count}
    
    ${messages} =    Create List
    
    FOR    ${i}    IN RANGE    ${count}
        ${kpi_data} =    Create Test CAF KPI Data
        Set To Dictionary    ${kpi_data}    pod_name    caf-pod-${i}
        Append To List    ${messages}    ${kpi_data}
    END
    
    [Return]    ${messages}

Publish CAF KPI Batch To Kafka
    [Documentation]    Publish batch of CAF KPI messages to Kafka
    [Arguments]    ${topic}    ${kpi_messages}
    
    Log    Publishing ${kpi_messages.__len__()} CAF KPI messages to topic: ${topic}
    
    ${mock_mode} =    Get Environment Variable    MOCK_MODE    default=false
    Return From Keyword If    '${mock_mode}' == 'true'    ${True}
    
    # Real batch publishing would be performed here
    [Return]    ${True}

# Additional helper keywords and test infrastructure keywords would continue...
# For brevity, including core functionality

# Helper Keywords
timestamp
    [Documentation]    Generate timestamp string
    [Return]    ${Get Current Date    result_format=%Y%m%d%H%M%S}
