'use client';

import React, { useState, useEffect, useCallback } from 'react';
import WeatherCanvas from '../components/WeatherCanvas';
import HeroCard from '../components/HeroCard';
import ForecastCard from '../components/ForecastCard';
import OverviewGrid from '../components/OverviewGrid';
import OtherCitiesSidebar from '../components/OtherCitiesSidebar';
import SearchBar from '../components/SearchBar';
import SettingsModal from '../components/SettingsModal';
import { getWeatherInfo, DEFAULT_INDIAN_FAVORITES } from '../lib/weatherCodes';
import { CloudSun, RefreshCw, Sliders, LocateFixed, AlertCircle } from 'lucide-react';

const CHENNAI_DEFAULT = {
  name: 'Chennai',
  admin1: 'Tamil Nadu',
  country: 'India',
  latitude: 13.0827,
  longitude: 80.2707
};

export default function Home() {
  const [currentCity, setCurrentCity] = useState(CHENNAI_DEFAULT);
  const [weatherData, setWeatherData] = useState(null);
  const [aqiData, setAqiData] = useState(null);
  const [favorites, setFavorites] = useState(DEFAULT_INDIAN_FAVORITES);
  const [tempUnit, setTempUnit] = useState('celsius');
  const [windUnit, setWindUnit] = useState('kmh');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [customTheme, setCustomTheme] = useState(null); // For F2 theme previews

  // Load saved preferences from LocalStorage
  useEffect(() => {
    try {
      const savedCity = localStorage.getItem('skycast_city');
      if (savedCity) setCurrentCity(JSON.parse(savedCity));

      const savedFavs = localStorage.getItem('skycast_favs');
      if (savedFavs) setFavorites(JSON.parse(savedFavs));

      const savedTemp = localStorage.getItem('skycast_temp');
      if (savedTemp) setTempUnit(savedTemp);

      const savedWind = localStorage.getItem('skycast_wind');
      if (savedWind) setWindUnit(savedWind);
    } catch (e) {
      // Ignore
    }
  }, []);

  // Fetch live weather data from Open-Meteo REST APIs
  const fetchWeather = useCallback(
    async (lat, lon, unit = tempUnit, wind = windUnit) => {
      setIsLoading(true);
      setErrorMessage(null);

      const tempParam = unit === 'fahrenheit' ? '&temperature_unit=fahrenheit' : '';
      const windParam = wind === 'mph' ? '&wind_speed_unit=mph' : (wind === 'ms' ? '&wind_speed_unit=ms' : '');

      try {
        // 1. Forecast API (Current + 24h Hourly + 16-Day Daily)
        const forecastUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,cloud_cover,surface_pressure,wind_speed_10m,wind_direction_10m,dew_point_2m,visibility,uv_index&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,weather_code,surface_pressure,cloud_cover,visibility,wind_speed_10m,wind_direction_10m,uv_index,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max&forecast_days=16${tempParam}${windParam}&timezone=auto`;

        // 2. Air Quality API (European AQI + US AQI + PM2.5)
        const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=european_aqi,us_aqi,pm2_5,pm10`;

        const [forecastRes, aqiRes] = await Promise.all([
          fetch(forecastUrl),
          fetch(aqiUrl).catch(() => null)
        ]);

        if (!forecastRes.ok) throw new Error('Could not retrieve forecast');
        const forecastJson = await forecastRes.json();
        setWeatherData(forecastJson);

        if (aqiRes && aqiRes.ok) {
          const aqiJson = await aqiRes.json();
          setAqiData(aqiJson);
        }
      } catch (err) {
        setErrorMessage('Failed to connect to weather service. Please check your internet connection.');
      } finally {
        setIsLoading(false);
      }
    },
    [tempUnit, windUnit]
  );

  // Trigger fetch on city or unit change
  useEffect(() => {
    fetchWeather(currentCity.latitude, currentCity.longitude);
  }, [currentCity, tempUnit, windUnit, fetchWeather]);

  // Handle City Selection
  const handleSelectCity = (city) => {
    setCurrentCity(city);
    setCustomTheme(null);
    try {
      localStorage.setItem('skycast_city', JSON.stringify(city));
    } catch (e) {
      // Ignore
    }
  };

  // Add Favorite
  const handleAddFavorite = (city) => {
    const exists = favorites.some((f) => f.name.toLowerCase() === city.name.toLowerCase());
    if (exists) return;
    const nextFavs = [city, ...favorites].slice(0, 10);
    setFavorites(nextFavs);
    try {
      localStorage.setItem('skycast_favs', JSON.stringify(nextFavs));
    } catch (e) {
      // Ignore
    }
  };

  // Remove Favorite
  const handleRemoveFavorite = (cityName) => {
    const nextFavs = favorites.filter((f) => f.name.toLowerCase() !== cityName.toLowerCase());
    setFavorites(nextFavs);
    try {
      localStorage.setItem('skycast_favs', JSON.stringify(nextFavs));
    } catch (e) {
      // Ignore
    }
  };

  // Reset Favorites to Indian Metros
  const handleResetFavorites = () => {
    setFavorites(DEFAULT_INDIAN_FAVORITES);
    try {
      localStorage.setItem('skycast_favs', JSON.stringify(DEFAULT_INDIAN_FAVORITES));
    } catch (e) {
      // Ignore
    }
  };

  // Temperature unit toggle
  const handleToggleTemp = (unit) => {
    setTempUnit(unit);
    try {
      localStorage.setItem('skycast_temp', unit);
    } catch (e) {
      // Ignore
    }
  };

  // Wind unit change
  const handleSetWind = (unit) => {
    setWindUnit(unit);
    try {
      localStorage.setItem('skycast_wind', unit);
    } catch (e) {
      // Ignore
    }
  };

  // Geolocation lookup
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    setIsLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        try {
          const res = await fetch(
            `https://geocoding-api.open-meteo.com/v1/search?name=${lat.toFixed(2)},${lon.toFixed(2)}&count=1&language=en&format=json`
          );
          const data = await res.json();
          const first = data.results?.[0];
          const newCity = {
            name: first?.name || 'My Location',
            admin1: first?.admin1 || '',
            country: first?.country || '',
            latitude: lat,
            longitude: lon
          };
          handleSelectCity(newCity);
        } catch (e) {
          handleSelectCity({
            name: 'My Location',
            latitude: lat,
            longitude: lon
          });
        }
      },
      () => {
        setIsLoading(false);
        alert('Unable to retrieve your location');
      }
    );
  };

  // Determine active visual theme (Live or Preset)
  const currentWmo = weatherData?.current?.weather_code ?? 0;
  const currentIsDay = weatherData?.current?.is_day ?? 1;
  const liveInfo = getWeatherInfo(currentWmo, currentIsDay);
  const activeWeatherTheme = customTheme ? customTheme.theme : liveInfo.theme;
  const activeIsDay = customTheme ? customTheme.isDay : currentIsDay;

  return (
    <main className="relative min-h-screen w-full flex flex-col justify-between overflow-x-hidden p-3 sm:p-6 lg:p-8">
      {/* 60 FPS HTML5 Canvas Atmospheric Particle Engine */}
      <WeatherCanvas weatherTheme={activeWeatherTheme} isDay={activeIsDay} />

      {/* Atmospheric Radial Backlighting */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto w-full flex flex-col gap-5 sm:gap-6">
        {/* Top Navigation Bar */}
        <header className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-3 sm:p-4 shadow-2xl flex items-center justify-between gap-3 flex-wrap">
          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5 pl-1 sm:pl-2">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sky-400 to-amber-300 p-0.5 shadow-[0_0_20px_rgba(56,189,248,0.4)] flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <CloudSun className="w-6 h-6 text-amber-300 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
              </div>
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tight text-white leading-tight flex items-center gap-1.5">
                SkyCast
                <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  Next-Gen
                </span>
              </h1>
              <p className="text-[11px] font-medium text-slate-400 hidden sm:block">
                Atmospheric Weather Intelligence
              </p>
            </div>
          </div>

          {/* Autocomplete Search Bar */}
          <div className="flex-1 max-w-md mx-auto order-3 sm:order-2 w-full sm:w-auto">
            <SearchBar onSelectCity={handleSelectCity} onUseMyLocation={handleUseMyLocation} />
          </div>

          {/* Actions & Controls */}
          <div className="flex items-center gap-2 sm:gap-2.5 order-2 sm:order-3">
            {/* Geolocation Button */}
            <button
              type="button"
              onClick={handleUseMyLocation}
              title="Use current location"
              className="p-2 sm:px-3 sm:py-2 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-all flex items-center gap-1.5 text-xs font-semibold"
            >
              <LocateFixed className="w-4 h-4 text-sky-400" />
              <span className="hidden md:inline">Locate</span>
            </button>

            {/* Quick Unit Toggle */}
            <div className="flex items-center p-0.5 rounded-2xl bg-slate-950/40 border border-white/10">
              <button
                type="button"
                onClick={() => handleToggleTemp('celsius')}
                className={`px-2.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  tempUnit === 'celsius'
                    ? 'bg-sky-500 text-white shadow-[0_0_10px_rgba(14,165,233,0.4)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                °C
              </button>
              <button
                type="button"
                onClick={() => handleToggleTemp('fahrenheit')}
                className={`px-2.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  tempUnit === 'fahrenheit'
                    ? 'bg-sky-500 text-white shadow-[0_0_10px_rgba(14,165,233,0.4)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                °F
              </button>
            </div>

            {/* Refresh Button */}
            <button
              type="button"
              onClick={() => fetchWeather(currentCity.latitude, currentCity.longitude)}
              title="Refresh weather data"
              className="p-2 sm:p-2.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-sky-400 hover:text-sky-300 transition-all group"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-sky-400' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
            </button>

            {/* Settings & Themes Button */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              title="Weather themes & settings"
              className="p-2 sm:p-2.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-all"
            >
              <Sliders className="w-4 h-4 text-sky-400" />
            </button>
          </div>
        </header>

        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="backdrop-blur-xl bg-rose-500/15 border border-rose-500/30 text-rose-200 px-4 py-3 rounded-2xl text-xs sm:text-sm font-semibold flex items-center gap-2 shadow-lg animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Custom Theme Indicator Pill (if preview active) */}
        {customTheme && (
          <div className="self-center px-4 py-1.5 rounded-full bg-sky-500/20 border border-sky-400/30 text-sky-300 text-xs font-bold flex items-center gap-2 backdrop-blur-md shadow-[0_0_15px_rgba(56,189,248,0.3)]">
            <span>🎮 Atmospheric Preview: {customTheme.label}</span>
            <button
              onClick={() => setCustomTheme(null)}
              className="ml-2 underline text-white hover:text-sky-200"
            >
              Reset Live
            </button>
          </div>
        )}

        {/* Master Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6">
          {/* Main Left & Center Content (8 cols on lg) */}
          <div className="lg:col-span-8 flex flex-col gap-5 sm:gap-6">
            {/* Top Row: Hero Card & Forecast Tabs Card */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-5 sm:gap-6">
              <div className="md:col-span-5 flex flex-col">
                <HeroCard
                  currentCity={currentCity}
                  weatherData={weatherData}
                  tempUnit={tempUnit}
                />
              </div>

              <div className="md:col-span-7 flex flex-col">
                <ForecastCard
                  weatherData={weatherData}
                  tempUnit={tempUnit}
                />
              </div>
            </div>

            {/* Lower Row: 6 Overview Bento Tiles */}
            <OverviewGrid
              weatherData={weatherData}
              aqiData={aqiData}
              windUnit={windUnit}
            />
          </div>

          {/* Right Column: Other Cities Sidebar (4 cols on lg) */}
          <div className="lg:col-span-4 flex flex-col">
            <OtherCitiesSidebar
              currentCity={currentCity}
              onSelectCity={handleSelectCity}
              favorites={favorites}
              onAddFavorite={handleAddFavorite}
              onRemoveFavorite={handleRemoveFavorite}
              tempUnit={tempUnit}
            />
          </div>
        </div>
      </div>

      {/* Settings & Theme Switcher Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        tempUnit={tempUnit}
        onToggleTempUnit={handleToggleTemp}
        windUnit={windUnit}
        onSetWindUnit={handleSetWind}
        onApplyThemePreset={(theme, isDay, label) => {
          setCustomTheme({ theme, isDay, label });
          setIsSettingsOpen(false);
        }}
        onRestoreLiveWeather={() => {
          setCustomTheme(null);
          setIsSettingsOpen(false);
        }}
        onResetFavorites={handleResetFavorites}
        isCustomThemeActive={Boolean(customTheme)}
      />

      {/* Footer */}
      <footer className="relative z-10 text-center py-4 text-xs text-slate-500 font-medium">
        Powered by <a href="https://open-meteo.com" target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">Open-Meteo</a> APIs • Built with Next.js 14, Tailwind CSS & 60 FPS Canvas Graphics
      </footer>
    </main>
  );
}
