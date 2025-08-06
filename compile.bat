@echo off
echo ===================================
echo  RentalServerChecker - コンパイル開始
echo ===================================

pyinstaller --name "RentalServerChecker" --onefile --windowed --add-data "web;web" --add-data ".venv\lib\site-packages\whois\data;whois/data" --hidden-import=whois._1_query --hidden-import=aiodns --hidden-import=pycares main.py dkim_checker.py

echo.
echo ===================================
echo  コンパイル完了
echo ===================================
echo.
pause