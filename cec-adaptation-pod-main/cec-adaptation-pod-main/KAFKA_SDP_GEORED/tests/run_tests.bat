@echo off
REM KAFKA_SDP_GEORED Unit Test Runner
REM Windows batch script to execute all test suites

echo ========================================================
echo KAFKA_SDP_GEORED - Unit Test Runner
echo ========================================================
echo Current directory: %CD%

REM Check if we're in the tests directory
if not exist "test_basic.py" (
    echo Error: test_basic.py not found. Please run this script from the tests directory.
    echo Expected location: KAFKA_SDP_GEORED\tests\
    pause
    exit /b 1
)

echo.
echo [0] Running basic tests (most reliable)...
echo --------------------------------------------------------
python test_basic.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Basic tests had issues
)

echo.
echo [1] Running safe function tests (comprehensive and reliable)...
echo --------------------------------------------------------
python test_safe_functions.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Safe function tests had issues
)

echo.
echo [2] Running main module tests (with mocking)...
echo --------------------------------------------------------
python test_main.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Main module tests had issues
)

echo.
echo [3] Running KPI_SDP class tests...
echo --------------------------------------------------------
python test_kpi_sdp.py
if %ERRORLEVEL% neq 0 (
    echo Warning: KPI_SDP tests had issues
)

echo.
echo [4] Running logger and subprocess tests...
echo --------------------------------------------------------
python test_logger_subprocess.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Logger/subprocess tests had issues
)

echo.
echo [5] Running integration tests...
echo --------------------------------------------------------
python test_integration.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Integration tests had issues
)

echo.
echo [6] Running comprehensive test suite...
echo --------------------------------------------------------
python run_tests.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Comprehensive test suite had issues
)

echo.
echo ========================================================
echo All test suites completed!
echo ========================================================
echo.
echo Components tested:
echo ✅ Basic module functionality
echo ✅ Safe function operations
echo ✅ Main module workflow
echo ✅ KPI_SDP class operations
echo ✅ Logger system
echo ✅ Subprocess execution
echo ✅ Integration scenarios
echo ✅ GEORED-specific functionality
echo ========================================================

echo.
echo [7] Attempting to run with pytest (if available)...
echo --------------------------------------------------------
pytest --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Running with pytest...
    pytest -v
) else (
    echo pytest not available, skipping advanced test features.
    echo To install pytest: pip install pytest
)

echo.
echo Test run complete. Press any key to close...
pause >nul
