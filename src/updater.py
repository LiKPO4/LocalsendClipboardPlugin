from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import tempfile
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from tkinter import scrolledtext
import tkinter as tk
from typing import Callable, Optional

from .assets import app_icon_ico_path, app_icon_png_path
from .config import APP_ID, APP_NAME, APP_VERSION

GITHUB_OWNER = "LiKPO4"
GITHUB_REPO = "LocalsendClipboardPlugin"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
INSTALLER_PREFIX = "LocalSendClipboardPlugin-Setup-"
REQUEST_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{GITHUB_REPO}/{APP_VERSION}",
}
DOWNLOAD_CHUNK_SIZE = 1024 * 128


class UpdateError(Exception):
    pass


@dataclass
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass
class ReleaseInfo:
    tag_name: str
    version: str
    body: str
    html_url: str
    assets: list[ReleaseAsset]


def fetch_latest_release(timeout: int = 15) -> ReleaseInfo:
    request = urllib.request.Request(LATEST_RELEASE_API, headers=REQUEST_HEADERS)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"GitHub 接口返回错误：HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise UpdateError("无法连接 GitHub，请检查网络后重试。") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError("GitHub 返回的数据无法解析。") from exc

    assets = [
        ReleaseAsset(
            name=asset.get("name", ""),
            download_url=asset.get("browser_download_url", ""),
            size=asset.get("size", 0),
        )
        for asset in payload.get("assets", [])
    ]

    tag_name = payload.get("tag_name", "")
    return ReleaseInfo(
        tag_name=tag_name,
        version=normalize_version(tag_name),
        body=payload.get("body", "").strip(),
        html_url=payload.get("html_url", ""),
        assets=assets,
    )


def normalize_version(version: str) -> str:
    return version.lstrip("vV").strip()


def version_key(version: str) -> tuple:
    parts = re.split(r"(\d+)", normalize_version(version))
    key = []
    for part in parts:
        if not part:
            continue
        key.append(int(part) if part.isdigit() else part.lower())
    return tuple(key)


def is_newer_version(latest_version: str, current_version: str) -> bool:
    return version_key(latest_version) > version_key(current_version)


def select_installer_asset(release: ReleaseInfo) -> Optional[ReleaseAsset]:
    for asset in release.assets:
        if asset.name.startswith(INSTALLER_PREFIX) and asset.name.endswith(".exe"):
            return asset
    return None


def download_release_asset(
    asset: ReleaseAsset,
    destination: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    timeout: int = 30,
) -> Path:
    request = urllib.request.Request(asset.download_url, headers=REQUEST_HEADERS)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, open(destination, "wb") as output:
            total_size = int(response.headers.get("Content-Length", "0") or "0")
            downloaded = 0

            while True:
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                output.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
    except urllib.error.URLError as exc:
        raise UpdateError("下载更新失败，请稍后重试。") from exc

    return destination


def launch_installer(installer_path: Path):
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    subprocess.Popen(
        [
            str(installer_path),
            "/SP-",
            "/VERYSILENT",
            "/NOCANCEL",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
            "/FORCECLOSEAPPLICATIONS",
        ],
        close_fds=True,
        creationflags=flags,
    )


def schedule_installer_after_exit(installer_path: Path, pid: int):
    launcher_path = Path(tempfile.gettempdir()) / f"{APP_ID}_update_launcher.cmd"
    launcher_script = f"""@echo off
setlocal
:waitloop
tasklist /FI "PID eq {pid}" | find "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto waitloop
)
start "" "{installer_path}" /SP- /VERYSILENT /NOCANCEL /NORESTART /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS
"""
    launcher_path.write_text(launcher_script, encoding="ascii")
    subprocess.Popen(
        ["cmd.exe", "/c", str(launcher_path)],
        close_fds=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0),
    )


