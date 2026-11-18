@echo off
echo ========================================
echo   Building consolor.exe
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

echo Building executable...
echo.

pyinstaller --onefile --add-data "src/themes;src/themes" --name consolor --console consolor.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo ========================================
echo.
echo Executable location: dist\consolor.exe
echo.
echo Testing executable...
echo.

dist\consolor.exe --help

echo.
echo ========================================
echo   Test: List themes
echo ========================================
echo.

dist\consolor.exe list

echo.
echo ========================================
echo   Build successful!
echo ========================================
echo.
echo You can now distribute: dist\consolor.exe
echo.

pause
