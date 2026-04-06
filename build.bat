@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   NETD Calculator  -  Build ^& Package
echo ============================================================
echo.

:: ── 1. Verify Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python and add it to PATH.
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   Python  : %%v

:: ── 2. Install / upgrade build dependencies ───────────────────────────────────
echo.
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 ( echo [ERROR] Failed to install requirements.txt & goto :fail )

pip install pyinstaller --quiet
if errorlevel 1 ( echo [ERROR] Failed to install PyInstaller. & goto :fail )
echo   Done.

:: ── 3. Build with PyInstaller ─────────────────────────────────────────────────
echo.
echo [2/3] Building executable with PyInstaller...

:: Clean previous build artefacts
if exist "dist"  rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "NETD Calculator" ^
    --icon "assets\logo.ico" ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 ( echo [ERROR] PyInstaller build failed. & goto :fail )
echo   Done.  Output: dist\NETD Calculator\

:: ── 4. Create installer with Inno Setup ──────────────────────────────────────
echo.
echo [3/3] Creating installer...

:: Locate Inno Setup compiler (ISCC.exe)
set "ISCC="
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    "C:\Program Files\Inno Setup 5\ISCC.exe"
) do (
    if not defined ISCC (
        if exist %%P set "ISCC=%%~P"
    )
)

if not defined ISCC (
    echo.
    echo [WARNING] Inno Setup not found on this machine.
    echo           Download it from:  https://jrsoftware.org/isinfo.php
    echo           After installing, re-run this script  -OR-  run manually:
    echo             "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo.
    echo   The built application is still available at: dist\NETD Calculator\
    goto :done_no_installer
)

if not exist "Output" mkdir "Output"
"%ISCC%" installer.iss
if errorlevel 1 ( echo [ERROR] Inno Setup compilation failed. & goto :fail )

echo.
echo ============================================================
echo   SUCCESS!
echo   Installer : Output\NETD_Calculator_Setup.exe
echo ============================================================
goto :end

:done_no_installer
echo ============================================================
echo   BUILD COMPLETE (no installer — Inno Setup not found)
echo   Executable : dist\NETD Calculator\NETD Calculator.exe
echo ============================================================
goto :end

:fail
echo.
echo [FAILED] See errors above.
pause
exit /b 1

:end
pause
exit /b 0
