@echo off
REM HyperCLI - AI-Powered Terminal Code Assistant
REM ==============================================
REM Windows batch file to run HyperCLI
REM
REM Author: HyperCLI Development Team
REM Version: 1.0.0

title HyperCLI - AI Code Assistant

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              HyperCLI - AI Code Assistant                    ║
echo ║                                                              ║
echo ║         Starting application...                              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if Ollama is running (optional check)
echo [INFO] Checking Ollama connection...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5 -ErrorAction Stop; if ($response.StatusCode -eq 200) { Write-Host '[OK] Ollama server is running' -ForegroundColor Green } else { Write-Host '[WARNING] Ollama server returned unexpected status' -ForegroundColor Yellow } } catch { Write-Host '[WARNING] Cannot connect to Ollama server at http://localhost:11434' -ForegroundColor Yellow; Write-Host 'Make sure Ollama is running: ollama serve' -ForegroundColor Gray }"
echo.

REM Check if the model is available
echo [INFO] Checking for required model (deepseek-r1:8b)...
echo If the model is not installed, you may need to run: ollama pull deepseek-r1:8b
echo.

REM Change to script directory
cd /d "%~dp0"

REM Create projects directory if it doesn't exist
if not exist "projects" (
    mkdir projects
    echo [INFO] Created projects directory
)

REM Create database if it doesn't exist
if not exist "database.db" (
    echo [INFO] Database will be initialized on first run
)

echo ═══════════════════════════════════════════════════════════
echo.

REM Run the application
python main.py

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo [INFO] Application exited with code: %EXIT_CODE%
echo.

pause
