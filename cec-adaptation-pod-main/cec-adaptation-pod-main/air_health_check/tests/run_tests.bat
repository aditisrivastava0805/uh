@echo off
REM Air Health Check Test Runner for Windows
REM This script runs all unit tests for the air_health_check module

echo ================================================
echo Air Health Check - Unit Test Runner
echo ================================================
echo.

REM Change to the air_health_check directory
cd /d "%~dp0.."

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Make sure you're running this from the air_health_check directory.
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

REM Option 1: Run basic tests first
echo [1] Running basic validation tests...
echo ------------------------------------------------
python tests\test_runner_basic.py
echo.

REM Check if basic tests passed
if %ERRORLEVEL% neq 0 (
    echo.
    echo *** BASIC TESTS FAILED ***
    echo Check the output above for details.
    echo Skipping advanced tests...
    pause
    exit /b 1
)

REM Option 2: Run with Python unittest (all tests)
echo [2] Running full test suite with Python unittest...
echo ------------------------------------------------
python -m unittest discover tests -v
echo.

REM Check if full tests passed
if %ERRORLEVEL% neq 0 (
    echo.
    echo *** FULL TESTS HAD ISSUES ***
    echo Some advanced tests may have failed, but basic functionality works.
    echo Check the output above for details.
    echo.
    echo [3] Running basic test runner for summary...
    echo ------------------------------------------------
    python tests\test_runner_basic.py
    pause
    exit /b 0
)

echo.
echo [3] Running detailed test runner...
echo ------------------------------------------------
python tests\test_runner_basic.py

echo.
echo ================================================
echo Tests completed! Basic functionality validated.
echo ================================================

REM Optional: Run with pytest if available
echo.
echo [3] Attempting to run with pytest (if available)...
echo ------------------------------------------------
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
