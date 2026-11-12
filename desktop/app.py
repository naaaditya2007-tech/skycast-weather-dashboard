"""
SkyCast — Real-Time Weather Application (Desktop Tkinter Edition)
-----------------------------------------------------------------
Main entry point for running the desktop GUI application.
Developed using Python standard library Tkinter and Pillow.
Complies with school project guidelines: no external GUI frameworks.
"""

import sys
import os

# Ensure the root directory is available on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from desktop.ui.main_window import SkyCastMainWindow

def main():
    try:
        app = SkyCastMainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nSkyCast closed by user.")
    except Exception as e:
        print(f"Error executing SkyCast Desktop: {e}")

if __name__ == "__main__":
    main()
