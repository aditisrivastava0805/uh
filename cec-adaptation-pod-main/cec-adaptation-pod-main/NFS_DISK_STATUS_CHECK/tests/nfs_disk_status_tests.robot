*** Settings ***
Documentation    Comprehensive Robot Framework test suite for NFS_DISK_STATUS_CHECK module
...              Tests disk space monitoring, file cleanup operations, configuration management,
...              threshold checking, error handling, and storage management.

Resource         nfs_disk_status_resource.robot
Test Setup       Setup NFS_DISK_STATUS_CHECK Test Environment  
Test Teardown    Teardown NFS_DISK_STATUS_CHECK Test Environment
Force Tags       nfs_disk_status    storage

*** Test Cases ***

Test NFS_DISK_STATUS_CHECK Module Structure
    [Documentation]    Verify NFS_DISK_STATUS_CHECK module has all required files
    [Tags]    structure    smoke
    Verify NFS_DISK_STATUS_CHECK Module Structure

Test Disk Configuration Loading
    [Documentation]    Test loading and validation of disk configuration files
    [Tags]    configuration    unit
    [Setup]    Create Test Configuration Files
    Verify Configuration Loading    ${TEST_CONFIG_FILE}
    Verify Disk Configuration Parameters

Test Disk Usage Monitoring
    [Documentation]    Test disk usage monitoring functionality
    [Tags]    monitoring    integration
    ${test_dir}=    Create Test Directory With Files
    ${usage}=    Get Disk Usage    ${test_dir}
    Should Be True    ${usage} >= 0
    Should Be True    ${usage} <= 100

Test Disk Space Calculation
    [Documentation]    Test disk space calculation and percentage computation
    [Tags]    calculation    unit
    ${test_dir}=    Create Test Directory With Files
    Test Disk Space Calculation    ${test_dir}
    Verify Percentage Calculation Accuracy

Test File Size Monitoring
    [Documentation]    Test file size monitoring and tracking
    [Tags]    file_monitoring    unit
    ${test_file}=    Create Large Test File    1MB
    ${size}=    Get File Size In Bytes    ${test_file}
    Should Be True    ${size} > 0
    Verify File Size Calculation    ${test_file}

Test Directory Path Handling
    [Documentation]    Test directory path handling and navigation
    [Tags]    path_handling    unit
    ${original_dir}=    Get Current Working Directory
    ${test_dir}=    Create Test Directory With Files
    Test Directory Navigation    ${test_dir}
    Verify Current Directory    ${test_dir}
    Change Directory    ${original_dir}

Test Disk Threshold Checking
    [Documentation]    Test disk usage threshold checking functionality
    [Tags]    threshold    business_logic
    ${test_dir}=    Create Test Directory With Files
    Test Threshold Checking    ${test_dir}    ${DEFAULT_THRESHOLD}
    Verify Threshold Alert Generation

Test File Cleanup Operations
    [Documentation]    Test file cleanup and deletion operations
    [Tags]    cleanup    integration
    ${test_files}=    Create Multiple Test Files    count=5
    Execute File Cleanup    ${test_files}
    Verify Files Deleted    ${test_files}

Test Cleanup Script Execution
    [Documentation]    Test complete execution of cleanup script
    [Tags]    main_execution    integration
    ${test_dir}=    Create Test Directory With High Usage
    ${result}=    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Should Be Equal As Integers    ${result.rc}    0
    Verify Cleanup Execution

Test Automatic File Removal
    [Documentation]    Test automatic file removal when threshold is exceeded
    [Tags]    auto_cleanup    integration
    ${test_dir}=    Create Test Directory With High Usage
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Space Freed    ${test_dir}

Test Configuration-Based Cleanup
    [Documentation]    Test cleanup based on configuration parameters
    [Tags]    config_cleanup    integration
    [Setup]    Create Custom Configuration
    ${test_dir}=    Create Test Directory With Files
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Configuration-Based Behavior

Test Error Handling - Invalid Path
    [Documentation]    Test error handling with invalid directory paths
    [Tags]    error_handling    negative
    Verify Error Handling    invalid_path    /nonexistent/path
    Verify Error Logging

Test Error Handling - Permission Denied
    [Documentation]    Test error handling when file permissions prevent operations
    [Tags]    error_handling    security
    ${protected_file}=    Create Protected Test File
    Verify Error Handling    permission_denied    ${protected_file}

Test Error Handling - Disk Full
    [Documentation]    Test error handling when disk is full
    [Tags]    error_handling    disk_full
    Verify Error Handling    disk_full_simulation

Test Error Handling - Configuration Missing
    [Documentation]    Test error handling when configuration file is missing
    [Tags]    error_handling    negative
    Verify Error Handling    missing_config

Test Logging Functionality
    [Documentation]    Test logging configuration and log file creation
    [Tags]    logging    unit
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Log File Creation
    Verify Log Content Structure
    Test Log Level Configuration

Test Performance With Large Files
    [Documentation]    Test performance when handling large files
    [Tags]    performance    non_functional
    ${large_file}=    Create Large Test File    100MB
    Monitor System Resources
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Performance Metrics    max_execution_time=30

Test Performance With Many Files
    [Documentation]    Test performance when handling many small files
    [Tags]    performance    scalability
    ${test_files}=    Create Multiple Test Files    count=1000
    Monitor System Resources
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Performance With Many Files

Test Concurrent Access Handling
    [Documentation]    Test handling of concurrent file access
    [Tags]    concurrency    reliability
    ${test_files}=    Create Multiple Test Files    count=10
    Test Concurrent File Operations    ${test_files}
    Verify File Integrity After Concurrent Access

