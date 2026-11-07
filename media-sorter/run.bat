@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set /p DRIVE=Drive letter of the hard disk (example: E): 
echo.
echo 1 = TEST: check 100 files, change nothing
echo 2 = REAL TEST: sort 100 files
echo 3 = SORT THE WHOLE DRIVE
echo 4 = REAL TEST with MOVE (if option 2 said the drive does not support links)
echo 5 = SORT THE WHOLE DRIVE with MOVE
echo 6 = UNDO the MOVE
set /p CH=Choose 1-6: 
if "%CH%"=="1" python shadi_sorter.py %DRIVE%:\ --limit 100 --dry-run
if "%CH%"=="2" python shadi_sorter.py %DRIVE%:\ --limit 100
if "%CH%"=="3" python shadi_sorter.py %DRIVE%:\
if "%CH%"=="4" python shadi_sorter.py %DRIVE%:\ --limit 100 --mode move
if "%CH%"=="5" python shadi_sorter.py %DRIVE%:\ --mode move
if "%CH%"=="6" python shadi_sorter.py %DRIVE%:\ --undo
pause
