@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

where conda >nul 2>nul
if errorlevel 1 (
    echo Conda was not found on PATH.
    echo Open Anaconda Prompt, run "conda activate Pydisplay_env", then run "python -m pydisplay".
    pause
    exit /b 1
)

echo Starting Pydisplay from "%PROJECT_DIR%"
conda run -n Pydisplay_env python -m pydisplay %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Pydisplay exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
