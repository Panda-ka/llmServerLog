@echo off
setlocal

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Step 1: Check if Conda environment 'llmLogServer' exists
echo Checking if Conda environment 'llmLogServer' exists...
conda info --envs | findstr /C:"llmLogServer" >nul
if %errorlevel% equ 0 (
    echo Conda environment 'llmLogServer' already exists.
) else (
    echo Conda environment 'llmLogServer' not found. Creating...
    conda create -n llmLogServer python=3.11 -y
    if %errorlevel% neq 0 (
        echo Failed to create Conda environment. Exiting.
        exit /b 1
    )
)

:: Step 2: Try to activate the environment (with fallback)
echo Attempting to activate environment 'llmLogServer'...

:: First, try modern 'conda activate'
call activate llmLogServer
if %errorlevel% equ 0 (
    echo Successfully activated environment using 'conda activate'.
    set ACTIVATED=1
) else (
    echo 'conda activate' failed. Trying legacy 'activate'...
    call activate llmLogServer
    if %errorlevel% equ 0 (
        echo Successfully activated environment using 'activate'.
        set ACTIVATED=1
    ) else (
        echo ERROR: Failed to activate Conda environment by both 'conda activate' and 'activate'.
        echo Please run this script from Anaconda Prompt or ensure Conda is properly initialized.
        exit /b 1
    )
)

:: Step 3: Install dependencies
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install dependencies.
        exit /b 1
    )
    echo Dependencies installed successfully.
) else (
    echo Warning: requirements.txt not found in current directory.
)

echo Setup completed successfully!
pause