@echo off

REM Store the current working directory in a variable
set CURRENT_DIR=%cd%

echo Activating the virtual environment...

REM Check if the .venv directory exists, and create it if necessary
if not exist .venv (
    echo Virtual environment not found. Creating a new one...
) else (
    echo Virtual environment found. Activating it...
)

REM Determine if python3 is available, default to python if not
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=python3
) else (
    set PYTHON=python
)

REM Determine the appropriate pip version to use
%PYTHON% -m pip --version >nul 2>&1
if %errorlevel% == 0 (
    set PIP=pip
) else (
    set PIP=pip3
)

REM Create the virtual environment if it doesn't already exist
%PYTHON% -m venv .venv

REM Activate the virtual environment
call .venv\Scripts\activate

echo Virtual environment successfully activated.

REM Check if the requirements.txt file is present
if not exist requirements.txt (
    exit /b
) else (
    REM Prompt the user to install dependencies from requirements.txt
    set /p INSTALL_REQUIREMENTS=Do you want to install the requirements? [y/n]

    if /i "%INSTALL_REQUIREMENTS%"=="y" (
        echo Installing dependencies...
        %PIP% install -r requirements.txt
        echo Dependencies installed successfully.
    ) else (
        echo Skipping requirements installation.
    )
)
