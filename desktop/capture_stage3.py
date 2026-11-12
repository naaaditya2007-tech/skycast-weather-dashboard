"""
Script to capture Stage 3 screenshots of SkyCast Tkinter Desktop GUI:
1. Cloudy Sky Photo at 1100x750 & 800x600
2. Dark Rain/Night Photo at 1100x750 & 800x600
"""

import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import ImageGrab
from desktop.ui.main_window import SkyCastMainWindow
from desktop.ui.panels import clear_panel_cache

def capture_for_wallpaper(wallpaper_name: str, prefix: str):
    os.makedirs(os.path.join(ROOT_DIR, "desktop", "assets"), exist_ok=True)
    clear_panel_cache()
    
    app = SkyCastMainWindow()
    app.forced_wallpaper = wallpaper_name
    app.geometry("1100x750+50+50")
    app.update_idletasks()
    app.update()
    
    # Wait for panels to render
    time.sleep(0.9)
    app.update_idletasks()
    app.update()
    
    # 1. Capture 1100x750
    path_1100 = os.path.join(ROOT_DIR, "desktop", "assets", f"{prefix}_1100x750.png")
    img_1100 = ImageGrab.grab(window=app.winfo_id())
    img_1100.save(path_1100)
    print(f"Saved 1100x750 screenshot to {path_1100} size: {img_1100.size}")
    
    # 2. Resize to minimum size 800x600
    app.geometry("800x600+50+50")
    app.update_idletasks()
    app.update()
    
    time.sleep(0.9)
    app.update_idletasks()
    app.update()
    
    path_800 = os.path.join(ROOT_DIR, "desktop", "assets", f"{prefix}_800x600.png")
    img_800 = ImageGrab.grab(window=app.winfo_id())
    img_800.save(path_800)
    print(f"Saved 800x600 screenshot to {path_800} size: {img_800.size}")
    
    app.destroy()
    time.sleep(0.3)

def main():
    print("--- Capturing Cloudy Sky Photo ---")
    capture_for_wallpaper("partly_cloudy.jpg", "skycast_cloudy")
    
    # Also save as canonical skycast_stage3 for backwards compatibility
    import shutil
    shutil.copyfile(
        os.path.join(ROOT_DIR, "desktop", "assets", "skycast_cloudy_1100x750.png"),
        os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage3_1100x750.png")
    )
    shutil.copyfile(
        os.path.join(ROOT_DIR, "desktop", "assets", "skycast_cloudy_800x600.png"),
        os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage3_800x600.png")
    )

    print("--- Capturing Dark Rain/Night Photo ---")
    capture_for_wallpaper("rain_night.jpg", "skycast_dark")
    print("All captures completed successfully.")

if __name__ == "__main__":
    main()
