/**
 * SkyCast Web Application — Main Logic & Geolocation Controller
 * Complies with strict privacy standards (one-shot geolocation, no background tracking, no raw coords exposed).
 */

import { getWeatherInfo } from "./weather-engine.js";

// Storage Keys
const STORAGE_UNIT = "skycast_unit";
const STORAGE_LAST_CITY = "skycast_last_city";
const STORAGE_GEO_DENIED = "skycast_geo_denied";

// State
let currentUnit = localStorage.getItem(STORAGE_UNIT) || "celsius";
let currentLat = 51.5074;
let currentLon = -0.1278;
let currentCityName = "London";
let currentCountryName = "United Kingdom";
let weatherData = null;
let searchTimeout = null;

// DOM Elements
const bodyEl = document.body;
const cityInput = document.getElementById("cityInput");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const autocompleteList = document.getElementById("autocompleteList");
const searchForm = document.getElementById("searchForm");
const locBtn = document.getElementById("locBtn");
const refreshBtn = document.getElementById("refreshBtn");
const unitCelsiusBtn = document.getElementById("unitCelsius");
const unitFahrenheitBtn = document.getElementById("unitFahrenheit");

const statusBanner = document.getElementById("statusBanner");
const bannerIcon = document.getElementById("bannerIcon");
const bannerText = document.getElementById("bannerText");
const closeBannerBtn = document.getElementById("closeBannerBtn");

const cityNameEl = document.getElementById("cityName");
const locationDetailEl = document.getElementById("locationDetail");
const weatherIconEl = document.getElementById("weatherIcon");
const currentTempEl = document.getElementById("currentTemp");
const tempUnitEl = document.getElementById("tempUnit");
const conditionTitleEl = document.getElementById("conditionTitle");
const feelsLikeEl = document.getElementById("feelsLike");
const humidityValEl = document.getElementById("humidityVal");
const windValEl = document.getElementById("windVal");
const pressureValEl = document.getElementById("pressureVal");
const precipValEl = document.getElementById("precipVal");
const hourlyContainer = document.getElementById("hourlyContainer");
const dailyContainer = document.getElementById("dailyContainer");
const loadingOverlay = document.getElementById("loadingOverlay");
const weatherCanvas = document.getElementById("weatherCanvas");

// Particle Animation Engine
class WebWeatherAnimator {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.particles = [];
    this.animationType = "none";
    this.animationId = null;
    this.flashAlpha = 0;

