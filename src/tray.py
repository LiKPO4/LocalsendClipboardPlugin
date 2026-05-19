import sys
import time
import threading
import traceback
import ctypes
from pathlib import Path
from typing import Optional
from pystray._base import MenuItem as Item
from pystray._win32 import Icon as TrayIcon

from .assets import load_app_icon_image
from .config import Config, APP_NAME, APP_VERSION
from .watcher import FileWatcher
from .settings_window import SettingsWindow
from .notifier import notifier
from .updater import show_update_flow


class SingleInstance:
    """使用Windows Mutex实现单实例检测"""

    def __init__(self):
        self.mutex_name = f"LocalSendClipboardPlugin_SingleInstance_Mutex_v2"
        self.mutex_handle = None
        self.acquired = False

    def check(self) -> bool:
        """检查是否已有实例在运行，返回True表示可以启动"""
        try:
            kernel32 = ctypes.windll.kernel32

            self.mutex_handle = kernel32.CreateMutexW(
                None,
                False,
                self.mutex_name
            )

            ERROR_ALREADY_EXISTS = 183
            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                if self.mutex_handle:
                    kernel32.CloseHandle(self.mutex_handle)
                    self.mutex_handle = None
                return False

            self.acquired = True
            return True
        except Exception as e:
            print(f"[WARN] 单实例检测失败: {e}")
            return True

    def release(self):
        """释放互斥体"""
        try:
            if self.mutex_handle and self.acquired:
                ctypes.windll.kernel32.ReleaseMutex(self.mutex_handle)
            if self.mutex_handle:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
                self.acquired = False
        except:
            pass


_single_instance = None


def check_single_instance() -> bool:
    """检查是否已有实例在运行"""
    global _single_instance
    _single_instance = SingleInstance()

    if not _single_instance.check():
        ctypes.windll.user32.MessageBoxW(
            None,
            "程序已在运行中，拒绝重复启动！",
            "LocalSend图片剪贴板插件",
            0x10
        )
        return False

    return True


class TrayApp:
    def __init__(self):
        try:
            self.config = Config.load()
            self.watcher = FileWatcher(self.config, on_image_copied=self._on_image_copied)
            self.tray: Optional[TrayIcon] = None

            self._show_settings_event = threading.Event()
            self._show_update_event = threading.Event()
            self._running = True
            self._settings_thread: Optional[threading.Thread] = None

            self._create_tray()
        except Exception as e:
            print(f"[ERROR] 初始化失败: {e}")
            traceback.print_exc()
            raise

    def _create_tray(self):
        try:
            self.tray = TrayIcon(
                "localsend_clipboard",
                load_app_icon_image(),
                f"{APP_NAME} v{APP_VERSION}",
                self._build_menu("运行中")
            )
            notifier.register_tray_icon(self.tray)
        except Exception as e:
            print(f"[ERROR] 创建托盘图标失败: {e}")
            traceback.print_exc()
            raise

    def _build_menu(self, status: str):
        return (
            Item(f"状态: {status}", None, enabled=False),
            Item("打开设置", self._open_settings, default=True),
            Item("检查更新", self._request_update_check),
            Item("重启监听", self._restart_watcher),
            Item("退出", self._quit),
        )

    def _on_image_copied(self, file_path: Path):
        self._update_status(f"已复制: {file_path.name}")

    def _update_status(self, status: str):
        if self.tray:
            self.tray.menu = self._build_menu(status)

    def _open_settings(self):
        """从托盘菜单调用（pystray线程），设置事件触发设置窗口显示"""
        self._show_settings_event.set()

    def _request_update_check(self):
        self._show_update_event.set()

    def _show_settings_window(self):
        """在独立线程中创建Tkinter设置窗口"""
        try:
            def on_save(new_config: Config):
                self.config = new_config
                self.watcher.update_watch_dir(new_config.watch_dir)

            window = SettingsWindow(
                self.config,
                on_save=on_save,
                on_check_update=self._show_update_dialog,
            )
            window.show()
        except Exception as e:
            print(f"[ERROR] 显示设置窗口失败: {e}")
            traceback.print_exc()

    def _show_update_dialog(self, parent=None):
        try:
            show_update_flow(
                current_version=APP_VERSION,
                on_apply_update=self._quit,
                parent=parent,
            )
        except Exception as e:
            print(f"[ERROR] 显示更新窗口失败: {e}")
            traceback.print_exc()

    def _settings_thread_target(self):
        """后台线程持续监听设置窗口请求"""
        while self._running:
            try:
                if self._show_settings_event.is_set():
                    self._show_settings_event.clear()
                    self._show_settings_window()
                if self._show_update_event.is_set():
                    self._show_update_event.clear()
                    self._show_update_dialog()
                time.sleep(0.5)
            except Exception as e:
                print(f"[ERROR] 设置线程异常: {e}")
                traceback.print_exc()

    def _restart_watcher(self):
        try:
            self.watcher.stop()
            self.watcher.start()
            notifier.show(APP_NAME, "监听已重启")
        except Exception as e:
            print(f"[ERROR] 重启监听失败: {e}")
            traceback.print_exc()

    def _quit(self):
        self._running = False
        self.watcher.stop()
        if self.tray:
            notifier.unregister_tray_icon(self.tray)
        if self.tray:
            self.tray.stop()

    def run(self):
        try:
            self.watcher.start()

            self._settings_thread = threading.Thread(target=self._settings_thread_target, daemon=True)
            self._settings_thread.start()

            self.tray.run()
        except Exception as e:
            print(f"[ERROR] 运行失败: {e}")
            traceback.print_exc()
            raise


def main():
    try:
        if not check_single_instance():
            sys.exit(1)

        app = TrayApp()
        app.run()
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")
        traceback.print_exc()
    finally:
        if _single_instance:
            _single_instance.release()


if __name__ == "__main__":
    main()
