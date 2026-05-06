@echo off
setlocal enableextensions enabledelayedexpansion

echo Creating Python virtual environment...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create virtual environment.
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

echo Upgrading pip, wheel, and setuptools...
python -m pip install --upgrade pip wheel setuptools
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to upgrade packaging tools.
    exit /b 1
)

echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Dependency installation failed.
    echo Try running: python -m pip install streamlit
    exit /b 1
)

echo.
echo Setup complete.
echo To activate the environment later, run:
echo     .\.venv\Scripts\activate.bat

echo Then run the dashboard with:
echo     streamlit run app.py
endlocal
