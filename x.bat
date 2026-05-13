@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="-hidden" goto :payload
powershell -Command "Start-Process -FilePath '%~f0' -ArgumentList '-hidden' -WindowStyle Hidden"
exit /b

:payload
call venv\Scripts\activate
start "" pythonw main.pyw
exit