@echo off
echo Installing required dependencies for v5.0...
cd ml_engine
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
echo Done!
pause
