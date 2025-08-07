# KAFKA_SDP_PREPAID - Unit Tests

This directory contains comprehensive unit tests for the KAFKA_SDP_PREPAID module.

## Overview

The KAFKA_SDP_PREPAID module is responsible for collecting SDP (Service Data Point) KPIs from Kubernetes pods and sending them to Kafka. The test suite covers all major components and functionality.

## Test Structure

### Test Files

1. **`test_main.py`** - Tests for the main application (`main.py`)
   - Argument parsing
   - Configuration loading
   - Pod discovery and filtering
   - Process execution
   - Directory management
   - Error handling

2. **`test_kpi_sdp.py`** - Tests for the KPI_SDP class
   - Initialization and setup
   - Command execution and formatting
   - KPI data collection and processing
   - Date/time calculations
   - Kubectl command integration
   - Error handling

3. **`test_logger.py`** - Tests for the LoggingHandler class
   - Logger initialization
   - Configuration parameters
   - File naming and formatting
   - Static method functionality

4. **`test_subprocess_class.py`** - Tests for the SubprocessClass
   - Command execution (with and without shell)
   - Process management and cleanup
   - Error handling and exceptions
   - Unicode and large output handling

5. **`test_runner.py`** - Comprehensive test suite runner
   - Integration tests
   - Module import validation
   - Configuration file checks
   - Cross-component functionality

## Running Tests

### Prerequisites

1. **Install Dependencies** (if using optional tools):
   ```bash
   pip install -r tests/requirements.txt
   ```

### Running All Tests

1. **Using the Test Runner**:
   ```bash
   cd KAFKA_SDP_PREPAID
   python tests\test_runner.py
   ```

2. **Using the Batch Script**:
   ```bash
   cd KAFKA_SDP_PREPAID
   tests\run_tests.bat
   ```

3. **Using Python unittest directly**:
   ```bash
   cd KAFKA_SDP_PREPAID
   python -m unittest discover tests -v
   ```

4. **Using pytest** (if installed):
   ```bash
   cd KAFKA_SDP_PREPAID
   pytest tests/ -v
   ```

### Running Individual Test Files

```bash
# Test main.py
python -m unittest tests.test_main -v

# Test KPI_SDP
python -m unittest tests.test_kpi_sdp -v

# Test Logger
python -m unittest tests.test_logger -v

# Test SubprocessClass
python -m unittest tests.test_subprocess_class -v
```

### Running Specific Test Cases

```bash
# Run a specific test class
python -m unittest tests.test_main.TestMain -v

# Run a specific test method
python -m unittest tests.test_main.TestMain.test_timestamp -v
```

## Test Coverage

### Main Module (`main.py`)
- ✅ Command line argument parsing
- ✅ Configuration file loading and validation
- ✅ Pod discovery from Kubernetes
- ✅ Pod filtering (whitelist/blacklist)
- ✅ Directory creation and management
- ✅ Process execution and management
- ✅ Error handling and logging
- ✅ Timestamp generation
- ✅ Hostname fetching

### KPI_SDP Module (`KPI_SDP.py`)
- ✅ Class initialization and setup
- ✅ Date/time calculations
- ✅ Command formatting and execution
- ✅ Kubectl command integration
- ✅ KPI data collection methods
- ✅ CIP/DCIP peer status checking
- ✅ Error handling and logging
- ✅ Special character handling in commands

### Logger Module (`Logger.py`)
- ✅ Logger initialization
- ✅ Configuration parameters
- ✅ File naming with date stamps
- ✅ Static method functionality
- ✅ Multiple logger instance handling

### SubprocessClass Module (`SubprocessClass.py`)
- ✅ Command execution with shell
- ✅ Command execution without shell
- ✅ Process cleanup and termination
- ✅ Error handling and exceptions
- ✅ Unicode character support
- ✅ Large output handling
- ✅ Process killing functionality

## Mocking Strategy

The tests use Python's `unittest.mock` to mock external dependencies:

- **Subprocess calls** - Mocked to simulate kubectl and system commands
- **File operations** - Mocked for configuration file reading
- **Process management** - Mocked for process execution and cleanup
- **Logging system** - Mocked to prevent actual log file creation
- **Time-based operations** - Mocked for consistent testing

## Test Scenarios

### Healthy Scenarios
- All pods are discovered and processed successfully
- Configuration files are valid and readable
- Commands execute successfully with expected output
- KPI data is collected and formatted correctly

### Unhealthy Scenarios
- No pods found in namespace
- Configuration file errors or missing files
- Command execution failures
- Process termination issues
- Network or connectivity problems

### Edge Cases
- Empty command outputs
- Unicode characters in output
- Large data volumes
- Process cleanup failures
- Invalid configuration parameters

## Expected Test Results

When all tests pass, you should see output similar to:

```
======================================================================
KAFKA_SDP_PREPAID TEST SUMMARY
======================================================================
Tests run: 85+
Failures: 0
Errors: 0
Success rate: 100.0%

Validated Components:
✅ Main module functionality
✅ KPI_SDP class operations
✅ Logging system
✅ Subprocess execution
✅ Configuration handling
✅ Pod parsing logic
✅ Command execution
✅ Error handling
======================================================================
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure you're running tests from the KAFKA_SDP_PREPAID directory
   - Check that all module dependencies are available
   - Verify Python path includes the current directory

2. **Mock Issues**:
   - Ensure mock patches are correctly applied
   - Check that mocked objects return expected data types
   - Verify mock assertions match actual calls

3. **Configuration Issues**:
   - Ensure config.json exists in the config directory
   - Check that configuration structure matches expected format

### Debug Mode

To run tests with more verbose output:

```bash
python -m unittest discover tests -v --locals
```

## Contributing

When adding new functionality to the KAFKA_SDP_PREPAID module:

1. Add corresponding test cases for new functions/methods
2. Ensure tests cover both success and failure scenarios
3. Update this README if new test files are added
4. Maintain the same mocking patterns for consistency
5. Run the full test suite before committing changes

## Test Data

The tests use predefined mock data that simulates real environments:

- Kubernetes pod listings with various states
- Configuration file contents
- Command outputs from kubectl and system commands
- KPI data collection results

This ensures tests are predictable and don't depend on actual Kubernetes cluster state or external systems.

## Integration with CI/CD

The test suite is designed to be easily integrated with CI/CD pipelines:

- Exit codes properly indicate test success/failure
- Comprehensive output for debugging
- No external dependencies during testing
- Cross-platform compatibility (Windows/Linux)
