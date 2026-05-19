@echo off
chcp 65001 >nul
echo ========================================
echo  安装依赖包
echo ========================================
echo.

cd /d "%~dp0"

echo 正在创建虚拟环境...
python -m venv venv

echo.
echo 正在安装依赖包...
venv\Scripts\pip install -r requirements.txt

echo.
echo ========================================
echo  安装完成！
echo ========================================
echo.
echo 现在可以运行 start.bat 启动程序
echo.
pause
