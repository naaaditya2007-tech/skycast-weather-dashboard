# ✦ SkyCast — Real-Time Weather Application

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14%2B%20App%20Router-black?logo=next.js&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Live%20Deployment-black?logo=vercel&logoColor=white)
![GUI](https://img.shields.io/badge/Desktop-Tkinter%20%2B%20Pillow-blue)
![API](https://img.shields.io/badge/API-Open--Meteo%20(Keyless)-007ACC)
![Architecture](https://img.shields.io/badge/Architecture-Multithreaded%20Glassmorphism-purple)
![License](https://img.shields.io/badge/License-MIT-green)

A premium, atmospheric dual-platform weather intelligence application featuring:
1. **Desktop Client**: Native Python standard library **Tkinter** and **Pillow** with custom canvas glassmorphism, 30 FPS particle engine, and threaded Open-Meteo REST API.
2. **Web Mirror**: Next-generation **Next.js 14 (App Router) + React + Tailwind CSS** live web application deployed to **Vercel** with real-time 60 FPS HTML5 canvas weather particles, CSS backdrop-filter blur, interactive SVG spline temperature charts, and Indian city localization.

🌐 **Live Vercel Web Deployment**: [https://web-mocha-ten-79.vercel.app](https://web-mocha-ten-79.vercel.app)

---

## 📸 Desktop Application Preview (Chennai, India — 1100×750)

![SkyCast Desktop Application](desktop/assets/skycast_stage5_5_chennai_1100x750.png)

---

## 🚀 Core Technical Highlights

- **Compulsory Tkinter GUI**: Built from scratch using standard Python `tkinter` and `Pillow`. Completely standalone with zero external GUI framework bloat (no PyQt, no Electron, no Kivy). Employs standard native `tk.Button`, `tk.Label`, `tk.Entry`, `tk.Frame`, and `tk.Toplevel` dialogs embedded via `canvas.create_window()`.
- **Zero API Keys Required**: Integrates directly with [Open-Meteo](https://open-meteo.com) for real-time weather, 16-day daily forecasts, 24-hour timelines, geocoding search, and European air quality metrics (AQI). No secrets or credentials needed.
- **Custom Canvas Glassmorphism**: Frosted glass panels generated with dynamic Pillow Gaussian blurs, soft white translucency tints, dark contrast backing, and thin borders. Cached by geometry to re-render only on window resizing.
- **30 FPS Non-Blocking Particle Animation Engine**: Smooth canvas particle rendering that runs strictly behind glass panels and above the atmospheric wallpaper:
  - 🌧️ **Rain with Splash Droplets**: Dynamic falling raindrops that create bouncing splash rings upon impact.
  - ⚡ **Thunderstorm with Branching Lightning**: Procedural branching bolts with momentary screen flashes.
  - ❄️ **Snow**: Swirling crystalline flakes with sinusoidal horizontal drift.
  - 🌫️ **Fog & Mist**: Soft horizontal haze bands drifting slowly across the viewport.
  - ✨ **Twinkling Starfield**: Pulsing night stars with realistic brightness oscillations.
  - ☁️ **Drifting Clouds**: Puffy cloud layers gliding across the horizon.
- **Thread-Safe Asynchronous Architecture**: All network requests run on daemon background worker threads and dispatch UI updates safely to the main Tkinter thread using `root.after()` and `queue.Queue`, completely eliminating GUI freeze.
- **Interactive Top-Bar Popover Menus**:
  - **`⛅ SkyCast` Brand Weather Logo**: Custom vector weather logo (golden sun behind cloud) that opens an **About SkyCast** modal with architecture specifications.
  - **`⚙` Settings Popover**: Frosted popover menu allowing instant toggling of **°C / °F**, one-click activation of all **F2 Weather Preview themes**, offline cache clearing, and restoring default Indian metro favourites.
- **Live Local Clock**: Automatically calculates the searched city's exact local time using Open-Meteo's `utc_offset_seconds` and updates live every 60 seconds.
- **24-Hour Temperature Trend Chart**: Smooth spline temperature curve drawn directly on canvas with padded min/max labels that never collide with the baseline time axis or clip the window edge.
- **Day / Night Vector Weather Icons**: Crisp vector icons rendered via Pillow. Automatically renders glowing crescent moons with twinkling stars (`moon`, `partly_night`) during night hours (<06:00 or >=18:00) instead of daytime suns.
- **10-Minute Auto-Refresh & Offline Fallback**: Keeps weather metrics fresh with auto-refresh timers, a manual `[🔄]` button, and automatic fallback to persistent JSON cache if connection drops (`⚠️ No connection — showing last saved data`).

---

## 📂 Project Organization

```text
RealTimeWeatherApp/
├── desktop/                    # Compulsory Python Tkinter Desktop Application
│   ├── app.py                  # Main entrypoint
│   ├── api_client.py           # Multithreaded Open-Meteo client (5s timeout)
│   ├── storage.py              # Local JSON persistence (units, favorites, cache)
│   ├── settings.json           # Active configuration & saved favorites
│   ├── assets/                 # Background wallpapers & verified screenshots
│   │   ├── backgrounds/        # Clear, cloudy, rain, snow, fog, thunderstorm wallpapers
│   │   └── skycast_stage5_5_chennai_1100x750.png
│   └── ui/
│       ├── main_window.py      # Tkinter master window, canvas layout & popovers
│       ├── panels.py           # Frosted glassmorphism PIL renderer & caching
│       ├── animations.py       # 30 FPS particle animation engine
│       ├── icons.py            # High-contrast Pillow vector icon generator
│       └── other_cities.py     # Favorites sidebar cards & management
├── shared/
│   ├── __init__.py
│   └── weather_codes.py        # WMO weather codes, theme palettes & AQI mapping
├── web/                        # Next.js 14 App Router Web Mirror (Vercel Live)
│   ├── app/                    # App router (layout, globals.css, page)
│   ├── components/             # React weather components & 60 FPS HTML5 Canvas engine
│   ├── lib/                    # Weather code mappings & default Indian favorites
│   ├── next.config.js          # Next.js configuration
│   └── tailwind.config.js      # Custom glassmorphic design system
├── requirements.txt            # Python dependencies (Pillow, requests)
├── package.json                # Web monorepo scripts
├── vercel.json                 # Vercel deployment specification
├── .gitignore                  # Git exclusions (__pycache__, .venv, .next, out)
└── README.md                   # Project documentation
```

---

## 🌐 Live Web Version (Next.js 14 on Vercel)

Experience SkyCast directly in any modern browser with hardware-accelerated 60 FPS canvas atmospheric particles and true CSS backdrop-blur:

- **Live URL**: [https://web-mocha-ten-79.vercel.app](https://web-mocha-ten-79.vercel.app)
- **Features**: Live Open-Meteo REST API, interactive 24h bezier spline chart, multi-day forecast tabs, instant geocoding autocomplete, and Indian favorites sidebar.

To run the web version locally:
```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

---

## 💻 Installation & Setup

### Prerequisites
- Python 3.10 or higher.
- `pip` package manager.

```bash
# 1. Clone the repository
git clone https://github.com/naaaditya2007-tech/skycast-weather-dashboard.git
cd skycast-weather-dashboard

# 2. Install dependencies (Pillow and requests only)
pip install -r requirements.txt

# 3. Launch the desktop application
python desktop/app.py
```

---

## ⌨️ Controls & Shortcuts

| Control / Key | Action |
|:---|:---|
| **`Enter`** | Submit city search query in the search bar. |
| **`Escape`** | Clear search field and dismiss autocomplete suggestions. |
| **`[F2]`** | Cycle through all 8 atmospheric weather preview themes. |
| **`⚙` (Gear Icon)** | Open frosted glass Settings popover (units, previews, cache). |
| **`⛅` (Brand Logo)** | Open About SkyCast technical architecture popover. |
| **`[°C]` / `[°F]`** | Quick toggle between Celsius and Fahrenheit. |
| **`[🔄]`** | Manual instant refresh of current city and favorite cities. |
| **`+ Add Fav`** | Pin the currently viewed city into the favorites sidebar. |
| **`✕` on Card** | Remove a city from saved favorites. |

---

## 🇮🇳 Localized Default Cities

When launched for the first time, SkyCast opens with:
- **Default Home City**: **Chennai, Tamil Nadu, India** (`13.0827° N, 80.2707° E`, `Asia/Kolkata` +05:30).
- **Default Saved Favourites**:
  1. **Bengaluru**, Karnataka
  2. **Mumbai**, Maharashtra
  3. **New Delhi**, Delhi
  4. **Hyderabad**, Telangana
  5. **Kolkata**, West Bengal

---

## 📜 Acknowledgments & License

- Weather forecasting, geocoding, and air quality data provided by [Open-Meteo](https://open-meteo.com/).
- Distributed under the **MIT License**.
