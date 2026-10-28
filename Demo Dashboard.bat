@echo off
rem Dashboard dari data rekaan - tanpa key, tanpa internet.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
if exist "%~dp0python\python.exe" set PY="%~dp0python\python.exe"
%PY% pacelab.py demo
if errorlevel 1 ( pause & exit /b 1 )
start "" "dist\dashboard-demo.html"
timeout /t 3 >nul