    this.resize = this.resize.bind(this);
    this.tick = this.tick.bind(this);
    window.addEventListener("resize", this.resize);
    this.resize();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  setAnimation(type) {
    if (this.animationType === type) return;
    this.animationType = type;
    this.particles = [];
    const w = this.canvas.width;
    const h = this.canvas.height;

    if (type === "rain" || type === "thunderstorm") {
      const count = type === "thunderstorm" ? 120 : 80;
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          len: 12 + Math.random() * 10,
          speed: 12 + Math.random() * 8,
          width: Math.random() > 0.8 ? 2 : 1
        });
      }
    } else if (type === "snow") {
      for (let i = 0; i < 70; i++) {
        this.particles.push({
          x: Math.random() * w,
          baseX: Math.random() * w,
          y: Math.random() * h,
          radius: 1.5 + Math.random() * 2.5,
          speed: 1 + Math.random() * 2,
          angle: Math.random() * Math.PI * 2,
          driftSpeed: 0.02 + Math.random() * 0.03
        });
      }
    } else if (type === "sunbeam") {
      for (let i = 0; i < 40; i++) {
        this.particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          radius: 1.2 + Math.random() * 2.2,
          vx: (Math.random() - 0.5) * 0.6,
          vy: (Math.random() - 0.5) * 0.6,
          alpha: 0.3 + Math.random() * 0.4
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

      // Lightning effect
      if (this.animationType === "thunderstorm") {
        if (this.flashAlpha > 0) {
          ctx.fillStyle = `rgba(255, 255, 255, ${this.flashAlpha})`;
          ctx.fillRect(0, 0, w, h);
          this.flashAlpha -= 0.15;
        } else if (Math.random() < 0.012) {
          this.flashAlpha = 0.65;
        }
      }
    } else if (this.animationType === "snow") {
      ctx.fillStyle = "rgba(241, 245, 249, 0.85)";
      for (const p of this.particles) {
        p.y += p.speed;
        p.angle += p.driftSpeed;
        p.x = p.baseX + Math.sin(p.angle) * 20;

        if (p.y > h) {
          p.y = -10;
          p.baseX = Math.random() * w;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    } else if (this.animationType === "sunbeam") {
      ctx.fillStyle = "rgba(253, 224, 71, 0.4)";
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

// ---------------- Initialize Application ----------------
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  updateUnitToggleUI();

  // Check saved city or attempt browser geolocation
  const savedCity = localStorage.getItem(STORAGE_LAST_CITY);
  if (savedCity) {
    try {
      const parsed = JSON.parse(savedCity);
      currentLat = parsed.lat;
      currentLon = parsed.lon;
      currentCityName = parsed.name;
      currentCountryName = parsed.country;
      fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
      return;
    } catch (e) {
      // Fallback
    }
  }

  // Auto Geolocation on initial load if not previously denied
  const wasDenied = localStorage.getItem(STORAGE_GEO_DENIED);
  if (!wasDenied && "geolocation" in navigator) {
    requestUserLocation(false);
  } else {
    // Default to London if denied or unavailable
    fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
  }
});

// ---------------- Event Listeners ----------------
function setupEventListeners() {
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSearchSubmit();
  });

  cityInput.addEventListener("input", () => {
    const query = cityInput.value.trim();
    clearSearchBtn.hidden = query.length === 0;
    if (searchTimeout) clearTimeout(searchTimeout);
    if (query.length >= 2) {
      searchTimeout = setTimeout(() => fetchCitySuggestions(query), 300);
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

  locBtn.addEventListener("click", () => {
    requestUserLocation(true);
  });

  refreshBtn.addEventListener("click", () => {
    fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
  });

  unitCelsiusBtn.addEventListener("click", () => switchUnit("celsius"));
  unitFahrenheitBtn.addEventListener("click", () => switchUnit("fahrenheit"));

  closeBannerBtn.addEventListener("click", () => {
    statusBanner.hidden = true;
  });
}

// ---------------- Geolocation Engine ----------------
function requestUserLocation(isUserInitiated = false) {
  if (!("geolocation" in navigator)) {
    showBanner("Geolocation is not supported by your browser. Please search manually.", "warning");
    return;
  }

  showLoading("Detecting your location via GPS...");

  const options = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 60000
  };

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      hideLoading();
      localStorage.removeItem(STORAGE_GEO_DENIED);
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      // Reverse geocode to find city and country
      const location = await reverseGeocode(lat, lon);
      currentLat = lat;
      currentLon = lon;
      currentCityName = location.city;
      currentCountryName = location.country;

      saveLastLocation(currentCityName, currentCountryName, currentLat, currentLon);
      showBanner(`📍 Detected location: ${currentCityName}, ${currentCountryName}`);
      fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
    },
    (error) => {
      hideLoading();
      if (error.code === error.PERMISSION_DENIED) {
        localStorage.setItem(STORAGE_GEO_DENIED, "true");
        if (isUserInitiated) {
          showBanner("Location permission was denied. You can search for any city manually above.", "warning");
        }
      } else if (error.code === error.TIMEOUT) {
        showBanner("Location request timed out. Please try searching for your city manually.", "warning");
      } else {
        showBanner("Location information is currently unavailable. Please search manually.", "warning");
      }
      // If we don't have weather yet, load default
      if (!weatherData) {
        fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
      }
    },
    options
  );
}

