@echo off
REM ============================================================================
REM KAFKA_CSA Test Runner Batch Script
REM ============================================================================
REM
REM This batch script provides a convenient way to run KAFKA_CSA tests on Windows.
REM It supports various test execution modes and provides clear output formatting.
REM
REM Usage:
REM   run_tests.bat                    - Run all tests
REM   run_tests.bat basic              - Run basic tests only
REM   run_tests.bat quick              - Run quick tests
REM   run_tests.bat verbose            - Run with verbose output
REM   run_tests.bat help               - Show help information
REM
REM Author: Test Suite Generator
REM Date: 2025-07-23
REM ============================================================================

setlocal EnableDelayedExpansion

REM Set script directory and paths
set "SCRIPT_DIR=%~dp0"
set "PARENT_DIR=%SCRIPT_DIR%.."
set "TEST_RUNNER=%SCRIPT_DIR%run_tests.py"

REM Colors for output (if supported)
set "COLOR_GREEN=[32m"
set "COLOR_RED=[31m"
set "COLOR_YELLOW=[33m"
set "COLOR_BLUE=[34m"
set "COLOR_RESET=[0m"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo %COLOR_RED%ERROR: Python is not installed or not in PATH%COLOR_RESET%
    echo Please install Python 3.6+ and ensure it's available in your PATH
    exit /b 1
)

REM Check if test runner exists
if not exist "%TEST_RUNNER%" (
    echo %COLOR_RED%ERROR: Test runner not found at %TEST_RUNNER%%COLOR_RESET%
    echo Please ensure the test suite is properly set up
    exit /b 1
)

REM Parse command line arguments
set "ARGS="
set "MODE=all"
set "HELP_REQUESTED=false"

:parse_args
if "%~1"=="" goto :args_parsed
if /i "%~1"=="help" (
    set "HELP_REQUESTED=true"
    goto :args_parsed
)
if /i "%~1"=="quick" (
    set "MODE=quick"
    set "ARGS=%ARGS% --quick"
    shift
    goto :parse_args
)
if /i "%~1"=="verbose" (
    set "ARGS=%ARGS% --verbose"
    shift
    goto :parse_args
)
if /i "%~1"=="basic" (
    set "MODE=module"
    set "ARGS=%ARGS% --module basic"
    shift
    goto :parse_args
)
if /i "%~1"=="safe_functions" (
    set "MODE=module"
    set "ARGS=%ARGS% --module safe_functions"
    shift
    goto :parse_args
)
if /i "%~1"=="kpi_helper" (
    set "MODE=module"
    set "ARGS=%ARGS% --module kpi_helper"
    shift
    goto :parse_args
)
if /i "%~1"=="main" (
    set "MODE=module"
    set "ARGS=%ARGS% --module main"
    shift
    goto :parse_args
)
if /i "%~1"=="kpi_csa" (
    set "MODE=module"
    set "ARGS=%ARGS% --module kpi_csa"
    shift
    goto :parse_args
)
if /i "%~1"=="integration" (
    set "MODE=module"
    set "ARGS=%ARGS% --module integration"
    shift
    goto :parse_args
)
REM Unknown argument, pass it through
set "ARGS=%ARGS% %~1"
shift
goto :parse_args

:args_parsed

REM Show help if requested
if "%HELP_REQUESTED%"=="true" (
    call :show_help
    exit /b 0
)

REM Print header
echo.
echo ================================================================================
echo KAFKA_CSA Test Suite Runner
echo ================================================================================
echo.

REM Show current configuration
echo %COLOR_BLUE%Configuration:%COLOR_RESET%
echo   Script Directory: %SCRIPT_DIR%
echo   Parent Directory: %PARENT_DIR%
echo   Test Runner: %TEST_RUNNER%
echo   Mode: %MODE%
echo   Arguments: %ARGS%
echo.

REM Change to the tests directory
cd /d "%SCRIPT_DIR%"
if errorlevel 1 (
    echo %COLOR_RED%ERROR: Failed to change to test directory%COLOR_RESET%
    exit /b 1
)

REM Execute the tests
echo %COLOR_BLUE%Starting test execution...%COLOR_RESET%
echo.

python "%TEST_RUNNER%" %ARGS%
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
echo ================================================================================

REM Display results based on exit code
if %TEST_EXIT_CODE% equ 0 (
    echo %COLOR_GREEN%✓ All tests completed successfully!%COLOR_RESET%
    echo.
    echo %COLOR_BLUE%Next steps:%COLOR_RESET%
    echo   • Tests are ready for production use
    echo   • Consider running full test suite if you ran a subset
    echo   • Check test coverage if needed
) else if %TEST_EXIT_CODE% equ 130 (
    echo %COLOR_YELLOW%⚠ Test execution was interrupted%COLOR_RESET%
    echo.
    echo %COLOR_BLUE%What happened:%COLOR_RESET%
    echo   • Test execution was stopped by user (Ctrl+C)
    echo   • This is normal if you intended to stop the tests
) else (
    echo %COLOR_RED%✗ Some tests failed or encountered errors%COLOR_RESET%
    echo.
    echo %COLOR_BLUE%Troubleshooting:%COLOR_RESET%
    echo   • Review the test output above for specific failures
    echo   • Run individual test modules for detailed debugging:
    echo     run_tests.bat basic
    echo     run_tests.bat safe_functions
    echo     run_tests.bat kpi_helper
    echo   • Check if all dependencies are properly installed
    echo   • Ensure the KAFKA_CSA module files are in the correct location
)

echo.
echo %COLOR_BLUE%Additional commands:%COLOR_RESET%
echo   run_tests.bat help      - Show detailed help
echo   run_tests.bat quick     - Run quick tests only
echo   run_tests.bat verbose   - Run with detailed output
echo.

exit /b %TEST_EXIT_CODE%

REM ============================================================================
REM Functions
REM ============================================================================

:show_help
echo.
echo ================================================================================
echo KAFKA_CSA Test Runner Help
echo ================================================================================
echo.
echo This script runs the test suite for the KAFKA_CSA module.
echo.
echo USAGE:
echo   run_tests.bat [OPTIONS] [MODULE]
echo.
echo OPTIONS:
echo   help                Show this help message
echo   quick               Run quick tests only (basic + safe_functions)
echo   verbose             Run with verbose output
echo.
echo MODULES:
echo   basic               Run basic functionality tests
echo   safe_functions      Run safe functions tests  
echo   kpi_helper          Run KPI_Helper utility tests
echo   main                Run main module tests
echo   kpi_csa             Run KPI_CSA class tests
echo   integration         Run integration tests
echo.
echo EXAMPLES:
echo   run_tests.bat                    Run all tests
echo   run_tests.bat basic              Run basic tests only
echo   run_tests.bat quick              Run quick test subset
echo   run_tests.bat verbose            Run all tests with verbose output
echo   run_tests.bat basic verbose      Run basic tests with verbose output
echo.
echo EXIT CODES:
echo   0     All tests passed
echo   1     Some tests failed or errors occurred
echo   130   Test execution was interrupted
echo.
echo REQUIREMENTS:
echo   • Python 3.6 or higher
echo   • All test files in the tests/ directory
echo   • KAFKA_CSA module files in the parent directory
echo.
echo For more information, see the test documentation in the tests/ directory.
echo.
goto :eof

REM End of script
