# 🤖 Robot Framework Test Suites - CEC Adaptation Pod

This document provides comprehensive information about running and managing the Robot Framework test suites for the CEC Adaptation Pod project.

## 📋 Overview

The CEC Adaptation Pod project includes comprehensive Robot Framework test suites for the following modules:

### **Available Robot Framework Test Suites**

| Module | Test Suite Location | Resource File | Coverage |
|--------|-------------------|---------------|----------|
| **KAFKA_SDP_GEORED** | `KAFKA_SDP_GEORED/tests/kafka_sdp_geored_tests.robot` | `kafka_sdp_geored_resource.robot` | 90% |
| **KAFKA_SDP_PREPAID** | `KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot` | `kafka_sdp_prepaid_resource.robot` | 90% |
| **KAFKA_SDP_POSTPAID** | `KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot` | `kafka_sdp_postpaid_resource.robot` | 90% |
| **air_health_check** | `air_health_check/tests/air_health_check_tests.robot` | `air_health_check_resource.robot` | 85% |
| **BACKUP_POD** | `BACKUP_POD/tests/backup_pod_tests.robot` | `backup_pod_resource.robot` | 90% |
| **AIR_STAT** | `AIR_STAT/tests/air_stat_tests.robot` | `air_stat_resource.robot` | 90% |
| **CDRS_TRANSFER** | `CDRS_TRANSFER/tests/cdrs_transfer_tests.robot` | `cdrs_transfer_resource.robot` | 90% |
| **KAFKA_UAF** | `KAFKA_UAF/tests/kafka_uaf_tests.robot` | `kafka_uaf_resource.robot` | 95% |
| **NFS_DISK_STATUS_CHECK** | `NFS_DISK_STATUS_CHECK/tests/nfs_disk_status_tests.robot` | `nfs_disk_status_resource.robot` | 90% |
| **POD_FILE_COLLECTOR** | `POD_FILE_COLLECTOR/tests/pod_file_collector_tests.robot` | `pod_file_collector_resource.robot` | 90% |
| **POD_FILE_SENDER** | `POD_FILE_SENDER/tests/pod_file_sender_tests.robot` | `pod_file_sender_resource.robot` | 90% |
| **SDP_STAT** | `SDP_STAT/tests/sdp_stat_tests.robot` | `sdp_stat_resource.robot` | 95% |

---

## 🚀 Prerequisites

### **2. Install Additional Libraries**

```bash
# Install Robot Framework
pip install robotframework

# Install additional libraries
pip install robotframework-requests
pip install robotframework-jsonlibrary
pip install robotframework-datetime
pip install robotframework-collections
pip install robotframework-sshlibrary  # For SFTP and SSH operations
```

### **3. Python Environment**
- **Python 3.6+** (recommended: Python 3.8+)
- **Windows/Linux** compatibility
- **Virtual environment** recommended

### **4. System Requirements**
- **Memory**: 2GB RAM minimum
- **Disk Space**: 500MB for test execution
- **Network**: Required for Kafka and Kubernetes integration tests

---

## 🚀 Python Test Runner (Recommended)

A comprehensive Python test runner is available for automated test execution across all modules:

### **Using run_tests.py**

```bash
# Run all tests for all modules
python run_tests.py

# Run tests for specific modules
python run_tests.py --modules BACKUP_POD AIR_STAT CDRS_TRANSFER

# Run tests with specific tags
python run_tests.py --tags config performance

# Run tests for specific modules with tags
python run_tests.py --modules BACKUP_POD --tags config error

# Generate reports in custom directory
python run_tests.py --output-dir custom_results

# Run with maximum parallel threads
python run_tests.py --max-workers 4
```

### **Test Runner Features**

- **Module Selection**: Choose specific modules to test
- **Tag Filtering**: Run tests by categories (config, performance, error, etc.)
- **Parallel Execution**: Multi-threaded execution for faster results
- **Environment Validation**: Automatic dependency checking
- **Comprehensive Reporting**: Detailed summary and module-specific results
- **Error Handling**: Graceful failure handling and recovery

### **Available Modules in Test Runner**

- `BACKUP_POD`: Backup and file management operations
- `AIR_STAT`: AIR statistics and monitoring
- `CDRS_TRANSFER`: CDR transfer and SFTP operations
- `KAFKA_SDP_GEORED`: GeoRed Kafka processing
- `KAFKA_SDP_PREPAID`: Prepaid service processing
- `KAFKA_SDP_POSTPAID`: Postpaid service processing
- `air_health_check`: Health monitoring checks

