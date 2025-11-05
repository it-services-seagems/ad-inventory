@echo off
setlocal enabledelayedexpansion

REM === Cleanup ===
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :42059 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :42058 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

timeout /t 3 /nobreak >nul

REM === Iniciar Backend e Frontend a partir do diretório do script ===
REM Resolve o diretório onde este script está localizado e trabalha a partir dele
pushd "%~dp0.." >nul

REM Ativa o virtualenv relativo em backend\api se existir
if exist "backend\api\Scripts\activate.bat" (
    echo Activating virtualenv from backend\api
    call "backend\api\Scripts\activate.bat"
) else (
    echo Virtualenv not found at backend\api\Scripts\activate.bat - proceeding without activation
)

REM Iniciar frontend (executa em background)
if exist "frontend\package.json" (
    echo Starting frontend...
    start /B /D "%CD%\frontend" cmd /c npm start
) else (
    echo Frontend package.json not found; skipping frontend start
)

timeout /t 5 /nobreak >nul

REM Iniciar backend principal com python (após ativar o venv, 'python' deve apontar para o venv)
echo Starting backend...
if exist "backend\app.py" (
    python backend\app.py
) else (
    echo backend\app.py not found; try: uvicorn backend.fastapi_app.main:app --host 0.0.0.0 --port 42059 --reload
)

popd >nul