Test Storage Space Recovery
    [Documentation]    Test storage space recovery after cleanup
    [Tags]    storage_recovery    integration
    ${test_dir}=    Create Test Directory With High Usage
    ${initial_usage}=    Get Disk Usage    ${test_dir}
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    ${final_usage}=    Get Disk Usage    ${test_dir}
    Should Be True    ${final_usage} < ${initial_usage}

Test File Age-Based Cleanup
    [Documentation]    Test cleanup based on file age criteria
    [Tags]    age_based_cleanup    business_logic
    ${old_files}=    Create Old Test Files    age_days=30
    ${new_files}=    Create New Test Files
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Old Files Removed    ${old_files}
    Verify New Files Preserved    ${new_files}

Test Size-Based Cleanup Priority
    [Documentation]    Test cleanup priority based on file sizes
    [Tags]    size_based_cleanup    business_logic
    ${large_files}=    Create Large Test Files    count=3
    ${small_files}=    Create Small Test Files    count=10
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Cleanup Priority Logic

Test Configuration Validation
    [Documentation]    Test validation of configuration parameters
    [Tags]    config_validation    unit
    Test Invalid Configuration Values
    Test Missing Configuration Keys
    Test Configuration Schema Validation
    Verify Default Values

Test Multiple Directory Monitoring
    [Documentation]    Test monitoring multiple directories simultaneously
    [Tags]    multi_directory    integration
    ${dir1}=    Create Test Directory With Files    name=test_dir1
    ${dir2}=    Create Test Directory With Files    name=test_dir2
    ${dir3}=    Create Test Directory With Files    name=test_dir3
    Test Multiple Directory Processing    ${dir1}    ${dir2}    ${dir3}

Test Custom Threshold Configuration
    [Documentation]    Test custom threshold configuration and behavior
    [Tags]    custom_threshold    configuration
    [Setup]    Create Custom Threshold Configuration    threshold=85
    ${test_dir}=    Create Test Directory With Medium Usage
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Custom Threshold Behavior

Test File Type Filtering
    [Documentation]    Test filtering files by type during cleanup
    [Tags]    file_filtering    business_logic
    ${log_files}=    Create Test Files By Type    .log    count=5
    ${tmp_files}=    Create Test Files By Type    .tmp    count=5
    ${data_files}=    Create Test Files By Type    .data    count=5
    Execute NFS_DISK_STATUS_CHECK Script
    Verify File Type Based Cleanup

Test Symbolic Link Handling
    [Documentation]    Test handling of symbolic links during cleanup
    [Tags]    symlink_handling    edge_case
    ${real_files}=    Create Test Files    count=3
    ${symlinks}=    Create Symbolic Links    ${real_files}
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Symbolic Link Handling

Test Nested Directory Cleanup
    [Documentation]    Test cleanup of nested directory structures
    [Tags]    nested_directories    integration
    ${nested_structure}=    Create Nested Directory Structure    depth=5
    Populate Nested Directories    ${nested_structure}
    Execute NFS_DISK_STATUS_CHECK Script
    Verify Nested Directory Cleanup

Test Backup Before Cleanup
    [Documentation]    Test backup functionality before file cleanup
    [Tags]    backup    data_safety
    ${test_files}=    Create Important Test Files    count=3
    Execute NFS_DISK_STATUS_CHECK Script    backup_mode=True
    Verify Files Backed Up Before Deletion

Test Cleanup Dry Run Mode
    [Documentation]    Test dry run mode that simulates cleanup without actual deletion
    [Tags]    dry_run    safety
    ${test_files}=    Create Test Files    count=5
    Execute NFS_DISK_STATUS_CHECK Script    dry_run=True
    Verify Files Not Deleted    ${test_files}
    Verify Dry Run Reporting

Test Real-time Monitoring
    [Documentation]    Test real-time disk usage monitoring
    [Tags]    real_time    monitoring
    Start Real Time Monitoring
    ${test_file}=    Create Large Test File    50MB
    Verify Real Time Updates
    Stop Real Time Monitoring

Test Alert Generation
    [Documentation]    Test alert generation when thresholds are exceeded
    [Tags]    alerts    monitoring
    ${test_dir}=    Create Test Directory With High Usage
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Alert Generation
    Verify Alert Content

Test Integration With System Tools
    [Documentation]    Test integration with system monitoring tools
    [Tags]    system_integration    integration
    Execute NFS_DISK_STATUS_CHECK Script
    Verify System Tool Integration
    Test Command Line Tool Usage

Test Storage Policy Enforcement
    [Documentation]    Test enforcement of storage policies
    [Tags]    policy_enforcement    compliance
    [Setup]    Create Storage Policy Configuration
    ${test_dir}=    Create Test Directory With Files
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Policy Enforcement

Test Cleanup Reporting
    [Documentation]    Test generation of cleanup reports
    [Tags]    reporting    monitoring
    ${test_dir}=    Create Test Directory With Files
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}
    Verify Cleanup Report Generation
    Verify Report Content Accuracy

Test Emergency Cleanup Mode
    [Documentation]    Test emergency cleanup when disk is critically full
    [Tags]    emergency_cleanup    critical
    ${test_dir}=    Create Test Directory With Critical Usage
    Execute NFS_DISK_STATUS_CHECK Script    ${test_dir}    emergency_mode=True
    Verify Emergency Cleanup Behavior

Test Configuration Hot Reload
    [Documentation]    Test hot reloading of configuration changes
    [Tags]    hot_reload    configuration
    Execute NFS_DISK_STATUS_CHECK Script
    Update Configuration During Runtime
    Verify Configuration Reload
    Verify New Configuration Applied
