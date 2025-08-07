# Air Health Check - Unit Tests

This directory contains comprehensive unit tests for the Air Health Check module.

## Overview

The Air Health Check module monitors the health status of Air Pods in a Kubernetes cluster and provides an HTTP API to check their status. The test suite covers all major components and functionality.

## Test Structure

### Test Files

1. **`test_app.py`** - Tests for the Flask application (`app.py`)
   - HTTP endpoint testing
   - Result caching mechanism
   - Logging setup
   - JSON file reading
   - Error handling

2. **`test_command_executor.py`** - Tests for the CommandExecutor class
   - Pod health status checking
   - Command execution and parsing
   - Percentage calculations
   - Envoy pod status checking
   - Error handling and edge cases

3. **`test_namespace.py`** - Tests for the Namespace utility module
   - Application namespace retrieval
   - Adaptation namespace retrieval
   - Command execution utilities
   - Error handling

4. **`test_integration.py`** - Integration tests
   - End-to-end testing of complete workflows
   - HTTP request to response testing
   - Multiple component interaction testing
   - Real-world scenario simulation

5. **`test_runner.py`** - Test suite runner
   - Runs all tests with detailed reporting
   - Provides test summary and statistics

## Running Tests

### Prerequisites

1. **Install Dependencies** (if using optional tools):
   ```bash
   pip install -r tests/requirements.txt
   ```

### Running All Tests

1. **Using the Test Runner**:
   ```bash
   cd air_health_check
   python tests/test_runner.py
   ```

2. **Using Python unittest directly**:
   ```bash
   cd air_health_check
   python -m unittest discover tests -v
   ```

3. **Using pytest** (if installed):
   ```bash
   cd air_health_check
   pytest tests/ -v
   ```

### Running Individual Test Files

```bash
# Test app.py
python -m unittest tests.test_app -v

# Test CommandExecutor
python -m unittest tests.test_command_executor -v

# Test Namespace utilities
python -m unittest tests.test_namespace -v

# Test integration scenarios
python -m unittest tests.test_integration -v
```

### Running Specific Test Cases

```bash
# Run a specific test class
python -m unittest tests.test_app.TestApp -v

# Run a specific test method
python -m unittest tests.test_app.TestApp.test_http_get_air_pod_health_status -v
```

## Test Coverage

### App Module (`app.py`)
- ✅ HTTP endpoint `/air_pod/status`
- ✅ Health status retrieval
- ✅ Result caching with time-based refresh
- ✅ Logging configuration
- ✅ JSON file reading
- ✅ Error handling

### CommandExecutor Module (`CommandExecutor.py`)
- ✅ Initialization with different configurations
- ✅ Command execution and output parsing
- ✅ Pod health status analysis
- ✅ Cluster IP retrieval
- ✅ Envoy pod status checking
- ✅ Percentage calculations
- ✅ Threshold-based health determination
- ✅ Test mode functionality
- ✅ Error handling and edge cases

### Namespace Module (`lib/Namespace.py`)
- ✅ Application namespace retrieval
- ✅ Adaptation namespace retrieval
- ✅ Command execution utilities
- ✅ Error handling

### Integration Testing
- ✅ Complete healthy pod scenario
- ✅ Unhealthy pods below threshold
- ✅ Unhealthy envoy pods
- ✅ Command execution failures
- ✅ Caching mechanism
- ✅ End-to-end HTTP workflows

## Mocking Strategy

The tests use Python's `unittest.mock` to mock external dependencies:

- **Subprocess calls** - Mocked to simulate kubectl command outputs
- **File operations** - Mocked for configuration file reading
- **Network calls** - Not applicable (no external network calls)
- **System calls** - Mocked namespace retrieval
- **Time-based operations** - Mocked for cache testing

## Test Scenarios

### Healthy Scenarios
- All pods are running and above threshold
- Envoy pods are healthy
- Cluster IP is accessible

### Unhealthy Scenarios
- Pods below threshold percentage
- Envoy pods are unhealthy
- Command execution failures
- Configuration file errors

### Edge Cases
- Empty command outputs
- Zero pod counts
- Division by zero in percentage calculations
- File not found errors
- Network timeouts (simulated)

## Expected Test Results

When all tests pass, you should see output similar to:

```
test_calculate_percentage (__main__.TestCommandExecutor) ... ok
test_execute_command_air_pod_quality_check (__main__.TestCommandExecutor) ... ok
test_execute_command_cluster_ip (__main__.TestCommandExecutor) ... ok
test_fetch_result_cached_data (__main__.TestApp) ... ok
test_fetch_result_fresh_data (__main__.TestApp) ... ok
test_full_healthy_scenario (__main__.TestAirHealthCheckIntegration) ... ok
test_get_application_namespace_success (__main__.TestNamespace) ... ok
test_http_get_air_pod_health_status (__main__.TestApp) ... ok
...

==================================================
TEST SUMMARY
==================================================
Tests run: 45
Failures: 0
Errors: 0
Success rate: 100.0%
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure you're running tests from the correct directory
   - Check that the `lib` module is accessible
   - Verify Python path includes parent directories

2. **Mock Issues**:
   - Ensure mock patches are correctly applied
   - Check that mocked objects return expected data types
   - Verify mock assertions match actual calls

3. **Path Issues**:
   - Use absolute paths when possible
   - Ensure test files can import the modules being tested

### Debug Mode

To run tests with more verbose output:

```bash
python tests/test_runner.py --verbose
```

Or with unittest:

```bash
python -m unittest discover tests -v --locals
```

## Contributing

When adding new functionality to the Air Health Check module:

1. Add corresponding test cases
2. Ensure tests cover both success and failure scenarios
3. Update this README if new test files are added
4. Maintain the same mocking patterns for consistency
5. Run the full test suite before committing changes

## Test Data

The tests use predefined mock data that simulates real kubectl command outputs:

- Pod status outputs with various states
- Cluster IP responses
- Envoy health check responses
- Configuration file contents

This ensures tests are predictable and don't depend on actual Kubernetes cluster state.
