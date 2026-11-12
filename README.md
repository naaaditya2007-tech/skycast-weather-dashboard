# ✦ SkyCast — Real-Time Weather Application & Dashboard

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter%20%2B%20Pillow-blue)
![JavaScript](https://img.shields.io/badge/Web-Modern%20ES6%2B-F7DF1E?logo=javascript&logoColor=black)
![API](https://img.shields.io/badge/API-Open--Meteo-007ACC)
![Deployment](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A dual-platform weather intelligence suite featuring a **Python Tkinter Desktop Application** with canvas glassmorphism and lightweight particle animations, alongside a **responsive Modern Web Dashboard** hosted on Vercel with automatic browser-based geolocation and dynamic atmospheric themes.

---

## 🌟 Key Features

### 🖥️ A. Desktop Application (Python Tkinter)
- **Compulsory Tkinter GUI**: Developed using Python's native Tkinter with Canvas-rendered glassmorphism panels.
- **Glassmorphism Aesthetic**: Custom Pillow-rendered translucent cards with smooth rounded borders.
- **Live Weather Metrics**: Real-time temperature, feels-like, humidity, wind speed & direction, surface pressure, and precipitation.
- **Hourly & 7-Day Outlooks**: Next 24 hours of hourly projections plus a comprehensive 7-day extended forecast.
- **Particle Animation Engine**:
  - 🌧️ **Rain**: Slanted raindrops with variable velocity and splash dynamics.
  - ❄️ **Snow**: Swirling snowflakes with sinusoidal horizontal drift.
  - ☁️ **Drifting Clouds**: Moving atmospheric clouds across the upper horizon.
  - ⚡ **Thunderstorms**: High-velocity downpours with random lightning flash effects.
  - ☀️ **Sunbeams**: Ambient dust/sun motes for clear sunny days.
- **Instant Search with Autocomplete**: Debounced asynchronous city search powered by Open-Meteo geocoding.
- **Unit Toggle**: Instant conversion between Celsius (°C) and Fahrenheit (°F).
- **Responsive Layout**: Auto-adjusts cards and canvas elements smoothly on window resize.

### 🌐 B. Web Application & Dashboard (HTML/CSS/JS)
- **Visual Identity Parity**: Recreates the desktop glassmorphism design with backdrop filters and dynamic gradient transitions.
- **Automatic Browser Geolocation**:
  - Securely requests user location via `navigator.geolocation.getCurrentPosition()`.
  - Reverse geocodes coordinates to display city and country.
  - Privacy-preserving: No continuous background tracking, single-shot request, no raw coordinates exposed.
  - Respects permission denial gracefully with a friendly banner and immediate fallback to manual search.
  - Includes a **Refresh Location** button to re-sync coordinates on demand.
- **Dynamic Atmospheric Backgrounds**: Auto-switches background color palettes and Canvas particle animations according to the live WMO weather condition code and time of day.
- **Fluid & Accessible**: Built adhering to modern responsive standards (`clamp()`, dynamic viewport units `100dvh`, semantic HTML5, high-contrast dark themes).

---

## 📂 Project Organization

```text
SkyCast/
├── desktop/                    # Compulsory Python Tkinter Desktop Application
│   ├── app.py                  # Main entrypoint
│   ├── api_client.py           # Threaded Open-Meteo API client
│   └── ui/
│       ├── main_window.py      # Tkinter window, Canvas layout & interactions
│       ├── panels.py           # Pillow glassmorphism renderer & image cache
│       ├── animations.py       # Canvas particle animations (rain/snow/clouds)
│       └── theme.py            # Weather-dependent color palettes & themes
├── web/                        # Modern Web Application (Deployed to Vercel)
│   ├── index.html              # Semantic HTML5 dashboard
│   ├── css/
│   │   └── style.css           # Glassmorphism styling & dynamic themes
│   ├── js/
│   │   ├── app.js              # Application controller & Geolocation handler
│   │   └── weather-engine.js   # WMO code mapping & theme classification
│   ├── api/                    # Vercel Serverless Functions (Python)
│   │   ├── weather.py          # Weather API proxy
│   │   ├── geocode.py          # Geocoding & reverse geocoding proxy
│   │   └── requirements.txt    # Vercel Python runtime dependencies
│   └── vercel.json             # Sub-directory Vercel deployment configuration
├── shared/                     # Shared weather engine across platforms
│   ├── __init__.py
│   └── weather_codes.py        # WMO weather codes, icons & condition descriptions
├── requirements.txt            # Python dependencies for local desktop execution
├── vercel.json                 # Root Vercel routing configuration
├── package.json                # Project metadata
├── .gitignore                  # Professional Git exclusion file
└── README.md                   # Complete documentation
```

---

## ⚡ Weather Engine & Condition Themes

Both applications leverage **Open-Meteo**, a free and open-source weather API that requires no API keys. Weather codes adhere to the World Meteorological Organization (WMO) standards:

| WMO Codes | Condition | Visual Theme | Particle Animation |
|:---:|:---:|:---:|:---:|
| `0` | Clear Sky | Sunny / Clear Sky (Day & Night) | Sunbeam shimmer |
| `1 - 2` | Mainly Clear / Partly Cloudy | Partly Cloudy (Day & Night) | Drifting clouds |
| `3` | Overcast | Overcast Skies | Soft clouds |
| `45, 48` | Fog / Depositing Rime Fog | Foggy Horizon | Dense mist |
| `51 - 65` | Drizzle & Continuous Rain | Rainy Sky | Falling rain drops |
| `71 - 77` | Snow Fall & Snow Grains | Winter Snow | Swirling snowflakes |
| `80 - 82` | Rain Showers | Passing Showers | Quick rain streaks |
| `85 - 86` | Snow Showers | Snow Flurries | Blizzard particles |
| `95 - 99` | Thunderstorm & Severe Hail | Thunderstorm | Torrential rain + lightning |

---

## 🚀 Getting Started

### 1. Running the Desktop Application (Tkinter)

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/naaaditya2007-tech/skycast-weather-dashboard.git
cd skycast-weather-dashboard

# Install required dependencies
pip install -r requirements.txt

# Run the Tkinter desktop GUI
python desktop/app.py
```

### 2. Running the Web Application Locally

```bash
# Start a local static server inside the web directory
python -m http.server 3000 --directory web

# Open http://localhost:3000 in your browser
```

---

## 🌐 Live Production Deployment

- **Vercel Production URL**: *[Provided below upon deployment confirmation]*
- **GitHub Repository**: [https://github.com/naaaditya2007-tech/skycast-weather-dashboard](https://github.com/naaaditya2007-tech/skycast-weather-dashboard)

---

## 🛡️ Privacy & Geolocation Policy

SkyCast prioritizes user privacy:
1. **No background location tracking**: Geolocation is only accessed on-demand using single-shot `getCurrentPosition`.
2. **Permission memory**: If the user dismisses or denies location access, SkyCast respects the decision and does not repeatedly prompt.
3. **No exposed coordinates**: Raw latitude and longitude are never shown to the user or stored on external servers; they are only used to reverse geocode the city name.
4. **Keyless and secure**: Because Open-Meteo does not require private API keys, no secrets or credentials are baked into client bundles or source control.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
