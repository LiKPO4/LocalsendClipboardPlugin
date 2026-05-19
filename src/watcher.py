import os
import time
from pathlib import Path
from typing import Callable, Optional

from .config import Config
from .clipboard_utils import is_image_file, copy_image_to_clipboard
from .notifier import notifier


class ImageFileHandler:
    def __init__(self, config: Config, on_image_copied: Optional[Callable] = None):
        self.config = config
        self.on_image_copied = on_image_copied
        self._processed_files = set()
        self._max_processed = 1000

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if str(file_path) in self._processed_files:
            return

        # 等待文件写入完成（最多等待2秒，每100ms检查一次）
        max_attempts = 20
        last_size = -1
        stable_count = 0

        for _ in range(max_attempts):
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 2:  # 连续2次大小不变，认为写入完成
                        break
                else:
                    stable_count = 0
                    last_size = current_size
                time.sleep(0.1)
            except:
                time.sleep(0.1)

        if not file_path.exists():
            return

        if is_image_file(file_path, self.config.image_extensions):
            self._process_image(file_path)

    def _process_image(self, file_path: Path):
        try:
            print(f"[INFO] 处理图片: {file_path.name}")
            print(f"[INFO] 通知开关: {self.config.show_notification}")
            
            if copy_image_to_clipboard(file_path):
                file_path_str = str(file_path)
                self._processed_files.add(file_path_str)
                
                # 如果已处理文件数量超过限制，随机删除一部分以控制内存
                if len(self._processed_files) > self._max_processed:
                    excess = len(self._processed_files) - self._max_processed
                    to_remove = list(self._processed_files)[:excess]
                    for item in to_remove:
                        self._processed_files.remove(item)
                    print(f"[INFO] 清理了 {excess} 条已处理文件记录")
                
                print(f"[INFO] 图片已复制到剪贴板: {file_path.name}")

                if self.config.show_notification:
                    print(f"[INFO] 准备显示成功通知...")
                    notifier.notify_image_copied(file_path.name)
                else:
                    print(f"[INFO] 通知已关闭，跳过显示")

                if self.on_image_copied:
                    self.on_image_copied(file_path)

                if self.config.delete_after_copy:
                    try:
                        file_path.unlink()
                        print(f"[INFO] 已删除原文件: {file_path.name}")
                    except Exception as e:
                        print(f"[ERROR] 删除文件失败: {e}")
            else:
                print(f"[ERROR] 复制图片失败: {file_path.name}")
                if self.config.show_notification:
                    notifier.notify_error(f"复制图片失败: {file_path.name}")
        except Exception as e:
            print(f"[ERROR] 处理图片失败: {e}")


class FileWatcher:
    def __init__(self, config: Config, on_image_copied: Optional[Callable] = None):
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        self.config = config

        class Handler(FileSystemEventHandler):
            def __init__(handler_self, handler_config, handler_callback):
                super().__init__()
                handler_self.handler = ImageFileHandler(handler_config, handler_callback)

            def on_created(handler_self, event):
                handler_self.handler.on_created(event)

        self.observer = Observer()
        self.handler = Handler(config, on_image_copied)
        self._running = False

    def start(self):
        if self._running:
            return

        watch_dir = self.config.ensure_watch_dir()

        self.observer.schedule(
            self.handler,
            str(watch_dir),
            recursive=False
        )
        self.observer.start()
        self._running = True
        print(f"开始监听目录: {watch_dir}")

    def stop(self):
        if self._running:
            self.observer.stop()
            self.observer.join()
            self._running = False
            print("停止监听")

    def is_running(self) -> bool:
        return self._running

    def update_watch_dir(self, new_dir: str):
        was_running = self._running
        if was_running:
            self.stop()

        self.config.watch_dir = new_dir
        self.config.save()

        if was_running:
            self.start()
