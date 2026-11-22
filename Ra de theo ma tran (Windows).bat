@echo off
rem Mo ung dung "Ra de theo ma tran" tren Windows (cai dat lan dau: "Cai dat tren Windows.bat")
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
rem Lay cau moi tu GitHub neu an toan (chi tua nhanh, khong gop); loi thi bo qua
where git >nul 2>nul && if exist ".git" git pull --ff-only -q >nul 2>nul
py -3 scripts\ung_dung.py
if errorlevel 9009 python scripts\ung_dung.py
pause
