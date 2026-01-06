@echo off
echo ========================================
echo   AI Stock Analyst - API Server
echo ========================================
echo.

cd /d "%~dp0.."
call ..\..\.venv\Scripts\activate.bat

echo Starting OpenAI-compatible API server on port 8080...
echo.
echo Chat-UI should connect to: http://localhost:8080/v1
echo.

python api/openai_server.py
pause
