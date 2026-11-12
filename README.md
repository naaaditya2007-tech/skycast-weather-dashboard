# ✦ SkyCast — Real-Time Weather Application & Dashboard

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/Desktop-Tkinter%20%2B%20Pillow-blue)
![Web](https://img.shields.io/badge/Web-Modern%20ES6%2B%20%2B%20CSS-F7DF1E?logo=javascript&logoColor=black)
![API](https://img.shields.io/badge/API-Open--Meteo-007ACC)
![Deployment](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

SkyCast is a real-time weather intelligence application built in two distinct versions that share the same visual design language and live data engine:
1. **Desktop Application**: Written in Python using standard **Tkinter** and **Pillow**, featuring Canvas glassmorphism panels, an asynchronous threaded network engine, and a 24-hour temperature trend line chart.
2. **Web Application**: A modern, mobile-first responsive dashboard with direct browser-to-API communication, automatic geolocation with privacy safeguards, and Canvas particle animations.

---

## 🚀 Hard Requirements Compliance

- **Compulsory Tkinter GUI**: The desktop application is strictly developed in Python with Tkinter and Pillow. It runs completely standalone with zero external GUI framework dependencies.
- **Allowed Libraries**: `tkinter`, `Pillow`, `requests` only.
- **Zero API Keys**: Both versions use **Open-Meteo** (Forecast API, Geocoding API, and Air Quality API). No private tokens or secrets are needed or embedded anywhere in the code.
- **Privacy Standard**: Geolocation is accessed strictly via a single-shot `navigator.geolocation.getCurrentPosition()`. Continuous background tracking (`watchPosition`) is never used, raw coordinates are never exposed in the UI, and permission denial is permanently respected.

---

## 🌟 Key Features

### 1. City Search with Autocomplete
- 300ms debounced asynchronous search querying the Open-Meteo Geocoding API.
- Autocomplete dropdown displaying matching cities, regions, and countries.
- Keyboard navigation: `Enter` to search, `Escape` to clear.

### 2. Current Conditions & Environmental Metrics
- Large temperature readout with feels-like temperature.
- Human-readable condition description and emoji icons.
- **Extra Detail Tiles**:
  - ☀️ **UV Index**: WHO categories (Low, Moderate, High, Very High, Extreme) with color labels.
  - 🍃 **Air Quality**: European Air Quality Index (AQI) with color-coded classification.
  - 💧 **Humidity**: Relative humidity percentage.
  - 💨 **Wind**: Wind speed & direction compass heading.
  - ⏲ **Pressure**: Barometric pressure with hPa and inHg conversions.
  - 👁️ **Visibility**: Distance in kilometers or miles.
  - ☁️ **Cloud Cover**: Percentage cloud coverage.
  - 🌡️ **Dew Point**: Temperature at which moisture condenses.
  - 🌅 **Sunrise & Sunset**: Local daylight hours.

### 3. Forecasts & Trend Chart
- **Hourly Forecast**: Timeline of the next 24 hours including hourly chance of precipitation (💧 %).
- **7-Day Outlook**: Daily weather icons, condition labels, precipitation probability, and high/low temperature bars.
- **24-Hour Temperature Trend Chart (Desktop)**: A custom line chart drawn directly on the Tkinter Canvas.

### 4. Unit Toggles & Persistence
- **Temperature**: Celsius (°C) ↔ Fahrenheit (°F).
- **Wind Speed**: km/h ↔ mph ↔ m/s.
- **Pressure**: hPa ↔ inHg.
- Preferences automatically persisted across sessions (`desktop/storage.py` JSON file on desktop, `localStorage` on web).

### 5. Local Time, Auto-Refresh & Offline Fallback
- Displays the local time of the searched city.
- "Last updated X min ago" timestamp with a manual refresh button.
- Background auto-refresh timer every 10 minutes.
- **Offline Fallback**: If an internet interruption occurs, the desktop app immediately restores the last cached weather snapshot with an explicit notice (`⚠️ No connection - showing last saved data`).

### 6. Dynamic Atmospheric Themes & Particle Animations
- Background color gradients and canvas particles dynamically reflect the current WMO weather code and day/night cycle:
  - ☀️ **Clear Sky**: Sunbeam shimmer.
  - ☁️ **Cloudy / Overcast**: Drifting clouds.
  - 🌫️ **Fog**: Soft misty atmosphere.
  - 🌧️ **Rain / Drizzle**: Falling raindrops with angled trajectory.
  - ❄️ **Snow**: Swirling snowflakes with sinusoidal horizontal drift.
  - ⚡ **Thunderstorm**: Heavy rain with lightning flashes.
- Responsive mobile design reduces particle density on screens under 640px and honors `prefers-reduced-motion`.

---

## 📂 Project Organization

```text
RealTimeWeatherApp/
├── desktop/                    # Compulsory Python Tkinter Desktop Application
│   ├── app.py                  # Desktop application entrypoint
│   ├── api_client.py           # Threaded Open-Meteo client (5s timeout)
│   ├── storage.py              # Local JSON persistence (units, favorites, cache)
│   └── ui/
│       ├── main_window.py      # Main window, Canvas layout & queue dispatch
│       ├── panels.py           # Pillow glassmorphism renderer & image cache
│       ├── search_bar.py       # Debounced search & autocomplete dropdown
│       ├── current_weather.py  # Hero weather card & local time
│       ├── details_grid.py     # UV, AQI, visibility, dew point, cloud cover tiles
│       ├── forecast.py         # Hourly chart & 7-day outlook
│       ├── animations.py       # Canvas 30fps particle engine
│       └── theme.py            # Weather-dependent gradient palettes
├── web/                        # Modern Mobile-First Web Application
│   ├── index.html              # Accessible HTML5 dashboard (<meta viewport>)
│   ├── css/
│   │   └── style.css           # Mobile-first CSS, glassmorphism & media queries
│   ├── js/
│   │   ├── app.js              # Application logic & Geolocation controller
│   │   └── weather-engine.js   # WMO mapping & AQI scales
├── shared/                     # Shared weather engine logic
│   ├── __init__.py
│   └── weather_codes.py        # WMO code to condition, icon, theme, and animation
├── requirements.txt            # Python dependencies (Pillow, requests)
├── vercel.json                 # Static site configuration (outputDirectory: "web")
├── package.json                # Project metadata
├── .gitignore                  # Clean Git exclusion file
└── README.md                   # Full documentation
```

---

## 💻 Running the Desktop Application

### Prerequisites
- Python 3.10+ installed.

```bash
# 1. Clone the repository
git clone https://github.com/naaaditya2007-tech/skycast-weather-dashboard.git
cd skycast-weather-dashboard

# 2. Install dependencies (Pillow and requests only)
pip install -r requirements.txt

# 3. Launch the desktop GUI
python desktop/app.py
```

### Keyboard Shortcuts:
- **Enter**: Search for city in search field.
- **Escape**: Clear search bar and dismiss autocomplete suggestions.
- **Down Arrow**: Focus autocomplete dropdown.

---

## 🌐 Running the Web Application

The web version runs purely client-side without any backend server.

### Local Development:
```bash
# Using Python built-in static server
python -m http.server 3000 --directory web

# Or using Node.js serve
npx serve web
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Responsive Breakpoints Tested:
- **320px** (Ultra-compact mobile): Single column, 2-column details grid, zero horizontal overflow.
- **375px** (Standard mobile): Touch targets $\ge$ 44px, input font-size 16px.
- **768px** (Tablet): 3-column details grid, horizontal swipe hourly forecast.
- **1280px** (Desktop): Split layout (Hero & Metrics on left, Forecasts on right).

---

## 🔒 Privacy & Data Usage

- **Zero Tracking**: SkyCast never records or transmits your browsing activity.
- **Location Safety**: Geolocation is only retrieved on-demand when the user approves. Raw latitude and longitude coordinates are never displayed on screen and never stored on remote servers.
- **Keyless Architecture**: By using Open-Meteo's open endpoints, no private API keys are ever stored or exposed.

---

## 📜 Acknowledgments & License

- Weather forecasts, geocoding, and air quality data generously provided by [Open-Meteo](https://open-meteo.com/).
- Reverse geocoding provided by [BigDataCloud](https://www.bigdatacloud.net/).
- Distributed under the **MIT License**. See `LICENSE` for details.
