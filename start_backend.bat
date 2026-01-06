@echo off
echo Starting Stock Analyst AI Backend...
cd /d "%~dp0backend"
call venv\Scripts\activate 2>nul || (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
)
python api/openai_server.py