class UpdateDialog:
    COLORS = {
        "bg": "#edf3ff",
        "panel": "#ffffff",
        "accent": "#1d4ed8",
        "accent_hover": "#1e40af",
        "text": "#0f172a",
        "muted": "#64748b",
        "border": "#cdd8eb",
        "success": "#047857",
    }

    def __init__(
        self,
        parent,
        current_version: str,
        release: ReleaseInfo,
        on_apply_update: Callable[[], None],
    ):
        self.parent = parent
        self.current_version = current_version
        self.release = release
        self.on_apply_update = on_apply_update
        self.window = tk.Toplevel(parent)
        self.window.title("发现新版本")
        self.window.geometry("720x560")
        self.window.resizable(False, False)
        self.window.configure(bg=self.COLORS["bg"])
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._close)

        self._icon_photo = None
        self._set_window_icon(self.window)
        self._status_var = tk.StringVar(value=f"当前版本 v{current_version}，检测到新版本 v{release.version}")
        self._busy = False

        self._create_widgets()

    def _set_window_icon(self, window):
        try:
            window.iconbitmap(str(app_icon_ico_path()))
        except Exception:
            pass

        try:
            self._icon_photo = tk.PhotoImage(file=str(app_icon_png_path()))
            window.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def _create_widgets(self):
        container = tk.Frame(self.window, bg=self.COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        header = tk.Frame(container, bg=self.COLORS["panel"], highlightbackground=self.COLORS["border"], highlightthickness=1)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text=f"发现新版本 v{self.release.version}",
            font=("Microsoft YaHei UI", 18, "bold"),
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
        )
        title.pack(anchor=tk.W, padx=18, pady=(16, 6))

        subtitle = tk.Label(
            header,
            text=f"当前版本 v{self.current_version}，可以一键下载并自动安装更新。",
            font=("Microsoft YaHei UI", 9),
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
        )
        subtitle.pack(anchor=tk.W, padx=18, pady=(0, 16))

        notes_card = tk.Frame(container, bg=self.COLORS["panel"], highlightbackground=self.COLORS["border"], highlightthickness=1)
        notes_card.pack(fill=tk.BOTH, expand=True, pady=(14, 0))

        notes_title = tk.Label(
            notes_card,
            text="Release 更新内容",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
        )
        notes_title.pack(anchor=tk.W, padx=16, pady=(14, 8))

        self.notes = scrolledtext.ScrolledText(
            notes_card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8fbff",
            fg=self.COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            padx=12,
            pady=12,
            height=18,
        )
        self.notes.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        body = self.release.body or "这个版本没有填写更新说明。"
        self.notes.insert("1.0", body)
        self.notes.configure(state=tk.DISABLED)

        footer = tk.Frame(container, bg=self.COLORS["bg"])
        footer.pack(fill=tk.X, pady=(14, 0))

        self.status = tk.Label(
            footer,
            textvariable=self._status_var,
            font=("Microsoft YaHei UI", 9),
            bg=self.COLORS["bg"],
            fg=self.COLORS["success"],
            anchor="w",
        )
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btns = tk.Frame(footer, bg=self.COLORS["bg"])
        btns.pack(side=tk.RIGHT)

        self.cancel_btn = tk.Button(
            btns,
            text="取消",
            command=self._close,
            font=("Microsoft YaHei UI", 10),
            bg="#ffffff",
            fg=self.COLORS["muted"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            bd=0,
            padx=18,
            pady=7,
            cursor="hand2",
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.update_btn = tk.Button(
            btns,
            text="一键更新",
            command=self._start_update,
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.COLORS["accent"],
            fg="white",
            activebackground=self.COLORS["accent_hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        self.update_btn.pack(side=tk.LEFT)

    def show(self):
        self.window.wait_window()

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.update_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)

    def _start_update(self):
        asset = select_installer_asset(self.release)
        if not asset:
            messagebox.showerror("更新失败", "没有找到可安装的更新包。", parent=self.window)
            return

        self._set_busy(True)
        self._status_var.set("正在下载更新包...")

        worker = threading.Thread(target=self._download_and_launch, args=(asset,), daemon=True)
        worker.start()

    def _download_and_launch(self, asset: ReleaseAsset):
        try:
            download_dir = Path(tempfile.gettempdir()) / "LocalSendClipboardPlugin"
            download_dir.mkdir(parents=True, exist_ok=True)
            installer_path = download_dir / asset.name

            def on_progress(downloaded: int, total: int):
                if total > 0:
                    percent = int(downloaded * 100 / total)
                    text = f"正在下载更新包... {percent}%"
                else:
                    text = f"正在下载更新包... {downloaded // 1024} KB"
                self.window.after(0, lambda: self._status_var.set(text))

            download_release_asset(asset, installer_path, progress_callback=on_progress)
            self.window.after(0, lambda: self._show_ready_dialog(installer_path))
        except UpdateError as exc:
            self.window.after(0, lambda: self._handle_update_error(str(exc)))
        except Exception as exc:
            self.window.after(0, lambda: self._handle_update_error(f"更新失败：{exc}"))

    def _show_ready_dialog(self, installer_path: Path):
        self._set_busy(False)
        self.window.withdraw()
        ready = UpdateReadyDialog(
            self.window,
            installer_path=installer_path,
            on_apply_update=self.on_apply_update,
        )
        ready.show()
        if self.window.winfo_exists():
            self.window.destroy()

    def _launch_update(self, installer_path: Path):
        try:
            self._status_var.set("更新包已下载，正在启动安装程序...")
            launch_installer(installer_path)
            self.window.after(250, self._finish_and_exit)
        except Exception as exc:
            self._handle_update_error(f"启动安装程序失败：{exc}")

    def _finish_and_exit(self):
        self.window.destroy()
        self.on_apply_update()

    def _handle_update_error(self, message: str):
        self._set_busy(False)
        self._status_var.set(message)
        messagebox.showerror("更新失败", message, parent=self.window)

    def _close(self):
        if self._busy:
            return
        self.window.destroy()


class InfoDialog:
    COLORS = {
        "bg": "#eef4ff",
        "panel": "#ffffff",
        "accent": "#1d4ed8",
        "text": "#0f172a",
        "muted": "#64748b",
        "border": "#cdd8eb",
    }

    def __init__(self, parent, title: str, message: str, button_text: str = "知道了"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("500x250")
        self.window.resizable(False, False)
        self.window.configure(bg=self.COLORS["bg"])
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._icon_photo = None
        self._set_window_icon()

        shell = tk.Frame(self.window, bg=self.COLORS["panel"], highlightbackground=self.COLORS["border"], highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        tk.Label(
            shell,
            text=title,
            font=("Microsoft YaHei UI", 17, "bold"),
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
        ).pack(anchor=tk.W, padx=20, pady=(20, 10))

        tk.Label(
            shell,
            text=message,
            font=("Microsoft YaHei UI", 10),
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            justify=tk.LEFT,
            wraplength=420,
        ).pack(anchor=tk.W, padx=20, pady=(0, 18))

        footer = tk.Frame(shell, bg=self.COLORS["panel"])
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 20))

        tk.Button(
            footer,
            text=button_text,
            command=self.close,
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.COLORS["accent"],
            fg="white",
            relief="flat",
            bd=0,
            padx=22,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

    def _set_window_icon(self):
        try:
            self.window.iconbitmap(str(app_icon_ico_path()))
        except Exception:
            pass
        try:
            self._icon_photo = tk.PhotoImage(file=str(app_icon_png_path()))
            self.window.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def show(self):
        self.window.wait_window()

    def close(self):
        self.window.destroy()


class UpdateReadyDialog(InfoDialog):
    def __init__(self, parent, installer_path: Path, on_apply_update: Callable[[], None]):
        self.installer_path = installer_path
        self.on_apply_update = on_apply_update
        super().__init__(
            parent,
            title="准备开始更新",
            message="更新包已经下载完成。\n\n软件当前正在运行，请点击下面的按钮关闭软件，关闭后会自动继续安装更新。",
            button_text="关闭软件并继续更新",
        )

    def close(self):
        try:
            schedule_installer_after_exit(self.installer_path, os.getpid())
        except Exception as exc:
            messagebox.showerror("更新失败", f"无法启动安装程序：{exc}", parent=self.window)
            return
        self.window.destroy()
        self.on_apply_update()


def show_update_flow(
    current_version: str = APP_VERSION,
    on_apply_update: Optional[Callable[[], None]] = None,
    parent=None,
):
    owner_root = None
    root = parent

    if root is None:
        owner_root = tk.Tk()
        owner_root.withdraw()
        root = owner_root

    try:
        latest = fetch_latest_release()
    except UpdateError as exc:
        messagebox.showerror("检查更新", str(exc), parent=root)
        if owner_root is not None:
            owner_root.destroy()
        return

    if not is_newer_version(latest.version, current_version):
        info = InfoDialog(
            root,
            title="检查完成",
            message=(
                f"当前已经是最新版本。\n\n"
                f"本地版本：v{current_version}\n"
                f"GitHub 最新版本：{latest.tag_name or f'v{latest.version}'}\n"
                f"系统环境：{platform.system()} {platform.release()}"
            ),
        )
        info.show()
        if owner_root is not None:
            owner_root.destroy()
        return

    dialog = UpdateDialog(root, current_version, latest, on_apply_update or (lambda: None))
    dialog.show()

    if owner_root is not None:
        owner_root.destroy()
