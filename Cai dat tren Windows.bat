@echo off
rem ======================================================================
rem  CAI DAT NGAN HANG CAU HOI TOAN (thay Vu Tien Luc) TREN MAY WINDOWS
rem  Nhap dup file nay. Chay lai bao nhieu lan cung duoc (lan sau chi cap nhat).
rem  Muon chep san khoa AI / bi mat thi truc tuyen: dat cac file vao thu muc
rem  "bi_mat" canh file nay:  bi_mat\ai_khoa.json, bi_mat\bi_mat.json, bi_mat\mat_khau_dau.json
rem ======================================================================
chcp 65001 >nul
setlocal EnableExtensions
set "URL=https://github.com/VuTienLuc/NganHangToanTHPT.git"
set "DICH=%USERPROFILE%\Documents\NganHangCaNhan"
set "NGUON=%~dp0"
set "VUA_CAI=0"
title Cai dat Ngan hang cau hoi Toan

echo.
echo  === BUOC 1/4: Kiem tra phan mem can thiet ===
where winget >nul 2>nul
if errorlevel 1 (
  echo  [!] May chua co "winget" ^(App Installer^). Mo Microsoft Store, tim "App Installer", bam Cai dat roi chay lai file nay.
  goto :het
)

where git >nul 2>nul
if errorlevel 1 (
  echo  - Dang cai Git...
  winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
  set "VUA_CAI=1"
) else (
  echo  - Git: da co
)

py -3 --version >nul 2>nul
if errorlevel 1 (
  echo  - Dang cai Python 3...
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  set "VUA_CAI=1"
) else (
  echo  - Python: da co
)

where pdflatex >nul 2>nul
if errorlevel 1 (
  echo  - Dang cai MiKTeX ^(de bien dich PDF, khoang 200 MB^)...
  winget install -e --id MiKTeX.MiKTeX --accept-source-agreements --accept-package-agreements
  set "VUA_CAI=1"
) else (
  echo  - LaTeX: da co
)

if "%VUA_CAI%"=="1" (
  echo.
  echo  ============================================================
  echo   DA CAI XONG PHAN MEM. Thay DONG cua so nay roi NHAP DUP LAI
  echo   file cai dat nay mot lan nua de tai ngan hang ve.
  echo  ============================================================
  goto :het
)

rem MiKTeX: tu tai goi LaTeX con thieu khi bien dich, khong hoi
where initexmf >nul 2>nul && initexmf --set-config-value=[MPM]AutoInstall=1 >nul 2>nul

echo.
echo  === BUOC 2/4: Tai ngan hang tu GitHub ===
git config --global user.name >nul 2>nul
if errorlevel 1 (
  set /p "TEN=  Nhap ten hien thi khi luu len GitHub (vd Vu Tien Luc): "
  call git config --global user.name "%%TEN%%"
)
git config --global user.email >nul 2>nul
if errorlevel 1 (
  set /p "MAIL=  Nhap email tai khoan GitHub: "
  call git config --global user.email "%%MAIL%%"
)
if exist "%DICH%\.git" (
  echo  - Da co ngan hang o %DICH% - dang cap nhat...
  git -C "%DICH%" pull --ff-only
) else (
  echo  - Dang tai ve %DICH%
  echo    ^(Lan dau, trinh duyet se mo trang dang nhap GitHub: thay dang nhap tai khoan VuTienLuc roi bam Authorize^)
  git clone -c core.autocrlf=false -c core.longpaths=true "%URL%" "%DICH%"
  if errorlevel 1 (
    echo  [!] Chua tai duoc. Kiem tra mang / dang nhap GitHub roi chay lai file nay.
    goto :het
  )
)
git -C "%DICH%" config core.autocrlf false
git -C "%DICH%" config core.longpaths true

echo.
echo  === BUOC 3/4: Chep file bi mat ^(neu co thu muc bi_mat canh file nay^) ===
if not exist "%DICH%\thi-truc-tuyen" mkdir "%DICH%\thi-truc-tuyen"
call :chep "ai_khoa.json" "%DICH%\ai_khoa.json"
call :chep "bi_mat.json" "%DICH%\thi-truc-tuyen\bi_mat.json"
call :chep "mat_khau_dau.json" "%DICH%\thi-truc-tuyen\mat_khau_dau.json"

echo.
echo  === BUOC 4/4: Tao loi tat tren Desktop ===
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); foreach($p in @(@('Ra de theo ma tran','Ra de theo ma tran (Windows).bat'),@('Dong bo ngan hang','Dong bo (Windows).bat'))){ $s=$w.CreateShortcut((Join-Path $d ($p[0]+'.lnk'))); $s.TargetPath=(Join-Path $env:DICH $p[1]); $s.WorkingDirectory=$env:DICH; $s.Save() }"
echo  - Desktop co 2 loi tat: "Ra de theo ma tran" va "Dong bo ngan hang"

echo.
echo  ============================================================
echo   XONG! Mo ung dung bang loi tat "Ra de theo ma tran" tren Desktop.
echo   Lan dau ung dung lap chi muc ~30.000 cau, mat khoang 1 phut.
echo  ============================================================
goto :het

:chep
if exist "%~2" (
  echo  - %~1: da co, giu nguyen
  goto :eof
)
if exist "%NGUON%bi_mat\%~1" (
  copy /Y "%NGUON%bi_mat\%~1" "%~2" >nul
  echo  - %~1: da chep
) else (
  echo  - %~1: khong co trong thu muc bi_mat ^(bo qua^)
)
goto :eof

:het
echo.
pause
