@echo off
REM KAFKA_SDP_POSTPAID Test Runner for Windows
REM This script runs all unit tests for the KAFKA_SDP_POSTPAID module

echo ========================================================
echo KAFKA_SDP_POSTPAID - Unit Test Runner
echo ========================================================
echo.

REM Change to the KAFKA_SDP_POSTPAID directory
cd /d "%~dp0.."

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found. Make sure you're running this from the KAFKA_SDP_POSTPAID directory.
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

REM Option 1: Run basic tests (most reliable)
echo [1] Running basic tests (most reliable)...
echo --------------------------------------------------------
python tests\test_basic.py
echo.

REM Option 2: Run safe function tests  
echo [2] Running safe function tests...
echo --------------------------------------------------------
python tests\test_safe_functions.py
echo.

REM Option 3: Run all tests using test runner
echo [3] Running all tests using test runner...
echo --------------------------------------------------------
python tests\run_tests.py
echo.

REM Check if tests passed
if %ERRORLEVEL% neq 0 (
    echo.
    echo ⚠️ Some tests failed. Check the output above for details.
    echo.
) else (
    echo.
    echo ✅ All tests completed successfully!
    echo.
)

REM Option 4: Run with pytest if available
echo [4] Attempting to run with pytest (if available)...
echo --------------------------------------------------------
python -m pytest --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Running with pytest...
    python -m pytest tests/ -v
) else (
    echo pytest not available, skipping advanced test features.
    echo To install pytest: pip install pytest
)

echo.
echo ========================================================
echo Test run complete.
echo ========================================================
echo.
echo Usage:
echo   run_tests.bat           - Run all tests
echo   python tests\run_tests.py --verbose  - Verbose output
echo   python tests\run_tests.py --test-file test_basic.py  - Run specific test
echo.
echo Press any key to close...
pause >nul
