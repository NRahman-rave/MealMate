@echo off
cd /d "%~dp0"
echo Installing MealMate Python requirements...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Installation failed. Read the error above.
    pause
    exit /b
)
echo.
echo Requirements installed successfully.
pause
