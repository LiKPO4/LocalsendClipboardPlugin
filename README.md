# LocalSend 图片剪贴板插件

一个运行在 Windows 托盘区的小工具。

它会监听 LocalSend 接收目录中的新图片，并在文件落盘后自动复制到系统剪贴板，方便直接粘贴到聊天软件、文档或设计工具中。

## 功能

- 监听 LocalSend 接收目录
- 自动识别常见图片格式
- 新图片到达后自动复制到剪贴板
- 可选桌面通知
- 可选复制后删除原文件
- 支持开机自启动
- 支持打包为单文件 EXE
- 支持生成 Inno Setup 安装包

## 运行环境

- Windows 10 / 11
- Python 3.11

## 本地启动

```bat
start.bat
```

或直接运行：

```bat
venv\Scripts\python.exe main.py
```

## 安装依赖

```bat
安装依赖.bat
```

## 构建 EXE

```bat
build.bat
```

输出文件：

- `dist\LocalSendClipboardPlugin.exe`

## 构建安装包

先安装 Inno Setup 6，然后执行：

```bat
build_installer.bat
```

输出文件：

- `dist\LocalSendClipboardPlugin-Setup-<version>.exe`

## 主要目录

- `main.py`：程序入口
- `src\tray.py`：托盘主程序和单实例控制
- `src\watcher.py`：目录监听和图片处理触发
- `src\clipboard_utils.py`：剪贴板写入
- `src\settings_window.py`：设置窗口
- `src\config.py`：配置读写和开机启动
- `installer.iss`：Inno Setup 安装脚本

## 当前版本

`1.3.0`

## 版本说明

`1.3.0`：

- 去掉了额外通知依赖，改为直接使用 `pystray` 的 Windows 通知能力
- 优化了打包依赖，减小了 EXE 体积
- 为剪贴板写入增加了重试和更稳妥的资源释放
- 新增 Inno Setup 安装包构建流程