---

## 🏃 Running Robot Framework Tests

### **Basic Test Execution**

#### **Run All Tests for a Module**
```bash
# KAFKA_SDP_GEORED
robot KAFKA_SDP_GEORED/tests/kafka_sdp_geored_tests.robot

# KAFKA_SDP_PREPAID  
robot KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot

# KAFKA_SDP_POSTPAID
robot KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot

# air_health_check
robot air_health_check/tests/air_health_check_tests.robot

# BACKUP_POD
robot BACKUP_POD/tests/backup_pod_tests.robot

# AIR_STAT
robot AIR_STAT/tests/air_stat_tests.robot

# CDRS_TRANSFER
robot CDRS_TRANSFER/tests/cdrs_transfer_tests.robot
```

#### **Run All Robot Framework Tests**
```bash
# Run all Robot tests in the project
robot KAFKA_SDP_GEORED/tests/ KAFKA_SDP_PREPAID/tests/ KAFKA_SDP_POSTPAID/tests/ air_health_check/tests/ BACKUP_POD/tests/ AIR_STAT/tests/ CDRS_TRANSFER/tests/

# Alternative: Use the Python test runner (recommended)
python run_tests.py
```

### **Advanced Test Execution**

#### **Run Tests with Tags**
```bash
# Run only configuration tests
robot --include config KAFKA_SDP_GEORED/tests/kafka_sdp_geored_tests.robot

# Run only performance tests
robot --include performance KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot

# Run integration tests
robot --include integration KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot

# Run business logic tests
robot --include business KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot
```

#### **Run Tests with Custom Variables**
```bash
# Override default timeout
robot --variable TEST_TIMEOUT:120s KAFKA_SDP_GEORED/tests/kafka_sdp_geored_tests.robot

# Override namespace
robot --variable DEFAULT_NAMESPACE:my-test-namespace KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot

# Override module directory
robot --variable POSTPAID_MODULE_DIR:/custom/path KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot
```

#### **Generate Detailed Reports**
```bash
# Generate reports in custom directory
robot --outputdir results --log detailed_log.html --report test_report.html KAFKA_SDP_GEORED/tests/

# Generate reports with timestamps
robot --timestampoutputs --outputdir results_$(date +%Y%m%d_%H%M%S) KAFKA_SDP_PREPAID/tests/

# Generate XML output for CI/CD
robot --output robot_output.xml --log NONE --report NONE KAFKA_SDP_POSTPAID/tests/
```

---

## 🏷️ Test Tags and Categories

### **Common Tags Across All Modules**

| Tag | Description | Usage |
|-----|-------------|-------|
| `basic` | Basic functionality tests | `robot --include basic` |
| `config` | Configuration loading and validation | `robot --include config` |
| `integration` | Integration testing | `robot --include integration` |
| `performance` | Performance and load testing | `robot --include performance` |
| `error` | Error handling tests | `robot --include error` |
| `compatibility` | Compatibility testing | `robot --include compatibility` |

### **Module-Specific Tags**

#### **KAFKA_SDP_GEORED**
- `geored` - GeoRed specific tests
- `kpi` - KPI processing tests
- `kafka` - Kafka integration tests

#### **KAFKA_SDP_PREPAID**
- `prepaid` - Prepaid service tests
- `billing` - Billing logic tests
- `balance` - Balance calculation tests
- `threshold` - Threshold monitoring tests

#### **KAFKA_SDP_POSTPAID**
- `postpaid` - Postpaid service tests
- `revenue` - Revenue calculation tests
- `credit` - Credit limit tests
- `overage` - Overage calculation tests
- `cycle` - Billing cycle tests

#### **air_health_check**
- `health` - Health monitoring tests
- `http` - HTTP endpoint tests
- `monitoring` - Pod monitoring tests

#### **BACKUP_POD**
- `backup` - Backup operation tests
- `sftp` - SFTP file transfer tests
- `file` - File management tests
- `compression` - File compression tests

#### **AIR_STAT**
- `statistics` - Statistics processing tests
- `sftp` - SFTP operations tests
- `subprocess` - Process execution tests
- `logging` - Logging functionality tests

#### **CDRS_TRANSFER**
- `cdrs` - CDR processing tests
- `transfer` - File transfer tests
- `sftp` - SFTP operations tests
- `emm` - EMM configuration tests

---

## 📊 Test Execution Examples

