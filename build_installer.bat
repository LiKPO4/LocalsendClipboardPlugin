@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set "ISCC_PATH=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not exist "%ISCC_PATH%" (
    echo Inno Setup compiler not found. Please install Inno Setup first.
    exit /b 1
)

if not exist "dist\LocalSendClipboardPlugin.exe" (
    echo dist\LocalSendClipboardPlugin.exe not found. Run build.bat first.
    exit /b 1
)

for /f "usebackq delims=" %%V in (`venv\Scripts\python.exe -c "from src.config import APP_VERSION; print(APP_VERSION)"`) do set APP_VERSION=%%V

echo Building installer version %APP_VERSION%
"%ISCC_PATH%" /DAppVersion=%APP_VERSION% installer.iss
