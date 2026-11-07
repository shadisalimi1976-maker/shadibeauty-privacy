@echo off
cd /d "%~dp0"
echo Installing... this takes 5-10 minutes the first time.
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
echo.
echo DONE. Now run run.bat
pause