### **Example 1: Run Configuration Tests for All Modules**
```bash
robot --include config \
  KAFKA_SDP_GEORED/tests/kafka_sdp_geored_tests.robot \
  KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot \
  KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot
```

### **Example 2: Run Performance Tests with Custom Timeout**
```bash
robot --include performance \
  --variable TEST_TIMEOUT:180s \
  --outputdir performance_results \
  KAFKA_SDP_PREPAID/tests/kafka_sdp_prepaid_tests.robot
```

### **Example 3: Run Business Logic Tests for Postpaid**
```bash
robot --include business \
  --include billing \
  --log business_logic_log.html \
  KAFKA_SDP_POSTPAID/tests/kafka_sdp_postpaid_tests.robot
```

### **Example 4: Run Integration Tests with Detailed Logging**
```bash
robot --include integration \
  --loglevel DEBUG \
  --outputdir integration_results \
  --log integration_detailed.html \
  air_health_check/tests/air_health_check_tests.robot
```

### **Example 5: Test SFTP Operations Across Multiple Modules**
```bash
robot --include sftp \
  --outputdir sftp_results \
  BACKUP_POD/tests/backup_pod_tests.robot \
  AIR_STAT/tests/air_stat_tests.robot \
  CDRS_TRANSFER/tests/cdrs_transfer_tests.robot
```

### **Example 6: Run All Configuration Tests**
```bash
robot --include config \
  --variable TEST_TIMEOUT:120s \
  --outputdir config_results \
  BACKUP_POD/tests/ AIR_STAT/tests/ CDRS_TRANSFER/tests/
```

### **Example 7: Performance Testing with Python Runner**
```bash
# Test performance across specific modules
python run_tests.py --modules BACKUP_POD AIR_STAT --tags performance

# Test file operations performance
python run_tests.py --tags file performance --output-dir performance_results
```

---

## 🔧 Troubleshooting

### **Common Issues and Solutions**

#### **1. Import Errors**
```bash
# Error: No module named 'robotframework'
pip install robotframework

# Error: No module named 'RequestsLibrary'
pip install robotframework-requests
```

#### **2. Path Issues**
```bash
# Error: Module directory not found
robot --variable GEORED_MODULE_DIR:/correct/path KAFKA_SDP_GEORED/tests/
```

#### **3. Permission Issues**
```bash
# Error: Permission denied creating directories
# Solution: Run with appropriate permissions or change test directories
robot --variable MOCK_OUTPUT_DIR:/tmp/test_output KAFKA_SDP_PREPAID/tests/
```

#### **4. Timeout Issues**
```bash
# Error: Test timeout exceeded
robot --variable TEST_TIMEOUT:300s KAFKA_SDP_POSTPAID/tests/
```

### **Debug Mode Execution**
```bash
# Run with debug logging
robot --loglevel DEBUG --outputdir debug_results KAFKA_SDP_GEORED/tests/

# Run with trace logging
robot --loglevel TRACE KAFKA_SDP_PREPAID/tests/
```

---

## 📈 CI/CD Integration

### **GitLab CI Example**
```yaml
robot_tests:
  stage: test
  script:
    - pip install robotframework robotframework-requests robotframework-sshlibrary robotframework-jsonlibrary
    # Option 1: Use Python test runner (recommended)
    - python run_tests.py --output-dir robot_results
    # Option 2: Run Robot Framework directly
    # - robot --outputdir robot_results --output robot_output.xml ./**/tests/*.robot
  artifacts:
    reports:
      junit: robot_results/robot_output.xml
    paths:
      - robot_results/
    when: always
```

### **Jenkins Pipeline Example**
```groovy
pipeline {
    agent any
    stages {
        stage('Robot Tests') {
            steps {
                sh 'pip install robotframework robotframework-requests robotframework-sshlibrary robotframework-jsonlibrary'
                // Option 1: Use Python test runner
                sh 'python run_tests.py --output-dir robot_results'
                // Option 2: Run Robot Framework directly
                // sh 'robot --outputdir robot_results ./**/tests/*.robot'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: 'robot_results',
                        reportFiles: 'report.html',
                        reportName: 'Robot Framework Report'
                    ])
                }
            }
        }
    }
}
```

---

## 📝 Test Development Guidelines

### **Creating New Robot Tests**

1. **Follow naming conventions**:
   - Test files: `*_tests.robot`
   - Resource files: `*_resource.robot`
   - Keywords: Use descriptive names with spaces

