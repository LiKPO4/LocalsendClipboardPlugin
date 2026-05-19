import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

APP_NAME = "LocalSend图片剪贴板插件"
APP_VERSION = "1.4.4"
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

        # Always trust the real registry status over the cached config flag.
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

    def set_auto_start(self, enable: bool):
        """设置开机启动"""
        if os.name != 'nt':
            return False

        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)

            if enable:
                command = self._get_auto_start_command()
                self._delete_auto_start_values(key)
                winreg.SetValueEx(key, AUTO_START_REGISTRY_NAME, 0, winreg.REG_SZ, command)
                print(f"[INFO] 已启用开机启动: {command}")
            else:
                self._delete_auto_start_values(key)
                print("[INFO] 已禁用开机启动")

            winreg.CloseKey(key)
            self.auto_start = enable
            self.save()
            return True
        except Exception as e:
            print(f"[ERROR] 设置开机启动失败: {e}")
            return False

    def is_auto_start_enabled(self) -> bool:
        """检查开机启动是否已启用"""
        return self._query_auto_start_value() is not None
