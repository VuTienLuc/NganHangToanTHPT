@echo off
rem ======================================================================
rem  DONG BO NGAN HANG GIUA CAC MAY (Windows)
rem  Luu cau moi tren may nay len GitHub va tai cau moi tu may khac ve.
rem  Khong dua file bi mat (ai_khoa.json, thi-truc-tuyen\bi_mat.json...) len GitHub.
rem ======================================================================
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Dong bo ngan hang
where git >nul 2>nul || (echo  [!] May chua co Git - chay "Cai dat tren Windows.bat" truoc. & goto :het)

echo  - Luu thay doi tren may nay...
git add -- cau-hoi cau-hoi-ts10 du-lieu ai-nhap ma-tran notebooklm prompt-ai tai-lieu 2>nul
git diff --cached --quiet
if errorlevel 1 (
  git commit -q -m "Cap nhat tu may Windows %COMPUTERNAME%"
  echo    da ghi nhan thay doi
) else (
  echo    khong co thay doi moi
)

echo  - Tai thay doi tu may khac ve...
git pull --no-rebase --no-edit
if errorlevel 1 (
  git merge --abort >nul 2>nul
  echo.
  echo  [!] Hai may cung sua mot cau/mot file nen Git chua tu gop duoc.
  echo      Em da huy lan gop nay, ngan hang tren may van nguyen ven.
  echo      Thay nho tro ly AI ^(Claude^) xu ly giup, hoac dong bo lai tu may Mac truoc.
  goto :het
)

echo  - Day len GitHub...
git push
if errorlevel 1 (
  echo  [!] Chua day len duoc ^(mang / dang nhap GitHub^). Thay chay lai file nay sau.
  goto :het
)
echo.
echo  XONG - ngan hang tren may nay va GitHub da giong nhau.
:het
echo.
pause