// Reverse Geocoding via Vercel API or direct fallback
async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(`/api/geocode?lat=${lat}&lon=${lon}`);
    if (res.ok) {
      const data = await res.json();
      return {
        city: data.city || "Current Location",
        country: data.country || ""
      };
    }
  } catch (err) {
    console.warn("Backend reverse geocode failed, using direct fallback", err);
  }

  // Fallback to direct client reverse geocoding
  try {
    const fallbackRes = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`
    );
    if (fallbackRes.ok) {
      const data = await fallbackRes.json();
      return {
        city: data.city || data.locality || data.principalSubdivision || "Current Location",
        country: data.countryName || ""
      };
    }
  } catch (err) {
    console.error("Direct reverse geocode failed", err);
  }

  return { city: "Current Location", country: "" };
}

// ---------------- City Search & Autocomplete ----------------
async function fetchCitySuggestions(query) {
  try {
    let results = [];
    try {
      const res = await fetch(`/api/geocode?city=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        results = data.results || [];
      }
    } catch (e) {
      // Backend proxy unavailable, will fall through to direct Open-Meteo geocoding
    }

    if (!results || results.length === 0) {
      // Direct Open-Meteo geocoding fallback
      const direct = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=en&format=json`
      );
      const directData = await direct.json();
      results = (directData.results || []).map((r) => ({
        name: r.name,
        display_name: r.admin1 ? `${r.name}, ${r.admin1}, ${r.country}` : `${r.name}, ${r.country}`,
        country: r.country || "",
        latitude: r.latitude,
        longitude: r.longitude
      }));
    }

    renderAutocomplete(results);
  } catch (err) {
    console.error("Suggestion error:", err);
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
    div.innerHTML = `<span>📍</span> <span>${escapeHtml(item.display_name)}</span>`;
    div.addEventListener("click", () => {
      selectCity(item);
    });
    autocompleteList.appendChild(div);
  });

  autocompleteList.hidden = false;
}

function hideAutocomplete() {
  autocompleteList.hidden = true;
  autocompleteList.innerHTML = "";
}

function selectCity(item) {
  cityInput.value = item.name;
  clearSearchBtn.hidden = false;
  hideAutocomplete();

  currentLat = item.latitude;
  currentLon = item.longitude;
  currentCityName = item.name;
  currentCountryName = item.country;

  saveLastLocation(currentCityName, currentCountryName, currentLat, currentLon);
  fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
}

async function handleSearchSubmit() {
  const query = cityInput.value.trim();
  if (!query) return;

  hideAutocomplete();
  showLoading(`Searching weather for "${query}"...`);

  try {
    let results = [];
    const res = await fetch(`/api/geocode?city=${encodeURIComponent(query)}`);
    if (res.ok) {
      const data = await res.json();
      results = data.results || [];
    }

    if (!results || results.length === 0) {
      const direct = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&language=en&format=json`
      );
      const directData = await direct.json();
      results = directData.results || [];
    }

    hideLoading();

    if (results.length > 0) {
      const top = results[0];
      currentLat = top.latitude;
      currentLon = top.longitude;
      currentCityName = top.name;
      currentCountryName = top.country || "";

      saveLastLocation(currentCityName, currentCountryName, currentLat, currentLon);
      fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
    } else {
      showBanner(`Could not find "${query}". Please check spelling and try again.`, "warning");
    }
  } catch (err) {
    hideLoading();
    showBanner(`Search error: ${err.message}`, "warning");
  }
}

