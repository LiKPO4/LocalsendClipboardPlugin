from __future__ import annotations

import threading
import time

from .config import APP_NAME


class Notifier:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()
        self._tray_icon = None
        print("[INFO] Notification backend - pystray")

    def _next_tag(self) -> str:
        with self._lock:
            self._count += 1
            return f"copied-{int(time.time() * 1000)}-{self._count}"

    def register_tray_icon(self, tray_icon):
        self._tray_icon = tray_icon

    def unregister_tray_icon(self, tray_icon):
        if self._tray_icon is tray_icon:
            self._tray_icon = None

    def show(self, title: str, message: str, duration: int = 3):
        tag = self._next_tag()
        print(f"[INFO] Notification #{self._count}: {message}")

        if self._tray_icon and getattr(self._tray_icon, "HAS_NOTIFICATION", False):
            try:
                self._tray_icon.notify(message, title)
                if duration > 0:
                    timer = threading.Timer(duration, self._remove_notification_safe)
                    timer.daemon = True
                    timer.start()
                print("[INFO] Notification sent with pystray")
                return
            except Exception as exc:
                print(f"[WARN] pystray notification failed: {exc}")

        print(f"[NOTIFY] {title}: {message}")

    def _remove_notification_safe(self):
        tray_icon = self._tray_icon
        if not tray_icon:
            return

        try:
            tray_icon.remove_notification()
        except Exception:
            pass

    def notify_image_copied(self, filename: str):
        self.show(APP_NAME, f"已复制: {filename}")

    def notify_error(self, message: str):
        self.show(APP_NAME, message)


notifier = Notifier()
