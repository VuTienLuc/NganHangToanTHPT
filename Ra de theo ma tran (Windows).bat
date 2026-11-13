@echo off
rem Mo ung dung "Ra de theo ma tran" tren Windows (can cai Python 3 tu python.org)
cd /d "%~dp0"
python scripts\ung_dung.py
if errorlevel 1 py scripts\ung_dung.py
pause
