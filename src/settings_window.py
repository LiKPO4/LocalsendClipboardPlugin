import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
from typing import Callable, Optional

from .config import Config, APP_NAME, APP_VERSION


class ModernSettingsWindow:
    """更清晰的固定布局设置窗口"""

    COLORS = {
        'bg_primary': '#eef2f7',
        'bg_secondary': '#ffffff',
        'bg_muted': '#f8fafc',
        'bg_option': '#f3f6fb',
        'accent': '#2563eb',
        'accent_hover': '#1d4ed8',
        'accent_soft': '#dbeafe',
        'text_primary': '#0f172a',
        'text_secondary': '#475569',
        'text_hint': '#64748b',
        'border': '#d7dee8',
        'success': '#16a34a',
    }

    def __init__(self, config: Config, on_save: Optional[Callable] = None):
        self.config = config
        self.on_save = on_save
        self.root = None
        self._create_window()

    def _create_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME}")
        self.root.geometry("760x680")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS['bg_primary'])

        try:
            self.root.iconbitmap('icon.ico')
        except Exception:
            pass

        self._create_styles()
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center_window()

    def _center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = 760
        height = 720
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_styles(self):
        """初始化 ttk 样式"""
        style = ttk.Style()
        style.theme_use('clam')

    def _create_card(self, parent, title, description=None):
        """创建统一风格的卡片"""
        card = tk.Frame(
            parent,
            bg=self.COLORS['bg_secondary'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1,
            bd=0
        )

        header = tk.Frame(card, bg=self.COLORS['bg_secondary'])
        header.pack(fill=tk.X, padx=16, pady=(12, 8))

        title_label = tk.Label(
            header,
            text=title,
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_primary']
        )
        title_label.pack(anchor=tk.W, pady=(0, 2))

        if description:
            desc_label = tk.Label(
                header,
                text=description,
                font=('Microsoft YaHei UI', 9),
                bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['text_hint'],
                wraplength=660,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, pady=(2, 0))

        body = tk.Frame(card, bg=self.COLORS['bg_secondary'])
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        return card, body

    def _make_entry(self, parent, textvariable):
        """创建统一样式输入框"""
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=('Consolas', 11),
            bg=self.COLORS['bg_muted'],
            fg=self.COLORS['text_primary'],
            relief='flat',
            bd=10,
            highlightthickness=1,
            highlightcolor=self.COLORS['accent'],
            highlightbackground=self.COLORS['border'],
            insertbackground=self.COLORS['text_primary']
        )

    def _create_widgets(self):
        """创建所有 UI 组件"""
        main_container = tk.Frame(self.root, bg=self.COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        self._create_header(main_container)

        content_frame = tk.Frame(main_container, bg=self.COLORS['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        watch_card = self._create_watch_dir_card(content_frame)
        watch_card.pack(fill=tk.X, pady=(0, 10))

        ext_card = self._create_extensions_card(content_frame)
        ext_card.pack(fill=tk.X, pady=(0, 10))

        options_card = self._create_options_card(content_frame)
        options_card.pack(fill=tk.X, pady=(0, 10))

        self._create_footer(main_container)

    def _create_header(self, parent):
        """创建标题区域"""
        header = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        header.pack(fill=tk.X)

        title_row = tk.Frame(header, bg=self.COLORS['bg_primary'])
        title_row.pack(fill=tk.X)

        title = tk.Label(
            title_row,
            text=APP_NAME,
            font=('Microsoft YaHei UI', 22, 'bold'),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_primary']
        )
        title.pack(side=tk.LEFT)

        badge = tk.Label(
            title_row,
            text=f"v{APP_VERSION}",
            font=('Microsoft YaHei UI', 9, 'bold'),
            bg=self.COLORS['accent_soft'],
            fg=self.COLORS['accent'],
            padx=10,
            pady=4
        )
        badge.pack(side=tk.RIGHT, pady=(4, 0))

        subtitle = tk.Label(
            header,
            text="调整监听目录、图片格式和自动处理行为。默认窗口已固定为完整显示所有设置项。",
            font=('Microsoft YaHei UI', 9),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_secondary'],
            justify=tk.LEFT
        )
        subtitle.pack(anchor=tk.W, pady=(8, 0))

    def _create_watch_dir_card(self, parent):
        """创建监听目录卡片"""
        card, body = self._create_card(
            parent,
            "监听目录",
            "设置 LocalSend 接收图片的文件夹，建议指向接收目录。"
        )
        row = tk.Frame(body, bg=self.COLORS['bg_secondary'])
        row.pack(fill=tk.X)

        self.watch_dir_var = tk.StringVar(value=self.config.watch_dir)
        self.dir_entry = self._make_entry(row, self.watch_dir_var)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        browse_btn = tk.Button(
            row,
            text="选择文件夹",
            command=self._browse_dir,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg=self.COLORS['accent_soft'],
            fg=self.COLORS['accent'],
            activebackground='#c7ddff',
            activeforeground=self.COLORS['accent'],
            relief='flat',
            bd=0,
            padx=14,
            pady=6,
            cursor='hand2'
        )
        browse_btn.pack(side=tk.RIGHT)
        return card

    def _create_extensions_card(self, parent):
        """创建图片格式卡片"""
        card, body = self._create_card(
            parent,
            "图片格式",
            "填写需要自动复制的图片扩展名，多个格式请用英文逗号分隔，例如：.jpg, .png, .webp"
        )

        if self.config.image_extensions:
            extensions_str = ", ".join(self.config.image_extensions)
        else:
            extensions_str = ".jpg, .jpeg, .png, .gif, .bmp, .webp, .ico, .tiff, .svg"

        self.extensions_var = tk.StringVar(value=extensions_str)
        self.ext_entry = self._make_entry(body, self.extensions_var)
        self.ext_entry.pack(fill=tk.X)
        return card

    def _create_options_card(self, parent):
        """创建功能选项卡片"""
        card, body = self._create_card(
            parent,
            "功能选项",
            "这些行为会在检测到新图片后自动生效。"
        )

        options = [
            ("delete_var", "复制后删除原文件", "图片复制到剪贴板后，自动删除源文件。"),
            ("notify_var", "显示桌面通知", "每次处理完成后显示一条系统通知。"),
            ("autostart_var", "开机自动启动", "Windows 登录后自动启动这个工具。"),
        ]

        self.option_vars = {}

        for index, (var_name, title, desc) in enumerate(options):
            if var_name == "delete_var":
                value = self.config.delete_after_copy
            elif var_name == "notify_var":
                value = self.config.show_notification
            else:
                value = self.config.auto_start

            var = tk.BooleanVar(value=value)
            self.option_vars[var_name] = var
            self._create_option_row(
                body,
                var=var,
                title=title,
                desc=desc,
                add_spacing=index < len(options) - 1
            )
        return card

    def _create_option_row(self, parent, var, title, desc, add_spacing=True):
        """创建紧凑的功能项行"""
        option_frame = tk.Frame(
            parent,
            bg=self.COLORS['bg_option'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1,
            bd=0
        )
        option_frame.pack(fill=tk.X, pady=(0, 6 if add_spacing else 0))

        checkbox = tk.Checkbutton(
            option_frame,
            variable=var,
            bg=self.COLORS['bg_option'],
            activebackground=self.COLORS['bg_option'],
            selectcolor=self.COLORS['bg_secondary'],
            fg=self.COLORS['accent'],
            activeforeground=self.COLORS['accent'],
            highlightthickness=0,
            bd=0,
            padx=4,
            pady=0
        )
        checkbox.pack(side=tk.LEFT, padx=(12, 8), pady=8)

        text_frame = tk.Frame(option_frame, bg=self.COLORS['bg_option'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12), pady=8)

        title_label = tk.Label(
            text_frame,
            text=title,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg=self.COLORS['bg_option'],
            fg=self.COLORS['text_primary']
        )
        title_label.pack(anchor=tk.W)

        desc_label = tk.Label(
            text_frame,
            text=desc,
            font=('Microsoft YaHei UI', 9),
            bg=self.COLORS['bg_option'],
            fg=self.COLORS['text_secondary'],
            wraplength=560,
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, pady=(2, 0))

    def _create_footer(self, parent):
        """创建底部区域"""
        footer = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        footer.pack(fill=tk.X, pady=(12, 0))

        divider = tk.Frame(footer, height=1, bg=self.COLORS['border'])
        divider.pack(fill=tk.X, pady=(0, 10))

        content = tk.Frame(footer, bg=self.COLORS['bg_primary'])
        content.pack(fill=tk.X)

        hint = tk.Label(
            content,
            text="保存后立即生效，监听目录会自动更新。",
            font=('Microsoft YaHei UI', 9),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_hint']
        )
        hint.pack(side=tk.LEFT)

        btn_container = tk.Frame(content, bg=self.COLORS['bg_primary'])
        btn_container.pack(side=tk.RIGHT)

        cancel_btn = tk.Button(
            btn_container,
            text="取消",
            command=self._on_close,
            font=('Microsoft YaHei UI', 10),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_secondary'],
            activebackground=self.COLORS['bg_muted'],
            activeforeground=self.COLORS['text_primary'],
            relief='flat',
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            bd=0,
            padx=18,
            pady=7,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        save_btn = tk.Button(
            btn_container,
            text="保存设置",
            command=self._save,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg=self.COLORS['accent'],
            fg='white',
            activebackground=self.COLORS['accent_hover'],
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT)

    def _browse_dir(self):
        """浏览目录"""
        current_dir = self.watch_dir_var.get()
        if not Path(current_dir).exists():
            current_dir = str(Path.home())

        selected = filedialog.askdirectory(initialdir=current_dir)
        if selected:
            self.watch_dir_var.set(selected)

    def _save(self):
        """保存设置"""
        self.config.watch_dir = self.watch_dir_var.get()

        extensions_str = self.extensions_var.get()
        self.config.image_extensions = [
            ext.strip().lower() if ext.strip().startswith('.') else f'.{ext.strip().lower()}'
            for ext in extensions_str.split(',')
            if ext.strip()
        ]

        self.config.delete_after_copy = self.option_vars['delete_var'].get()
        self.config.show_notification = self.option_vars['notify_var'].get()

        new_autostart = self.option_vars['autostart_var'].get()
        current_autostart = self.config.is_auto_start_enabled()
        if current_autostart != new_autostart:
            self.config.set_auto_start(new_autostart)
        else:
            self.config.auto_start = current_autostart

        self.config.save()

        if self.on_save:
            self.on_save(self.config)

        self._show_success_message()
        self._on_close()

    def _show_success_message(self):
        """显示保存成功提示"""
        success_popup = tk.Toplevel(self.root)
        success_popup.overrideredirect(True)
        success_popup.configure(bg=self.COLORS['success'])

        label = tk.Label(
            success_popup,
            text="设置已保存",
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg=self.COLORS['success'],
            fg='white',
            padx=28,
            pady=10
        )
        label.pack()

        success_popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (success_popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (success_popup.winfo_height() // 2)
        success_popup.geometry(f"+{x}+{y}")

        self.root.after(1500, success_popup.destroy)

    def _on_close(self):
        """关闭窗口"""
        self.root.destroy()

    def show(self):
        """显示窗口"""
        self.root.mainloop()


SettingsWindow = ModernSettingsWindow


if __name__ == "__main__":
    config = Config.load()
    window = ModernSettingsWindow(config)
    window.show()
