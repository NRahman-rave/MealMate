@echo off
title MealMate Launcher
color 0A

cls

echo ==========================================
echo            MealMate Launcher
echo ==========================================
echo.

:: ------------------------------------------
:: Check MySQL port 3307
:: ------------------------------------------

echo Checking MySQL...

netstat -ano | findstr ":3307" | findstr "LISTENING" >nul

if errorlevel 1 (
    echo.
    echo ==========================================
    echo MySQL 8.4 is not running on port 3307.
    echo ==========================================
    echo.
    echo Please start MySQL84 and try again.
    echo.
    pause
    exit /b
)

echo MySQL is running on port 3307.
echo.

:: ------------------------------------------
:: Go to MealMate project
:: ------------------------------------------

cd /d "C:\Users\nrnay\Documents\MealMate\MealMate-Full-Website"

if errorlevel 1 (
    echo.
    echo ERROR: MealMate project folder was not found.
    echo.
    pause
    exit /b
)

if not exist "manage.py" (
    echo.
    echo ERROR: manage.py was not found.
    echo.
    pause
    exit /b
)

echo Project found.
echo.

:: ------------------------------------------
:: Database setup
:: ------------------------------------------

echo Checking database...
echo.

py manage.py setup_mealmate

if errorlevel 1 (
    echo.
    echo ==========================================
    echo Database setup failed.
    echo ==========================================
    echo.
    pause
    exit /b
)

echo Database OK.
echo.

:: ------------------------------------------
:: Django check
:: ------------------------------------------

echo Checking Django project...
echo.

py manage.py check

if errorlevel 1 (
    echo.
    echo ==========================================
    echo Django check failed.
    echo ==========================================
    echo.
    pause
    exit /b
)

echo Django project OK.
echo.

:: ------------------------------------------
:: Start Django server
:: ------------------------------------------

echo Starting MealMate...
echo.

start "MealMate Django Server" cmd /k "cd /d C:\Users\nrnay\Documents\MealMate\MealMate-Full-Website && py manage.py runserver 127.0.0.1:8000"

timeout /t 3 /nobreak >nul

:: ------------------------------------------
:: Open website
:: ------------------------------------------

start "" "http://127.0.0.1:8000/"

exit