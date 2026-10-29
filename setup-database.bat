@echo off
cd /d "%~dp0"
py manage.py migrate
py manage.py setup_mealmate
pause