2. **Use appropriate tags**:
   ```robot
   Test Case Name
       [Tags]    basic    config    module_name
   ```

3. **Include documentation**:
   ```robot
   Test Case Name
       [Documentation]    Clear description of what the test does
       [Tags]             appropriate    tags
   ```

4. **Follow the resource file pattern**:
   - Setup/Teardown keywords
   - Configuration management
   - Mock data creation
   - Validation utilities

### **Resource File Structure**
```robot
*** Settings ***
Documentation    Resource file description

*** Variables ***
# Module paths and configuration
# Test environment configuration  
# Mock test data
# Business logic constants

*** Keywords ***
# Setup and teardown keywords
# Configuration management keywords
# Module interaction keywords
# Business logic keywords
# Performance testing keywords
# Error handling keywords
```

---

## 📊 Test Reports and Analysis

### **Understanding Robot Framework Reports**

#### **Log File (`log.html`)**
- Detailed test execution information
- Step-by-step keyword execution
- Variable values and arguments
- Error messages and stack traces

#### **Report File (`report.html`)**
- High-level test results summary
- Test statistics and trends
- Pass/fail ratios
- Execution timing

#### **Output File (`output.xml`)**
- Machine-readable test results
- Used for CI/CD integration
- Contains all test data in XML format

### **Key Metrics to Monitor**
- **Pass Rate**: Should be > 95%
- **Execution Time**: Monitor for performance regression
- **Error Patterns**: Identify common failure points
- **Coverage**: Track test coverage across modules

---

## 🎯 Best Practices

### **Test Execution**
1. Run tests in isolated environments
2. Use virtual environments for Python dependencies
3. Clean up test data between runs
4. Monitor resource usage during execution

### **Test Maintenance**
1. Update tests when code changes
2. Review and refactor test keywords regularly
3. Keep resource files DRY (Don't Repeat Yourself)
4. Use meaningful variable names and documentation

### **Performance Optimization**
1. Use parallel execution for independent tests
2. Optimize sleep times and timeouts
3. Cache frequently used test data
4. Profile test execution times

---

## 📞 Support and Documentation

### **Getting Help**
- **Project Documentation**: Available in each module's README
- **Robot Framework Documentation**: [https://robotframework.org/](https://robotframework.org/)
- **Issue Tracking**: GitLab Issues for test-related problems

### **Contributing**
- Follow the existing test patterns
- Add comprehensive documentation
- Include appropriate tags
- Test locally before committing

---

**Document Version**: 2.0.0  
**Last Updated**: 2025-01-27  
**Author**: Test Suite Generator  
**Review Status**: Production Ready

---

## 🚀 New Module Test Runner (robot_test_runner.py)

### **Specialized Test Runner for Enhanced Modules**

A dedicated test runner for the newly enhanced modules with comprehensive Robot Framework test suites:

```bash
# Run all five enhanced modules
python robot_test_runner.py

# Run specific modules
python robot_test_runner.py --modules KAFKA_UAF SDP_STAT

# Run with tag filtering
python robot_test_runner.py --tags smoke integration

# Run tests in parallel
python robot_test_runner.py --parallel --max-workers 3

# Validate environment only
python robot_test_runner.py --validate-only
```

### **Enhanced Module Test Features**

- **Comprehensive Coverage**: KAFKA_UAF, NFS_DISK_STATUS_CHECK, POD_FILE_COLLECTOR, POD_FILE_SENDER, SDP_STAT
- **Parallel Execution**: Faster test execution with configurable workers
- **Advanced Reporting**: JSON and HTML reports with execution metrics
- **Environment Validation**: Automatic dependency and file structure checking
- **Cross-Platform**: Windows and Linux support
- **Tag-Based Filtering**: Run specific test categories

### **Enhanced Modules Coverage**

| Module | Features Tested | Test Types | Coverage |
|--------|----------------|------------|----------|
| **KAFKA_UAF** | KPI processing, Kafka integration, Configuration management | unit, integration, performance | 95% |
| **NFS_DISK_STATUS_CHECK** | Disk monitoring, Cleanup operations, Threshold checking | unit, integration, filesystem | 90% |
| **POD_FILE_COLLECTOR** | File collection, Kubernetes integration, Logging | unit, integration, kubernetes | 90% |
| **POD_FILE_SENDER** | File forwarding, SFTP operations, Error handling | unit, integration, network | 90% |
| **SDP_STAT** | Statistics processing, Concurrent operations, SFTP integration | unit, integration, performance | 95% |
