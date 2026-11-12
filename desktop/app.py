"""
SkyCast — Real-Time Weather Application (Desktop Tkinter Edition).
Launch script for the Tkinter desktop GUI.
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from desktop.ui.main_window import SkyCastApp

def main():
    try:
        app = SkyCastApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nSkyCast closed by user.")
    except Exception as e:
        print(f"Error launching SkyCast Desktop: {e}")

if __name__ == "__main__":
    main()
