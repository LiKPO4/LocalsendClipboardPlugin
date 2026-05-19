@echo off
chcp 65001 >nul
echo ========================================
echo  LocalSend图片剪贴板插件
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境启动...
    venv\Scripts\python.exe main.py
) else (
    echo 使用系统Python启动...
    python main.py
)

echo.
echo 程序已退出，按任意键关闭...
pause >nul
