/**
 * SkyCast Modern Web Application — Main Logic & Controller
 * ---------------------------------------------------------
 * Connects directly to Open-Meteo APIs via native browser `fetch()`:
 * - Forecast API: Weather metrics, hourly timeline, 7-day outlook
 * - Geocoding API: City lookup with 300ms debounced autocomplete
 * - Air Quality API: European AQI, PM2.5, PM10
 * - Reverse Geocoding: BigDataCloud reverse geocode client
 *
 * Privacy Standards:
 * - Single-shot `navigator.geolocation.getCurrentPosition()` only (never `watchPosition`)
 * - Denial state remembered in localStorage to prevent repeated prompts
 * - Coordinates strictly used to resolve city/country; never exposed in the UI
 */

import { getWeatherInfo, getAqiLevel, getUvLevel } from "./weather-engine.js";

// Storage Keys
const STORAGE_UNITS = "skycast_units_v2";
const STORAGE_LAST_CITY = "skycast_last_city_v2";
const STORAGE_RECENT = "skycast_recent_searches_v2";
const STORAGE_GEO_DENIED = "skycast_geo_denied_v2";

// Default State
let units = {
  temp: "celsius",   // "celsius" | "fahrenheit"
  wind: "kmh",       // "kmh" | "mph" | "ms"
  pressure: "hPa"    // "hPa" | "inHg"
};

let currentCity = {
  name: "London",
  country: "United Kingdom",
  lat: 51.5074,
  lon: -0.1278
};

let weatherData = null;
let lastUpdatedTimestamp = Date.now();
let searchDebounceTimer = null;
let autoRefreshTimer = null;

// DOM Elements
const bodyEl = document.body;
const weatherCanvas = document.getElementById("weatherCanvas");

// Header Controls
const locBtn = document.getElementById("locBtn");
const unitCBtn = document.getElementById("unitC");
const unitFBtn = document.getElementById("unitF");
const windKmhBtn = document.getElementById("windKmh");
const windMphBtn = document.getElementById("windMph");
const windMsBtn = document.getElementById("windMs");
const pressHpaBtn = document.getElementById("pressHpa");
const pressInhgBtn = document.getElementById("pressInhg");

// Search
const searchForm = document.getElementById("searchForm");
const cityInput = document.getElementById("cityInput");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const autocompleteList = document.getElementById("autocompleteList");
const recentSearchesContainer = document.getElementById("recentSearches");

// Banner & Overlay
const statusBanner = document.getElementById("statusBanner");
const bannerIcon = document.getElementById("bannerIcon");
const bannerText = document.getElementById("bannerText");
const closeBannerBtn = document.getElementById("closeBannerBtn");
const loadingOverlay = document.getElementById("loadingOverlay");
const loadingText = document.getElementById("loadingText");

// Hero Elements
const cityNameEl = document.getElementById("cityName");
const localTimeEl = document.getElementById("localTime");
const weatherIconEl = document.getElementById("weatherIcon");
const currentTempEl = document.getElementById("currentTemp");
const tempSymbolEl = document.getElementById("tempSymbol");
const conditionTitleEl = document.getElementById("conditionTitle");
const feelsLikeEl = document.getElementById("feelsLike");
const lastUpdatedEl = document.getElementById("lastUpdated");
const manualRefreshBtn = document.getElementById("manualRefreshBtn");

// Detail Tiles
const uvValEl = document.getElementById("uvVal");
const uvBadgeEl = document.getElementById("uvBadge");
const aqiValEl = document.getElementById("aqiVal");
const aqiBadgeEl = document.getElementById("aqiBadge");
const humidityValEl = document.getElementById("humidityVal");
const windValEl = document.getElementById("windVal");
const windDirEl = document.getElementById("windDir");
const pressureValEl = document.getElementById("pressureVal");
const visibilityValEl = document.getElementById("visibilityVal");
const cloudValEl = document.getElementById("cloudVal");
const dewValEl = document.getElementById("dewVal");
const sunriseValEl = document.getElementById("sunriseVal");
const sunsetValEl = document.getElementById("sunsetVal");

// Forecast Containers
const hourlySlider = document.getElementById("hourlySlider");
const dailyList = document.getElementById("dailyList");

// ============================================================================
// Particle Animation Engine (Optimized for Mobile & Reduced Motion)
// ============================================================================
class WebWeatherAnimator {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.particles = [];
    this.animationType = "none";
    this.animationId = null;
    this.lightningAlpha = 0;

