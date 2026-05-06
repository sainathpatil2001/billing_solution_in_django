@echo off
title Billing System Builder
cd /d "%~dp0"
cls
echo ========================================================
echo        Billing System Desktop App Builder
echo ========================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and add it to PATH.
    pause
    exit /b
)

REM Check if Node is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b
)

echo Installing Node dependencies...
call npm install
if %errorlevel% neq 0 (
    echo Error installing dependencies.
    pause
    exit /b
)

echo.
echo Starting Complete Build Process (Backend + Frontend)...
echo.

REM Run the master build script
python build_installer.py

if %errorlevel% neq 0 (
    echo.
    echo Build failed! 
    echo Check the output above for errors.
    pause
    exit /b
)

echo.
echo Build Successful!
echo Check the 'dist' folder for the installer.
pause