// ---------------- Fetch Weather Data ----------------
async function fetchWeather(lat, lon, city, country) {
  showLoading(`Loading weather for ${city}...`);

  try {
    let data = null;
    const url = `/api/weather?lat=${lat}&lon=${lon}&units=${currentUnit}`;
    const res = await fetch(url);
    if (res.ok) {
      data = await res.json();
    } else {
      throw new Error("Backend weather proxy unavailable");
    }

    renderWeather(data, city, country);
    hideLoading();
  } catch (err) {
    console.warn("Proxy failed, falling back to direct Open-Meteo call:", err);
    try {
      const unitTemp = currentUnit === "fahrenheit" ? "fahrenheit" : "celsius";
      const unitWind = currentUnit === "fahrenheit" ? "mph" : "kmh";
      const directUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=temperature_2m,weather_code,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max&timezone=auto&temperature_unit=${unitTemp}&wind_speed_unit=${unitWind}&forecast_days=7`;

      const directRes = await fetch(directUrl);
      if (!directRes.ok) throw new Error("Open-Meteo API error");
      const directData = await directRes.json();

      renderWeather(directData, city, country);
      hideLoading();
    } catch (e) {
      hideLoading();
      showBanner(`Unable to load weather: ${e.message}`, "warning");
    }
  }
}

// ---------------- Render Weather to DOM ----------------
function renderWeather(data, city, country) {
  if (!data || !data.current) return;
  weatherData = data;

  const curr = data.current;
  const code = curr.weather_code ?? 0;
  const isDay = curr.is_day ?? 1;
  const info = getWeatherInfo(code, isDay);

  // Apply Atmospheric Theme Class to Body
  bodyEl.className = info.themeClass;

  // Apply Particle Animation
  animator.setAnimation(info.animation);

  // Update Hero Card
  cityNameEl.textContent = `📍 ${city}`;
  const now = new Date();
  const dateStr = now.toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "short"
  });
  locationDetailEl.textContent = country ? `${country} • ${dateStr}` : dateStr;

  weatherIconEl.textContent = info.icon;
  currentTempEl.textContent = Math.round(curr.temperature_2m);
  tempUnitEl.textContent = currentUnit === "fahrenheit" ? "°F" : "°C";

  conditionTitleEl.textContent = `${info.condition} — ${info.description}`;
  const unitSym = currentUnit === "fahrenheit" ? "°F" : "°C";
  feelsLikeEl.textContent = `Feels like ${Math.round(curr.apparent_temperature)}${unitSym}`;

  // Update Metrics
  humidityValEl.textContent = `${curr.relative_humidity_2m ?? "--"}%`;
  const windUnit = currentUnit === "fahrenheit" ? "mph" : "km/h";
  windValEl.textContent = `${curr.wind_speed_10m ?? "--"} ${windUnit}`;
  pressureValEl.textContent = `${Math.round(curr.surface_pressure ?? 1013)} hPa`;
  precipValEl.textContent = `${curr.precipitation ?? 0} mm`;

  // Render Hourly Forecast
  renderHourly(data.hourly);

  // Render 7-Day Forecast
  renderDaily(data.daily);
}

function renderHourly(hourly) {
  if (!hourly || !hourly.time) return;
  hourlyContainer.innerHTML = "";

  const times = hourly.time.slice(0, 24);
  const temps = hourly.temperature_2m.slice(0, 24);
  const codes = hourly.weather_code.slice(0, 24);
  const isDays = hourly.is_day || [];
  const unitSym = currentUnit === "fahrenheit" ? "°F" : "°C";

  times.forEach((t, i) => {
    const dt = new Date(t);
    const hourLabel = dt.toLocaleTimeString([], { hour: "numeric" });
    const code = codes[i];
    const isDay = isDays[i] !== undefined ? isDays[i] : 1;
    const info = getWeatherInfo(code, isDay);

    const card = document.createElement("div");
    card.className = "hour-card glass-subcard";
    card.innerHTML = `
      <span class="hour-time">${hourLabel}</span>
      <span class="hour-icon" role="img" aria-label="${info.condition}">${info.icon}</span>
      <span class="hour-temp">${Math.round(temps[i])}${unitSym}</span>
    `;
    hourlyContainer.appendChild(card);
  });
}

function renderDaily(daily) {
  if (!daily || !daily.time) return;
  dailyContainer.innerHTML = "";

  const dates = daily.time.slice(0, 7);
  const maxTemps = daily.temperature_2m_max.slice(0, 7);
  const minTemps = daily.temperature_2m_min.slice(0, 7);
  const codes = daily.weather_code.slice(0, 7);
  const precips = daily.precipitation_probability_max || [];
  const unitSym = currentUnit === "fahrenheit" ? "°F" : "°C";

  dates.forEach((dateStr, i) => {
    const dt = new Date(dateStr + "T00:00:00");
    const dayName = i === 0 ? "Today" : dt.toLocaleDateString(undefined, { weekday: "short" });
    const formattedDate = dt.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    const code = codes[i];
    const info = getWeatherInfo(code, 1);
    const rainProb = precips[i] !== undefined && precips[i] !== null ? `${precips[i]}%` : "--";

    const row = document.createElement("div");
    row.className = "daily-row glass-subcard";
    row.innerHTML = `
      <div class="daily-meta">
        <span class="daily-day">${dayName}</span>
        <span class="daily-date">${formattedDate}</span>
      </div>
      <div class="daily-condition">
        <span class="daily-icon" role="img" aria-label="${info.condition}">${info.icon}</span>
        <span>${info.condition}</span>
      </div>
      <div class="daily-precip" title="Chance of Precipitation">
        💧 ${rainProb}
      </div>
      <div class="daily-temps">
        <span class="daily-high">${Math.round(maxTemps[i])}${unitSym}</span>
        <span class="daily-low">${Math.round(minTemps[i])}${unitSym}</span>
      </div>
    `;
    dailyContainer.appendChild(row);
  });
}

// ---------------- Helpers & Unit Toggle ----------------
function switchUnit(unit) {
  if (currentUnit === unit) return;
  currentUnit = unit;
  localStorage.setItem(STORAGE_UNIT, unit);
  updateUnitToggleUI();
  fetchWeather(currentLat, currentLon, currentCityName, currentCountryName);
}

function updateUnitToggleUI() {
  if (currentUnit === "celsius") {
    unitCelsiusBtn.classList.add("active");
    unitFahrenheitBtn.classList.remove("active");
  } else {
    unitFahrenheitBtn.classList.add("active");
    unitCelsiusBtn.classList.remove("active");
  }
}

function saveLastLocation(name, country, lat, lon) {
  localStorage.setItem(STORAGE_LAST_CITY, JSON.stringify({ name, country, lat, lon }));
}

function showBanner(message, type = "info") {
  bannerText.textContent = message;
  bannerIcon.textContent = type === "warning" ? "⚠️" : "📍";
  statusBanner.className = `status-banner ${type === "warning" ? "banner-warning" : ""}`;
  statusBanner.hidden = false;
}

function showLoading(msg = "Loading weather...") {
  const loadingMsg = document.getElementById("loadingMessage");
  if (loadingMsg) loadingMsg.textContent = msg;
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
