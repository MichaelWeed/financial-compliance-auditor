@echo off
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo --- 🚀 IGNITING SOVEREIGN AUDITOR [Windows] ---

:: Check for conda
where conda >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Conda not found in PATH.
    pause
    exit /b
)

set CONDA_ENV=compliance-auditor
set MODEL=mlx-community/Qwen2.5-72B-Instruct-4bit
set PORT=8080

:: Check if port is open (requires powershell)
powershell -Command "if (Get-NetTCPConnection -LocalPort %PORT% -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"
if %ERRORLEVEL% equ 1 (
    echo 💡 REASONING NODE is already online on port %PORT%.
) else (
    echo 🧠 STARTING INFERENCE NODE (%MODEL%)...
    start /b conda run -n %CONDA_ENV% python -m mlx_lm.server --model %MODEL% --port %PORT% > logs/server.log 2>&1
    echo    Waiting for node to initialize...
    timeout /t 10 /nobreak >nul
)

echo ⚖️  AWAKENING FORENSIC WORKBENCH...
conda run -n %CONDA_ENV% streamlit run app.py --server.port 8503
pause
