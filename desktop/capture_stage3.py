"""
Script to capture Stage 3 screenshots of SkyCast Tkinter Desktop GUI:
1. 1100x750 (Default layout)
2. 800x600 (Minimum size responsive layout)
"""

import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import ImageGrab
from desktop.ui.main_window import SkyCastMainWindow

def capture():
    os.makedirs(os.path.join(ROOT_DIR, "desktop", "assets"), exist_ok=True)
    
    app = SkyCastMainWindow()
    app.geometry("1100x750+50+50")
    app.update_idletasks()
    app.update()
    
    # Wait for panels to render
    time.sleep(0.8)
    app.update_idletasks()
    app.update()
    
    # Capture 1100x750
    path_1100 = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage3_1100x750.png")
    img_1100 = ImageGrab.grab(window=app.winfo_id())
    img_1100.save(path_1100)
    print(f"Saved 1100x750 screenshot to {path_1100} size: {img_1100.size}")
    
    # Resize to minimum size 800x600
    app.geometry("800x600+50+50")
    app.update_idletasks()
    app.update()
    
    # Allow debounce timer to fire and re-render
    time.sleep(0.8)
    app.update_idletasks()
    app.update()
    
    path_800 = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage3_800x600.png")
    img_800 = ImageGrab.grab(window=app.winfo_id())
    img_800.save(path_800)
    print(f"Saved 800x600 screenshot to {path_800} size: {img_800.size}")
    
    app.destroy()
    print("Capture completed successfully.")

if __name__ == "__main__":
    capture()
