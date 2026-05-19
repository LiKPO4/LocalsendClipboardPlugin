@echo off
chcp 65001 >nul
echo ========================================
echo LocalSend 图片剪贴板插件 - 打包工具
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

echo 正在安装依赖...
pip install -r requirements.txt -q
pip install pyinstaller -q

echo.
echo 正在打包程序...
echo.

pyinstaller --noconfirm --clean LocalSendClipboardPlugin.spec
if errorlevel 1 goto end

if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" (
    echo.
    echo 正在生成安装包...
    call build_installer.bat
    goto summary
)

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    echo.
    echo 正在生成安装包...
    call build_installer.bat
) else (
    echo 未检测到 Inno Setup，跳过安装包生成。
)

:summary
echo.
echo ========================================
if exist "dist\LocalSendClipboardPlugin.exe" (
    echo 打包完成!
    echo 输出文件: dist\LocalSendClipboardPlugin.exe
    echo.
    for %%I in (dist\LocalSendClipboardPlugin.exe) do echo 文件大小: %%~zI 字节
) else (
    echo 打包失败，请检查错误信息
)
echo ========================================
echo.

:end
pause
