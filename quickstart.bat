@echo off
REM Quick start script for Windows

echo ========================================
echo Elios AI Interview Service - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment already exists
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
echo This may take a few minutes on first run...
python -m pip install --upgrade pip >nul 2>&1
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv

echo [4/4] Starting server...
echo.
echo ========================================
echo Server starting on http://localhost:8000
echo ========================================
echo.
echo Visit:
echo   - http://localhost:8000 (Welcome page)
echo   - http://localhost:8000/health (Health check)
echo   - http://localhost:8000/docs (API docs)
echo.
echo Press CTRL+C to stop the server
echo.

python src/main.py