    this.onResize = this.onResize.bind(this);
    this.tick = this.tick.bind(this);
    window.addEventListener("resize", this.onResize);
    this.onResize();
  }

  onResize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  setAnimation(type) {
    if (this.animationType === type) return;
    this.animationType = type;
    this.particles = [];

    // Check if user prefers reduced motion
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    const isSmallScreen = window.innerWidth < 640;
    const w = this.canvas.width;
    const h = this.canvas.height;

    if (type === "rain" || type === "thunderstorm") {
      const count = isSmallScreen ? (type === "thunderstorm" ? 60 : 40) : (type === "thunderstorm" ? 110 : 75);
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * (w + 100),
          y: Math.random() * h,
          len: 12 + Math.random() * 10,
          speed: 11 + Math.random() * 8,
          width: Math.random() > 0.8 ? 2 : 1
        });
      }
    } else if (type === "snow") {
      const count = isSmallScreen ? 35 : 65;
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * w,
          baseX: Math.random() * w,
          y: Math.random() * h,
          radius: 1.5 + Math.random() * 2.5,
          speed: 1.0 + Math.random() * 2.0,
          angle: Math.random() * Math.PI * 2,
          driftSpeed: 0.02 + Math.random() * 0.03
        });
      }
    } else if (type === "sunbeam") {
      const count = isSmallScreen ? 20 : 35;
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          radius: 1.2 + Math.random() * 2.2,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5
        });
      }
    }

    if (!this.animationId) {
      this.tick();
    }
  }

  tick() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);

    if (this.animationType === "rain" || this.animationType === "thunderstorm") {
      ctx.strokeStyle = "rgba(147, 197, 253, 0.7)";
      for (const p of this.particles) {
        ctx.lineWidth = p.width;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - 2, p.y + p.len);
        ctx.stroke();

        p.y += p.speed;
        p.x -= 2;
        if (p.y > h) {
          p.y = -20;
          p.x = Math.random() * (w + 100);
        }
      }

      // Lightning flash
      if (this.animationType === "thunderstorm") {
        if (this.lightningAlpha > 0) {
          ctx.fillStyle = `rgba(255, 255, 255, ${this.lightningAlpha})`;
          ctx.fillRect(0, 0, w, h);
          this.lightningAlpha -= 0.12;
        } else if (Math.random() < 0.012) {
          this.lightningAlpha = 0.65;
        }
      }
    } else if (this.animationType === "snow") {
      ctx.fillStyle = "rgba(241, 245, 249, 0.85)";
      for (const p of this.particles) {
        p.y += p.speed;
        p.angle += p.driftSpeed;
        p.x = p.baseX + Math.sin(p.angle) * 18;

        if (p.y > h) {
          p.y = -10;
          p.baseX = Math.random() * w;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    } else if (this.animationType === "sunbeam") {
      ctx.fillStyle = "rgba(253, 224, 71, 0.35)";
      for (const p of this.particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    this.animationId = requestAnimationFrame(this.tick);
  }
}

const animator = new WebWeatherAnimator(weatherCanvas);

// ============================================================================
// Initialization & Storage Load
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  loadSavedPreferences();
  setupEventListeners();
  renderRecentSearches();

  // Automatic Geolocation on launch if not previously denied
  const wasDenied = localStorage.getItem(STORAGE_GEO_DENIED);
  if (!wasDenied && "geolocation" in navigator) {
    requestUserLocation(false);
  } else {
    // Load last searched city
    fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
  }

  // Auto-refresh interval (every 10 minutes)
  autoRefreshTimer = setInterval(() => {
    fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country, true);
  }, 600000);

  // Update "Last updated X min ago" counter every minute
  setInterval(updateLastUpdatedLabel, 60000);
});

function loadSavedPreferences() {
  try {
    const savedUnits = localStorage.getItem(STORAGE_UNITS);
    if (savedUnits) units = Object.assign(units, JSON.parse(savedUnits));

    const savedCity = localStorage.getItem(STORAGE_LAST_CITY);
    if (savedCity) currentCity = Object.assign(currentCity, JSON.parse(savedCity));
  } catch (e) {
    console.warn("Storage load error:", e);
  }
  updateUnitButtonsUI();
}

