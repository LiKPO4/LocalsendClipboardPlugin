import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

APP_NAME = "LocalSend图片剪贴板插件"
APP_VERSION = "1.4.13"
APP_ID = "LocalSendClipboardPlugin"

DEFAULT_CONFIG = {
    "watch_dir": str(Path.home() / "Downloads" / "LocalSend"),
    "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".tiff", ".svg"],
    "delete_after_copy": False,
    "show_notification": True,
    "auto_start": False,
    "check_interval": 1.0,
}

CONFIG_FILE_NAME = "config.json"
AUTO_START_REGISTRY_NAME = APP_ID
LEGACY_AUTO_START_REGISTRY_NAMES = [APP_NAME]
AUTO_START_SHORTCUT_NAME = f"{APP_NAME}.lnk"


def get_config_path() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', Path.home()))
    elif os.name == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path.home() / '.config'

    config_dir = base / "LocalSendClipboardPlugin"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / CONFIG_FILE_NAME


@dataclass
class Config:
    watch_dir: str = DEFAULT_CONFIG["watch_dir"]
    image_extensions: List[str] = None
    delete_after_copy: bool = DEFAULT_CONFIG["delete_after_copy"]
    show_notification: bool = DEFAULT_CONFIG["show_notification"]
    auto_start: bool = DEFAULT_CONFIG["auto_start"]
    check_interval: float = DEFAULT_CONFIG["check_interval"]

    def __post_init__(self):
        if self.image_extensions is None:
            self.image_extensions = DEFAULT_CONFIG["image_extensions"].copy()

    @classmethod
    def load(cls) -> 'Config':
        config_path = get_config_path()
        loaded = None
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    merged_data = {**DEFAULT_CONFIG, **data}
                    loaded = cls(**{k: v for k, v in merged_data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        if loaded is None:
            loaded = cls()

        loaded._migrate_auto_start_registry_to_shortcut()
        loaded.auto_start = loaded.is_auto_start_enabled()
        return loaded

    def save(self):
        config_path = get_config_path()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def ensure_watch_dir(self):
        watch_path = Path(self.watch_dir)
        if not watch_path.exists():
            watch_path.mkdir(parents=True, exist_ok=True)
        return watch_path

    def _get_auto_start_command(self) -> str:
        """构造稳定的开机自启动命令"""
        if getattr(sys, 'frozen', False):
            return f'"{Path(sys.executable).resolve()}"'

        project_root = Path(__file__).resolve().parent.parent
        main_script = project_root / "main.py"
        pythonw_path = Path(sys.executable).with_name("pythonw.exe")
        python_path = pythonw_path if pythonw_path.exists() else Path(sys.executable)
        return f'"{python_path.resolve()}" "{main_script}"'

    def _get_auto_start_target(self) -> tuple[str, str, str]:
        """返回快捷方式目标、参数和工作目录"""
        if getattr(sys, 'frozen', False):
            executable = Path(sys.executable).resolve()
            return str(executable), "", str(executable.parent)

        project_root = Path(__file__).resolve().parent.parent
        main_script = project_root / "main.py"
        pythonw_path = Path(sys.executable).with_name("pythonw.exe")
        python_path = pythonw_path if pythonw_path.exists() else Path(sys.executable)
        return str(python_path.resolve()), f'"{main_script}"', str(project_root)

    def _get_startup_shortcut_path(self) -> Path | None:
        if os.name != 'nt':
            return None

        startup_dir = os.environ.get("APPDATA")
        if not startup_dir:
            return None
        return Path(startup_dir) / r"Microsoft\Windows\Start Menu\Programs\Startup" / AUTO_START_SHORTCUT_NAME

    def _create_auto_start_shortcut(self) -> bool:
        shortcut_path = self._get_startup_shortcut_path()
        if shortcut_path is None:
            return False

        try:
            import pythoncom
            from win32com.client import Dispatch

            target, arguments, working_dir = self._get_auto_start_target()
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)

            pythoncom.CoInitialize()
            try:
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = target
                shortcut.Arguments = arguments
                shortcut.WorkingDirectory = working_dir
                shortcut.IconLocation = target
                shortcut.Description = APP_NAME
                shortcut.save()
                del shortcut
                del shell
            finally:
                pythoncom.CoUninitialize()

            print(f"[INFO] 已创建开机启动快捷方式: {shortcut_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 创建开机启动快捷方式失败: {e}")
            return False

    def _delete_auto_start_shortcut(self):
        shortcut_path = self._get_startup_shortcut_path()
        if shortcut_path and shortcut_path.exists():
            try:
                shortcut_path.unlink()
                print(f"[INFO] 已删除开机启动快捷方式: {shortcut_path}")
            except Exception as e:
                print(f"[ERROR] 删除开机启动快捷方式失败: {e}")

    def _is_auto_start_shortcut_enabled(self) -> bool:
        shortcut_path = self._get_startup_shortcut_path()
        return bool(shortcut_path and shortcut_path.exists())

    def _delete_auto_start_values(self, key):
        """删除当前和旧版自启动注册表项"""
        import winreg

        names = [AUTO_START_REGISTRY_NAME, *LEGACY_AUTO_START_REGISTRY_NAMES]
        for name in names:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass

    def _query_auto_start_value(self):
        """查询当前生效的自启动注册表项"""
        if os.name != 'nt':
            return None

        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                for name in [AUTO_START_REGISTRY_NAME, *LEGACY_AUTO_START_REGISTRY_NAMES]:
                    try:
                        value, _ = winreg.QueryValueEx(key, name)
                        return name, value
                    except FileNotFoundError:
                        continue
                return None
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"[ERROR] 查询开机启动状态失败: {e}")
            return None

    def _migrate_auto_start_registry_to_shortcut(self):
        """把旧版注册表启动项迁移为单一启动文件夹快捷方式，避免任务管理器显示两条。"""
        registry_value = self._query_auto_start_value()
        if registry_value is None:
            return

        key = None
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if not self._is_auto_start_shortcut_enabled():
                self._create_auto_start_shortcut()
            self._delete_auto_start_values(key)
            print("[INFO] 已清理旧版注册表开机启动项，保留启动文件夹快捷方式")
        except Exception as e:
            print(f"[ERROR] 迁移开机启动项失败: {e}")
        finally:
            if key is not None:
                try:
                    winreg.CloseKey(key)
                except Exception:
                    pass

    def set_auto_start(self, enable: bool):
        """设置开机启动"""
        if os.name != 'nt':
            return False

        key = None
        shortcut_ok = False
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)

            if enable:
                self._delete_auto_start_values(key)
                shortcut_ok = self._create_auto_start_shortcut()
                print("[INFO] 已启用开机启动")
            else:
                self._delete_auto_start_values(key)
                self._delete_auto_start_shortcut()
                print("[INFO] 已禁用开机启动")

            self.auto_start = self.is_auto_start_enabled()
            self.save()
            return self.auto_start == enable or (enable and shortcut_ok)
        except Exception as e:
            print(f"[ERROR] 设置开机启动失败: {e}")
            return False
        finally:
            if key is not None:
                try:
                    winreg.CloseKey(key)
                except Exception:
                    pass

    def is_auto_start_enabled(self) -> bool:
        """检查开机启动是否已启用"""
        return self._is_auto_start_shortcut_enabled()
