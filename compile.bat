@echo off
set APP_NAME=RentalServerChecker

echo ===================================
echo  %APP_NAME% - Compiling Start
echo ===================================
pyinstaller --name "%APP_NAME%" --onefile --windowed --add-data "web;web" main.py
echo ===================================
echo  Compiling Completion
echo ===================================
pause