// ============================================================================
// Event Listeners
// ============================================================================
function setupEventListeners() {
  // Search Form
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    executeSearch();
  });

  // Debounced input for autocomplete (300ms)
  cityInput.addEventListener("input", () => {
    const q = cityInput.value.trim();
    clearSearchBtn.hidden = q.length === 0;
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    if (q.length >= 2) {
      searchDebounceTimer = setTimeout(() => queryAutocomplete(q), 300);
    } else {
      hideAutocomplete();
    }
  });

  clearSearchBtn.addEventListener("click", () => {
    cityInput.value = "";
    clearSearchBtn.hidden = true;
    hideAutocomplete();
    cityInput.focus();
  });

  document.addEventListener("click", (e) => {
    if (!searchForm.contains(e.target)) {
      hideAutocomplete();
    }
  });

  // Buttons
  locBtn.addEventListener("click", () => requestUserLocation(true));
  manualRefreshBtn.addEventListener("click", () => {
    fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
  });
  closeBannerBtn.addEventListener("click", () => {
    statusBanner.hidden = true;
  });

  // Unit Toggles: Temperature
  unitCBtn.addEventListener("click", () => setUnit("temp", "celsius"));
  unitFBtn.addEventListener("click", () => setUnit("temp", "fahrenheit"));

  // Unit Toggles: Wind
  windKmhBtn.addEventListener("click", () => setUnit("wind", "kmh"));
  windMphBtn.addEventListener("click", () => setUnit("wind", "mph"));
  windMsBtn.addEventListener("click", () => setUnit("wind", "ms"));

  // Unit Toggles: Pressure
  pressHpaBtn.addEventListener("click", () => setUnit("pressure", "hPa"));
  pressInhgBtn.addEventListener("click", () => setUnit("pressure", "inHg"));
}

function setUnit(category, val) {
  if (units[category] === val) return;
  units[category] = val;
  localStorage.setItem(STORAGE_UNITS, JSON.stringify(units));
  updateUnitButtonsUI();
  // Re-fetch weather to recalculate API units
  fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
}

function updateUnitButtonsUI() {
  // Temp
  unitCBtn.classList.toggle("active", units.temp === "celsius");
  unitFBtn.classList.toggle("active", units.temp === "fahrenheit");
  // Wind
  windKmhBtn.classList.toggle("active", units.wind === "kmh");
  windMphBtn.classList.toggle("active", units.wind === "mph");
  windMsBtn.classList.toggle("active", units.wind === "ms");
  // Pressure
  pressHpaBtn.classList.toggle("active", units.pressure === "hPa");
  pressInhgBtn.classList.toggle("active", units.pressure === "inHg");
}

// ============================================================================
// Geolocation Engine
// ============================================================================
function requestUserLocation(isUserInitiated = false) {
  if (!("geolocation" in navigator)) {
    showBanner("Geolocation is not supported by your browser. Please search manually.", "warning");
    return;
  }

  showLoading("Detecting your location via GPS...");

  const options = {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 60000
  };

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      hideLoading();
      localStorage.removeItem(STORAGE_GEO_DENIED);
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;

      // Reverse geocode to find city and country
      const loc = await reverseGeocode(lat, lon);
      currentCity = {
        name: loc.city,
        country: loc.country,
        lat,
        lon
      };
      saveLastCity(currentCity);
      addRecentSearch(currentCity);
      showBanner(`📍 Detected location: ${currentCity.name}, ${currentCity.country}`);
      fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
    },
    (err) => {
      hideLoading();
      if (err.code === err.PERMISSION_DENIED) {
        localStorage.setItem(STORAGE_GEO_DENIED, "true");
        if (isUserInitiated) {
          showBanner("Location permission was denied. You can search for your city above.", "warning");
        }
      } else {
        showBanner("Location detection timed out. Using default location.", "warning");
      }
      if (!weatherData) {
        fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
      }
    },
    options
  );
}

async function reverseGeocode(lat, lon) {
  try {
    const res = await fetchWithTimeout(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`,
      5000
    );
    if (res.ok) {
      const data = await res.json();
      return {
        city: data.city || data.locality || data.principalSubdivision || "Current Location",
        country: data.countryName || ""
      };
    }
  } catch (e) {
    console.warn("Reverse geocode notice:", e);
  }
  return { city: "Current Location", country: "" };
}

// ============================================================================
// City Search & Autocomplete
// ============================================================================
async function queryAutocomplete(query) {
  try {
    const res = await fetchWithTimeout(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=en&format=json`,
      5000
    );
    if (!res.ok) return;
    const data = await res.json();
    const results = data.results || [];
    renderAutocomplete(results);
  } catch (err) {
    console.warn("Autocomplete error:", err);
  }
}

