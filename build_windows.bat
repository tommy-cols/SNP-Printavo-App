@echo off
REM Build script for Printavo Quote Creator (Windows)

echo ==========================================
echo Printavo Quote Creator - Windows Build
echo ==========================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Build with PyInstaller using Windows spec file
echo.
echo Building Windows application...
pyinstaller printavo_quote_creator_windows.spec

REM Check if build was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo Build completed successfully!
    echo ==========================================
    echo.
    echo Executable created at: dist\PrintavoQuoteCreator.exe
    echo.
    echo To distribute:
    echo 1. Zip the dist\PrintavoQuoteCreator.exe file
    echo 2. Share with Windows users
    echo 3. Users run PrintavoQuoteCreator.exe
    echo 4. Click Settings button to enter credentials (one-time setup)
) else (
    echo.
    echo Build failed. Check errors above.
    exit /b 1
)

pause