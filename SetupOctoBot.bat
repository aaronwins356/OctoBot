@echo off
setlocal enabledelayedexpansion

REM Determine the directory containing this script.
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=.\"

pushd "%SCRIPT_DIR%"

set "VENV_DIR=%SCRIPT_DIR%.venv"
set "ACTIVATE_BAT=%VENV_DIR%\Scripts\activate.bat"
set "SETUP_FLAG=%SCRIPT_DIR%.octobot_setup_complete"

if exist "%SETUP_FLAG%" (
    echo OctoBot environment already initialized. Skipping setup.
    if not exist "%ACTIVATE_BAT%" (
        echo The existing setup flag was found, but the virtual environment is missing.
        echo Delete %SETUP_FLAG% and rerun this script to reinitialize.
        popd
        endlocal
        exit /b 1
    )
    goto run_bot
)

echo === Initializing OctoBot environment (one-time setup) ===

if not exist "%VENV_DIR%" (
    echo Creating virtual environment in %VENV_DIR% ...
    py -3.11 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 py -3 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the virtual environment. Ensure Python 3.11 is installed and available in PATH.
        popd
        endlocal
        exit /b 1
    )
)

if not exist "%ACTIVATE_BAT%" (
    echo Virtual environment activation script not found at %ACTIVATE_BAT%.
    popd
    endlocal
    exit /b 1
)

call "%ACTIVATE_BAT%"
if errorlevel 1 (
    echo Unable to activate the virtual environment.
    popd
    endlocal
    exit /b 1
)

echo Upgrading pip, setuptools, and wheel ...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto fail

echo Installing OctoBot and dependencies ...
python -m pip install -e "."
if errorlevel 1 goto fail

echo One-time setup complete.
> "%SETUP_FLAG%" echo OctoBot environment initialized on %DATE% at %TIME%.

goto run_bot

:run_bot
call "%ACTIVATE_BAT%"
if errorlevel 1 (
    echo Unable to activate the virtual environment for running OctoBot.
    popd
    endlocal
    exit /b 1
)

if "%~1"=="" (
    echo Launching OctoBot status dashboard...
    python -m octobot.interface.cli status
) else (
    echo Launching OctoBot with arguments: %*
    python -m octobot.interface.cli %*
)

popd
endlocal
exit /b 0

:fail
echo.
echo Dependency installation failed. Review the messages above for details.
popd
endlocal
exit /b 1