function renderAutocomplete(results) {
  if (!results || results.length === 0) {
    hideAutocomplete();
    return;
  }

  autocompleteList.innerHTML = "";
  results.forEach((item) => {
    const div = document.createElement("div");
    div.className = "autocomplete-item";
    const displayName = item.admin1 ? `${item.name}, ${item.admin1}, ${item.country}` : `${item.name}, ${item.country}`;
    div.innerHTML = `<span>📍</span> <span>${escapeHtml(displayName)}</span>`;
    div.addEventListener("click", () => {
      selectCityItem(item);
    });
    autocompleteList.appendChild(div);
  });

  autocompleteList.hidden = false;
}

function hideAutocomplete() {
  autocompleteList.hidden = true;
  autocompleteList.innerHTML = "";
}

function selectCityItem(item) {
  cityInput.value = item.name;
  clearSearchBtn.hidden = false;
  hideAutocomplete();

  currentCity = {
    name: item.name,
    country: item.country || "",
    lat: item.latitude,
    lon: item.longitude
  };
  saveLastCity(currentCity);
  addRecentSearch(currentCity);
  fetchWeather(currentCity.lat, currentCity.lon, currentCity.name, currentCity.country);
}

async function executeSearch() {
  const q = cityInput.value.trim();
  if (!q) return;

  hideAutocomplete();
  showLoading(`Searching for "${q}"...`);

  try {
    const res = await fetchWithTimeout(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=1&language=en&format=json`,
      5000
    );
    hideLoading();
    if (res.ok) {
      const data = await res.json();
      const results = data.results || [];
      if (results.length > 0) {
        selectCityItem(results[0]);
      } else {
        showBanner(`City "${q}" not found. Please verify spelling.`, "warning");
      }
    }
  } catch (err) {
    hideLoading();
    showBanner(`Search error: ${err.message}`, "warning");
  }
}

// ============================================================================
// Direct Open-Meteo Weather Fetching (Forecast + Air Quality)
// ============================================================================
async function fetchWeather(lat, lon, city, country, silent = false) {
  if (!silent) showLoading(`Loading forecast for ${city}...`);

  const tempParam = units.temp === "fahrenheit" ? "fahrenheit" : "celsius";
  const windParam = units.wind === "mph" ? "mph" : (units.wind === "ms" ? "ms" : "kmh");

  const forecastUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,uv_index,visibility,cloud_cover,dew_point_2m&hourly=temperature_2m,weather_code,is_day,precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max&timezone=auto&temperature_unit=${tempParam}&wind_speed_unit=${windParam}&forecast_days=7&forecast_hours=24`;

  const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=european_aqi,us_aqi,pm10,pm2_5&timezone=auto`;

  try {
    // Parallel fetch with 5s timeout
    const [forecastRes, aqiRes] = await Promise.allSettled([
      fetchWithTimeout(forecastUrl, 5000),
      fetchWithTimeout(aqiUrl, 5000)
    ]);

    if (forecastRes.status !== "fulfilled" || !forecastRes.value.ok) {
      throw new Error("Unable to reach Open-Meteo Forecast API");
    }

    const forecastData = await forecastRes.value.json();

    let aqiData = {};
    if (aqiRes.status === "fulfilled" && aqiRes.value.ok) {
      const aqiJson = await aqiRes.value.json();
      aqiData = aqiJson.current || {};
    }

    forecastData.air_quality = aqiData;
    weatherData = forecastData;
    lastUpdatedTimestamp = Date.now();

    renderDashboard(forecastData, city, country);
    hideLoading();
  } catch (err) {
    hideLoading();
    showBanner(`⚠️ Weather error: ${err.message}. Showing last known data.`, "warning");
  }
}

// ============================================================================
// Render Weather to DOM
// ============================================================================
function renderDashboard(data, city, country) {
  if (!data || !data.current) return;

  const curr = data.current;
  const code = curr.weather_code ?? 0;
  const isDay = curr.is_day ?? 1;
  const info = getWeatherInfo(code, isDay);

  // Apply Atmospheric Theme to Body
  bodyEl.className = info.themeClass;

  // Apply Canvas Particle Animation
  animator.setAnimation(info.animation);

  // 1. Hero Card
  cityNameEl.textContent = `📍 ${city}`;

  // Local Time of searched city
  const timeStr = curr.time || new Date().toISOString();
  try {
    const dt = new Date(timeStr);
    const dateFormatted = dt.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" });
    const timeFormatted = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    localTimeEl.textContent = country ? `${country} • ${dateFormatted} • ${timeFormatted}` : `${dateFormatted} • ${timeFormatted}`;
  } catch (e) {
    localTimeEl.textContent = country || "";
  }

  weatherIconEl.textContent = info.icon;
  currentTempEl.textContent = Math.round(curr.temperature_2m);
  const tempSym = units.temp === "fahrenheit" ? "°F" : "°C";
  tempSymbolEl.textContent = tempSym;

  conditionTitleEl.textContent = `${info.condition} — ${info.description}`;
  feelsLikeEl.textContent = `Feels like ${Math.round(curr.apparent_temperature)}${tempSym}`;
  updateLastUpdatedLabel();

  // 2. Extra Detail Tiles
  // UV Index
  const uvVal = curr.uv_index ?? 0;
  const uvInfo = getUvLevel(uvVal);
  uvValEl.textContent = uvInfo.val;
  uvBadgeEl.textContent = uvInfo.label;
  uvBadgeEl.style.color = uvInfo.color;

  // Air Quality
  const aqiVal = data.air_quality ? data.air_quality.european_aqi : null;
  if (aqiVal !== null && aqiVal !== undefined) {
    const aqiInfo = getAqiLevel(aqiVal);
    aqiValEl.textContent = `AQI ${aqiInfo.val}`;
    aqiBadgeEl.textContent = aqiInfo.label;
    aqiBadgeEl.style.color = aqiInfo.color;
  } else {
    aqiValEl.textContent = "AQI --";
    aqiBadgeEl.textContent = "N/A";
  }

  // Humidity
  humidityValEl.textContent = `${curr.relative_humidity_2m ?? "--"}%`;

  // Wind
  const windUnitLabel = units.wind === "mph" ? "mph" : (units.wind === "ms" ? "m/s" : "km/h");
  windValEl.textContent = `${curr.wind_speed_10m ?? "--"} ${windUnitLabel}`;
  windDirEl.textContent = getWindDirection(curr.wind_direction_10m);

  // Pressure
  const hpa = curr.surface_pressure ?? 1013;
  if (units.pressure === "inHg") {
    pressureValEl.textContent = `${(hpa * 0.02953).toFixed(2)} inHg`;
  } else {
    pressureValEl.textContent = `${Math.round(hpa)} hPa`;
  }

  // Visibility
  const visM = curr.visibility ?? 10000;
  if (units.temp === "fahrenheit") {
    visibilityValEl.textContent = `${(visM / 1609.34).toFixed(1)} mi`;
  } else {
    visibilityValEl.textContent = `${(visM / 1000).toFixed(1)} km`;
  }

  // Cloud Cover
  cloudValEl.textContent = `${curr.cloud_cover ?? "--"}%`;

  // Dew Point
  const dew = curr.dew_point_2m;
  dewValEl.textContent = dew !== undefined ? `${Math.round(dew)}${tempSym}` : "--";

  // Sunrise & Sunset
  const daily = data.daily || {};
  if (daily.sunrise && daily.sunrise[0]) {
    sunriseValEl.textContent = daily.sunrise[0].split("T")[1] || "--:--";
  }
  if (daily.sunset && daily.sunset[0]) {
    sunsetValEl.textContent = daily.sunset[0].split("T")[1] || "--:--";
  }

  // 3. Hourly Forecast (Swipe-scroll row)
  renderHourlyForecast(data.hourly);

  // 4. 7-Day Forecast (Vertical list)
  renderDailyForecast(data.daily);
}

function renderHourlyForecast(hourly) {
  if (!hourly || !hourly.time) return;
  hourlySlider.innerHTML = "";

  const times = hourly.time.slice(0, 24);
  const temps = hourly.temperature_2m.slice(0, 24);
  const codes = hourly.weather_code.slice(0, 24);
  const isDays = hourly.is_day || [];
  const precips = hourly.precipitation_probability || [];
  const tempSym = units.temp === "fahrenheit" ? "°F" : "°C";

  times.forEach((t, i) => {
    const dt = new Date(t);
    const hourLabel = dt.toLocaleTimeString([], { hour: "numeric" });
    const code = codes[i];
    const isD = isDays[i] !== undefined ? isDays[i] : 1;
    const info = getWeatherInfo(code, isD);
    const rainP = precips[i] !== undefined ? precips[i] : 0;

    const card = document.createElement("div");
    card.className = "hour-card glass-subcard";
    card.innerHTML = `
      <span class="hour-time">${hourLabel}</span>
      <span class="hour-icon" role="img" aria-label="${info.condition}">${info.icon}</span>
      <span class="hour-temp">${Math.round(temps[i])}${tempSym}</span>
      <span class="hour-rain" title="Precipitation Probability">💧 ${rainP}%</span>
    `;
    hourlySlider.appendChild(card);
  });
}

function renderDailyForecast(daily) {
  if (!daily || !daily.time) return;
  dailyList.innerHTML = "";

  const dates = daily.time.slice(0, 7);
  const maxTemps = daily.temperature_2m_max.slice(0, 7);
  const minTemps = daily.temperature_2m_min.slice(0, 7);
  const codes = daily.weather_code.slice(0, 7);
  const precips = daily.precipitation_probability_max || [];
  const tempSym = units.temp === "fahrenheit" ? "°F" : "°C";

  dates.forEach((dStr, i) => {
    const dt = new Date(dStr + "T00:00:00");
    const dayName = i === 0 ? "Today" : dt.toLocaleDateString(undefined, { weekday: "short" });
    const dateLabel = dt.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    const code = codes[i];
    const info = getWeatherInfo(code, 1);
    const rainP = precips[i] !== undefined && precips[i] !== null ? precips[i] : 0;

    const row = document.createElement("div");
    row.className = "daily-row glass-subcard";
    row.innerHTML = `
      <div class="daily-meta">
        <span class="daily-day">${dayName}</span>
        <span class="daily-date">${dateLabel}</span>
      </div>
      <div class="daily-condition">
        <span class="daily-icon" role="img" aria-label="${info.condition}">${info.icon}</span>
        <span>${info.condition}</span>
      </div>
      <div class="daily-rain" title="Precipitation Chance">
        💧 ${rainP}%
      </div>
      <div class="daily-temps">
        <span class="daily-high">${Math.round(maxTemps[i])}${tempSym}</span>
        <span class="daily-low">${Math.round(minTemps[i])}${tempSym}</span>
      </div>
    `;
    dailyList.appendChild(row);
  });
}

// ============================================================================
// Recent Searches & Helpers
// ============================================================================
function addRecentSearch(cityObj) {
  try {
    let recent = JSON.parse(localStorage.getItem(STORAGE_RECENT) || "[]");
    recent = recent.filter(c => c.name.toLowerCase() !== cityObj.name.toLowerCase());
    recent.unshift(cityObj);
    recent = recent.slice(0, 5); // Max 5 recent searches
    localStorage.setItem(STORAGE_RECENT, JSON.stringify(recent));
    renderRecentSearches();
  } catch (e) {
    console.warn("Recent search error:", e);
  }
}

function renderRecentSearches() {
  try {
    const recent = JSON.parse(localStorage.getItem(STORAGE_RECENT) || "[]");
    recentSearchesContainer.innerHTML = "";
    if (recent.length === 0) return;

    recent.forEach(c => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "recent-chip";
      chip.textContent = c.name;
      chip.addEventListener("click", () => {
        currentCity = c;
        saveLastCity(c);
        fetchWeather(c.lat, c.lon, c.name, c.country);
      });
      recentSearchesContainer.appendChild(chip);
    });
  } catch (e) {
    // Ignore
  }
}

function saveLastCity(c) {
  localStorage.setItem(STORAGE_LAST_CITY, JSON.stringify(c));
}

function updateLastUpdatedLabel() {
  const elapsedSec = Math.floor((Date.now() - lastUpdatedTimestamp) / 1000);
  const elapsedMin = Math.floor(elapsedSec / 60);
  if (elapsedMin < 1) {
    lastUpdatedEl.textContent = "● Updated just now";
  } else {
    lastUpdatedEl.textContent = `● Updated ${elapsedMin} min ago`;
  }
}

function getWindDirection(deg) {
  if (deg === undefined || deg === null) return "";
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const idx = Math.round(deg / 45) % 8;
  return directions[idx];
}

async function fetchWithTimeout(resource, timeout = 5000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(resource, { signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

function showBanner(msg, type = "info") {
  bannerText.textContent = msg;
  bannerIcon.textContent = type === "warning" ? "⚠️" : "📍";
  statusBanner.className = `status-banner ${type === "warning" ? "banner-warning" : ""}`;
  statusBanner.hidden = false;
}

function showLoading(msg = "Loading weather...") {
  loadingText.textContent = msg;
  loadingOverlay.hidden = false;
}

function hideLoading() {
  loadingOverlay.hidden = true;
}

function escapeHtml(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
