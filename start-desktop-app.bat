@echo off
title Billing System Launcher
cls
echo ========================================================
echo        Billing System Desktop App Launcher
echo ========================================================
echo.

REM Check if Node is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python.
    pause
    exit /b
)

echo Checking dependencies...
if not exist node_modules (
    echo First run detected. Installing dependencies...
    call npm install
)

echo.
echo Starting Application...
echo The Django server will be managed automatically by the app.
echo.

call npm start

if %errorlevel% neq 0 (
    echo.
    echo Application exited with error.
    pause
)
