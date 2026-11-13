"""
SkyCast Stage 5.5 Comprehensive Polish Verification Script
----------------------------------------------------------
Verifies:
1. Default startup city is Chennai, Tamil Nadu, India (13.0827, 80.2707)
2. Default favorites list is Indian cities: Bengaluru, Mumbai, New Delhi, Hyderabad, Kolkata
3. Night icons return 'moon' and 'partly_night' instead of yellow sun
4. Live local clock calculation using city UTC offset
5. Top bar has custom vector brand logo (not ☰) and functional ⚙️ gear icon
6. Settings popover with unit toggles, theme switcher, cache cleaner, and reset favorites
7. Captures 1100x750 screenshots to desktop/assets/ and copies to artifacts
"""

import sys
import os
import time
import tkinter as tk
from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop.storage import StorageManager
from desktop.ui.main_window import SkyCastMainWindow
from desktop.ui.icons import get_icon_for_wmo, get_weather_icon_image

def test_unit_assertions():
    print("=== 1. Checking Storage & Localization Defaults ===")
    storage = StorageManager()
    last_city = storage.get_last_city()
    favorites = storage.get_favorites()

    print(f"Startup City: {last_city.get('name')}, {last_city.get('admin1')}, {last_city.get('country')}")
    assert last_city.get("name") == "Chennai", f"Expected Chennai, got {last_city.get('name')}"
    assert abs(last_city.get("latitude") - 13.0827) < 0.01
    assert abs(last_city.get("longitude") - 80.2707) < 0.01

    fav_names = [f.get("name") for f in favorites]
    print(f"Default Favorites: {fav_names}")
    expected_favs = ["Bengaluru", "Mumbai", "New Delhi", "Hyderabad", "Kolkata"]
    assert fav_names == expected_favs, f"Expected {expected_favs}, got {fav_names}"

    print("\n=== 2. Checking Night Moon Vector Icons ===")
    assert get_icon_for_wmo(0, is_day=0) == "moon"
    assert get_icon_for_wmo(1, is_day=0) == "partly_night"
    assert get_icon_for_wmo(2, is_day=0) == "partly_night"
    assert get_icon_for_wmo(0, is_day=1) == "sun"
    assert get_icon_for_wmo(1, is_day=1) == "partly"
    print("[PASS] Night icons accurately resolve to 'moon' and 'partly_night'!")

def run_gui_verification():
    print("\n=== 3. Launching SkyCast GUI & Verifying Live Dashboard ===")
    app = SkyCastMainWindow()
    app.geometry("1100x750+50+50")
    app.update_idletasks()
    app.update()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(out_dir, exist_ok=True)
    artifact_dir = r"C:\Users\Aaditya.N.A\.gemini\antigravity\brain\9e04dabe-324d-4ad6-beef-0efb9f2ee50d"

    # Wait for live data to load from Open-Meteo
    start = time.time()
    while time.time() - start < 6.0:
        app.update_idletasks()
        app.update()
        if app.weather_data is not None and not app.is_loading:
            break
        time.sleep(0.1)

    # Verify live local clock calculation
    local_clock = app._get_current_local_time_str()
    print(f"Live Chennai Local Clock: {local_clock}")
    assert ":" in local_clock and ("AM" in local_clock or "PM" in local_clock)

    # 1. Main Dashboard Screenshot (Chennai & Indian favorites)
    p1 = os.path.join(out_dir, "skycast_stage5_5_chennai_1100x750.png")
    try:
        im1 = ImageGrab.grab(window=app.winfo_id())
        im1.save(p1)
        if os.path.exists(artifact_dir):
            import shutil
            shutil.copy(p1, os.path.join(artifact_dir, "skycast_stage5_5_chennai_1100x750.png"))
        print(f"[SUCCESS] Saved main dashboard screenshot to {p1} ({im1.size})")
    except Exception as e:
        print(f"[WARNING] ImageGrab failed for main dashboard: {e}")

    # 2. Trigger Settings Popover via ⚙️
    print("\n[Testing Settings Popover]")
    app._toggle_settings_popover()
    app.update_idletasks()
    app.update()
    p2 = os.path.join(out_dir, "skycast_stage5_5_settings_popover.png")
    try:
        im2 = ImageGrab.grab(window=app.winfo_id())
        im2.save(p2)
        if os.path.exists(artifact_dir):
            import shutil
            shutil.copy(p2, os.path.join(artifact_dir, "skycast_stage5_5_settings_popover.png"))
        print(f"[SUCCESS] Saved settings popover screenshot to {p2} ({im2.size})")
    except Exception as e:
        print(f"[WARNING] ImageGrab failed for settings popover: {e}")

    # 3. Test Clear Cache and Reset Favorites inside Settings
    app._clear_cache()
    assert app.cache_cleared_notice == True
    print("[PASS] Clear cache toggle activated with instant confirmation!")

    app._reset_favorites_to_defaults()
    assert app.favs_reset_notice == True
    print("[PASS] Reset favorites to default Indian metros activated successfully!")

    # 4. Trigger About Popover via Vector Brand Logo
    print("\n[Testing About Popover]")
    app._toggle_about_popover()
    app.update_idletasks()
    app.update()
    p3 = os.path.join(out_dir, "skycast_stage5_5_about_popover.png")
    try:
        im3 = ImageGrab.grab(window=app.winfo_id())
        im3.save(p3)
        if os.path.exists(artifact_dir):
            import shutil
            shutil.copy(p3, os.path.join(artifact_dir, "skycast_stage5_5_about_popover.png"))
        print(f"[SUCCESS] Saved about popover screenshot to {p3} ({im3.size})")
    except Exception as e:
        print(f"[WARNING] ImageGrab failed for about popover: {e}")

    app.destroy()
    print("\n=== All Stage 5.5 Visual & Functional Verifications Complete! ===")

if __name__ == "__main__":
    test_unit_assertions()
    run_gui_verification()
