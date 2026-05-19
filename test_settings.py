import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.settings_window import ModernSettingsWindow

if __name__ == "__main__":
    config = Config.load()
    window = ModernSettingsWindow(config)
    window.show()
