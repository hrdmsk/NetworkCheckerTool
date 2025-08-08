@echo off
set APP_NAME=RentalServerChecker

set /p CURRENT_VERSION=<version.txt
echo ver: %CURRENT_VERSION%

for /f "tokens=1-3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set /a PATCH=%%c
)

set NEW_VERSION=%MAJOR%.%MINOR%.%PATCH%
echo new ver: %NEW_VERSION%
echo %NEW_VERSION% > version.txt

set EXE_NAME=%APP_NAME%_v%NEW_VERSION%

echo ===================================
echo  %EXE_NAME% - Compiling Start
echo ===================================

pyinstaller --name "%EXE_NAME%" --onefile --windowed --add-data "web;web" --icon=img/RentalServerChecker.ico main.py

echo ===================================
echo  Compiling Completion
echo ===================================
pause