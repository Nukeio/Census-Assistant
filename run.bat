@echo off
echo ===================================================
echo Starting Census Assistant Application Server
echo Lakhipur Circle - By Shahin Sha A. - S. A. Ahmed
echo ===================================================

if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Running ingestion and server...
python -m backend.main
pause
