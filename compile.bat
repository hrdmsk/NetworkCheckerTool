@echo off
set APP_NAME=RentalServerChecker

echo ===================================
echo  %APP_NAME% - Compiling Start
echo ===================================
pyinstaller --name "%APP_NAME%" --onefile --windowed --add-data "web;web" --icon=img/RentalServerChecker.ico main.py
echo ===================================
echo  Compiling Completion
echo ===================================
pause