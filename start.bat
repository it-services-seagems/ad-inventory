@echo off
setlocal enabledelayedexpansion

REM === Cleanup ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :42057 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :42056 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

timeout /t 3 /nobreak >nul

REM === Iniciar Backend ===
cd /d "C:\Automation\RPA Service Tag\ServiceTag\ad-machine-manager\backend"
call api\Scripts\activate.bat

REM === Iniciar Frontend (método alternativo) ===
echo Starting frontend...
start /B /D "C:\Automation\RPA Service Tag\ServiceTag\ad-machine-manager\frontend" cmd /c npm start

timeout /t 5 /nobreak >nul

REM === Backend principal ===
echo Starting backend...
python app.py