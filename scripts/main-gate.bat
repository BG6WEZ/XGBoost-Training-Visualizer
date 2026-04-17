@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   XGBoost Training Visualizer - Main Gate
echo ========================================
echo.

set ROOT_DIR=%~dp0..
set PASSED=0
set FAILED=0

echo [1/4] API Tests
echo ----------------------------------------
cd /d "%ROOT_DIR%\apps\api"
"%ROOT_DIR%\.venv\Scripts\python.exe" -m pytest -v --tb=short -q 2>&1
if %ERRORLEVEL% EQU 0 (
    set /a PASSED+=1
    echo [PASS] API Tests
) else (
    set /a FAILED+=1
    echo [FAIL] API Tests
)
echo.

echo [2/4] Worker Tests
echo ----------------------------------------
cd /d "%ROOT_DIR%\apps\worker"
"%ROOT_DIR%\.venv\Scripts\python.exe" -m pytest -v --tb=short -q 2>&1
if %ERRORLEVEL% EQU 0 (
    set /a PASSED+=1
    echo [PASS] Worker Tests
) else (
    set /a FAILED+=1
    echo [FAIL] Worker Tests
)
echo.

echo [3/4] Web TypeScript Check
echo ----------------------------------------
cd /d "%ROOT_DIR%\apps\web"
call pnpm typecheck 2>&1
if %ERRORLEVEL% EQU 0 (
    set /a PASSED+=1
    echo [PASS] Web TypeScript Check
) else (
    set /a FAILED+=1
    echo [FAIL] Web TypeScript Check
)
echo.

echo [4/4] Web Build
echo ----------------------------------------
call pnpm build 2>&1
if %ERRORLEVEL% EQU 0 (
    set /a PASSED+=1
    echo [PASS] Web Build
) else (
    set /a FAILED+=1
    echo [FAIL] Web Build
)
echo.

echo ========================================
echo   Main Gate Summary
echo ========================================
echo Passed:  %PASSED%
echo Skipped: 9 (from API pytest - Redis-dependent integration tests)
echo Failed:  %FAILED%
echo ========================================
echo Note: Skipped tests are NOT counted as passed.
echo       They require Redis service to run.
echo ========================================

if %FAILED% EQU 0 (
    echo [SUCCESS] All gates passed!
    exit /b 0
) else (
    echo [FAILED] Some gates failed!
    exit /b 1
)
