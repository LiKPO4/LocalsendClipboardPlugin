import io
import time
from pathlib import Path

from PIL import Image


def is_image_file(file_path: Path, extensions: list) -> bool:
    ext = file_path.suffix.lower()
    if ext in extensions:
        return True
    
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def copy_image_to_clipboard(image_path: Path) -> bool:
    try:
        import win32clipboard

        with Image.open(image_path) as source_image:
            source_image.load()
            image = _prepare_clipboard_image(source_image)

        output = io.BytesIO()
        image.save(output, format='BMP')
        data = output.getvalue()[14:]  # 跳过BMP文件头

        return _write_dib_to_clipboard(data, win32clipboard)
    except Exception as e:
        print(f"复制图片到剪贴板失败: {e}")
        return False


def _prepare_clipboard_image(image: Image.Image) -> Image.Image:
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        prepared = image.convert('RGBA') if image.mode == 'P' else image.copy()
        alpha_mask = prepared.getchannel('A') if 'A' in prepared.getbands() else None
        background.paste(prepared, mask=alpha_mask)
        return background

    if image.mode != 'RGB':
        return image.convert('RGB')

    return image.copy()


def _write_dib_to_clipboard(data: bytes, win32clipboard, max_attempts: int = 8, delay: float = 0.1) -> bool:
    last_error = None

    for attempt in range(1, max_attempts + 1):
        clipboard_opened = False
        try:
            win32clipboard.OpenClipboard()
            clipboard_opened = True
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            return True
        except Exception as exc:
            last_error = exc
            print(f"[WARN] 第 {attempt}/{max_attempts} 次写入剪贴板失败: {exc}")
            time.sleep(delay)
        finally:
            if clipboard_opened:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

    print(f"[ERROR] 多次尝试后仍无法写入剪贴板: {last_error}")
    return False
