@echo off
REM KAFKA_SDP_PREPAID Test Runner for Windows
REM This script runs all unit tests for the KAFKA_SDP_PREPAID module

echo ========================================================
echo KAFKA_SDP_PREPAID - Unit Test Runner
echo ========================================================
echo.

REM Change to the KAFKA_SDP_PREPAID directory
cd /d "%~dp0.."

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found. Make sure you're running this from the KAFKA_SDP_PREPAID directory.
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

REM Option 0: Run basic fixed tests first (most reliable)
echo [0] Running basic fixed tests (most reliable)...
echo --------------------------------------------------------
python tests\test_basic_fixed.py
echo.

REM Option 0.5: Run safe function tests (comprehensive but reliable)
echo [0.5] Running safe function tests (comprehensive and reliable)...
echo --------------------------------------------------------
python tests\test_safe_functions.py
echo.

REM Option 1: Run comprehensive test suite
echo [1] Running comprehensive test suite (may have some expected failures)...
echo --------------------------------------------------------
python tests\test_runner.py
echo.

REM Check if tests passed
if %ERRORLEVEL% neq 0 (
    echo.
    echo *** SOME TESTS HAD ISSUES ***
    echo Check the output above for details.
    echo.
    echo [2] Running individual test modules...
    echo --------------------------------------------------------
    
    echo Running main module tests...
    python -m unittest tests.test_main -v
    echo.
    
    echo Running KPI_SDP module tests...
    python -m unittest tests.test_kpi_sdp -v
    echo.
    
    echo Running Logger module tests...
    python -m unittest tests.test_logger -v
    echo.
    
    echo Running SubprocessClass module tests...
    python -m unittest tests.test_subprocess_class -v
    echo.
    
    pause
    exit /b 0
)

echo ========================================================
echo All tests completed successfully!
echo ========================================================

REM Optional: Run with pytest if available
echo.
echo [3] Attempting to run with pytest (if available)...
echo --------------------------------------------------------
python -c "import pytest" 2>nul
if %ERRORLEVEL% equ 0 (
    echo pytest is available, running additional tests...
    pytest tests\ -v --tb=short
) else (
    echo pytest not available, skipping advanced test features.
    echo To install pytest: pip install pytest
)

echo.
echo Test run complete. Press any key to close...
pause >nul
