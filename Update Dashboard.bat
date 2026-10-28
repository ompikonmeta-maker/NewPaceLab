@echo off
rem Klik dua kali: tarik data Garmin, buat dashboard, lalu buka di browser.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
echo Mengambil data Garmin...
echo.
%PY% pacelab.py
set ERR=%ERRORLEVEL%
if exist "dist\dashboard.html" start "" "dist\dashboard.html"
echo.
if not "%ERR%"=="0" (
  echo Ada masalah, baca pesan di atas. Dashboard dibuka dengan data terakhir yang ada.
  pause
  exit /b %ERR%
)
echo Selesai. Jendela ini tertutup sendiri dalam 5 detik.
timeout /t 5 >nul
