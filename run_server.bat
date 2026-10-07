@echo off
setlocal
cd /d "%~dp0"

set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

echo ===================================================
echo   Fusion 360 MCP Server Launcher
echo ===================================================

python -c "import mcp, pydantic" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Dependencies not found. Installing package and dependencies...
    pip install -e .
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies. Please run 'pip install -e .' manually.
        pause
        exit /b 1
    )
)

echo Starting fusion360-mcp server...
python -m fusion360_mcp.server
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server exited with error code %ERRORLEVEL%.
)
pause

