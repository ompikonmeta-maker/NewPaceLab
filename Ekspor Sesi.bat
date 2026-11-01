@echo off
rem Klik dua kali: simpan lari satu hari (kedua pelari) ke ekspor\NewPaceLab_<tanggal>.zip untuk Claude chat.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
if exist "%~dp0python\python.exe" set PY="%~dp0python\python.exe"
set TGL=
set /p TGL=Tanggal lari (YYYY-MM-DD, kosong = hari ini):
set FIT=
set /p FIT=Sertakan file FIT asli dari jam? Berisi GPS. (Y/n):
set OPT=
if /i "%FIT%"=="n" set OPT=--tanpa-fit
echo.
%PY% pacelab.py ekspor %TGL% %OPT%
set ERR=%ERRORLEVEL%
if exist ekspor start "" ekspor
echo.
pause
exit /b %ERR%
