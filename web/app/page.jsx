'use client';

import React, { useState, useEffect, useCallback } from 'react';
import BackgroundAtmosphere from '../components/BackgroundAtmosphere';
import WeatherCanvas from '../components/WeatherCanvas';
import HeroCard from '../components/HeroCard';
import ForecastCard from '../components/ForecastCard';
import OverviewGrid from '../components/OverviewGrid';
import OtherCitiesSidebar from '../components/OtherCitiesSidebar';
import SearchBar from '../components/SearchBar';
import SettingsModal from '../components/SettingsModal';
import { getWeatherInfo, DEFAULT_INDIAN_FAVORITES } from '../lib/weatherCodes';
import { resolveUserLocation, CHENNAI_DEFAULT } from '../lib/location';
import { CloudSun, RefreshCw, Sliders, LocateFixed, Loader2, AlertCircle } from 'lucide-react';

export default function Home() {
  const [currentCity, setCurrentCity] = useState(CHENNAI_DEFAULT);
  const [weatherData, setWeatherData] = useState(null);
  const [aqiData, setAqiData] = useState(null);
  const [favorites, setFavorites] = useState(DEFAULT_INDIAN_FAVORITES);
  const [tempUnit, setTempUnit] = useState('celsius');
  const [windUnit, setWindUnit] = useState('kmh');
  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [customTheme, setCustomTheme] = useState(null);

  // Auto User Location Detection on Startup
  useEffect(() => {
    let isMounted = true;

    try {
      const savedCity = localStorage.getItem('skycast_city');
      if (savedCity) {
        setCurrentCity(JSON.parse(savedCity));
      } else {
        // Automatic location detection chain (GPS -> IP -> Chennai default)
        resolveUserLocation().then((loc) => {
          if (isMounted && loc) {
            setCurrentCity(loc);
          }
        });
      }

      const savedFavs = localStorage.getItem('skycast_favs');
      if (savedFavs) setFavorites(JSON.parse(savedFavs));

      const savedTemp = localStorage.getItem('skycast_temp');
      if (savedTemp) setTempUnit(savedTemp);

      const savedWind = localStorage.getItem('skycast_wind');
      if (savedWind) setWindUnit(savedWind);
    } catch (e) {
      // Fallback already defaulted to Chennai
    }

    return () => {
      isMounted = false;
    };
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
        setErrorMessage('Failed to connect to weather service. Please check your connection.');
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

  // On-Demand Geolocation Button Trigger
  const handleLocateClick = async () => {
    setIsLocating(true);
    setErrorMessage(null);
    try {
      const loc = await resolveUserLocation();
      if (loc) {
        handleSelectCity(loc);
      }
    } catch (e) {
      // Graceful fallback without crashing
    } finally {
      setIsLocating(false);
    }
  };

  // Determine active visual theme (Live or Preset)
  const currentWmo = weatherData?.current?.weather_code ?? 0;
  const currentIsDay = weatherData?.current?.is_day ?? 1;
  const liveInfo = getWeatherInfo(currentWmo, currentIsDay);
  const activeWeatherTheme = customTheme ? customTheme.theme : liveInfo.theme;
  const activeIsDay = customTheme ? customTheme.isDay : currentIsDay;

  return (
    <main className="relative min-h-screen w-full flex flex-col justify-between overflow-x-hidden p-3 sm:p-6 lg:p-8">
      {/* Dynamic Weather-Adaptive Background Wallpaper & Sky Gradient */}
      <BackgroundAtmosphere weatherTheme={activeWeatherTheme} isDay={activeIsDay} wmoCode={currentWmo} />

      {/* 60 FPS HTML5 Canvas Atmospheric Particle Engine */}
      <WeatherCanvas weatherTheme={activeWeatherTheme} isDay={activeIsDay} />

      <div className="relative z-10 max-w-7xl mx-auto w-full flex flex-col gap-5 sm:gap-6">
        {/* Top Navigation Bar */}
        <header className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-3 sm:p-4 shadow-2xl flex items-center justify-between gap-3 flex-wrap">
          {/* Logo & Brand (Clean, Natural Apple/Google-Grade Typography) */}
          <div className="flex items-center gap-2.5 pl-1 sm:pl-2">
            <div className="w-10 h-10 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center">
              <CloudSun className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-white leading-tight">
                SkyCast
              </h1>
              <p className="text-[11px] font-normal text-white/50 hidden sm:block">
                Live Weather & Forecast
              </p>
            </div>
          </div>

          {/* Autocomplete Search Bar */}
          <div className="flex-1 max-w-md mx-auto order-3 sm:order-2 w-full sm:w-auto">
            <SearchBar onSelectCity={handleSelectCity} />
          </div>

          {/* Actions & Controls */}
          <div className="flex items-center gap-2 sm:gap-2.5 order-2 sm:order-3">
            {/* Locate Button with Live Loading State */}
            <button
              type="button"
              onClick={handleLocateClick}
              disabled={isLocating}
              title="Locate current position"
              className="px-3 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white transition-all flex items-center gap-1.5 text-xs font-medium"
            >
              {isLocating ? (
                <Loader2 className="w-3.5 h-3.5 text-sky-400 animate-spin" />
              ) : (
                <LocateFixed className="w-3.5 h-3.5 text-sky-400" />
              )}
              <span className="hidden sm:inline">Locate</span>
            </button>

            {/* Quick Unit Toggle */}
            <div className="flex items-center p-0.5 rounded-full bg-white/5 border border-white/10">
              <button
                type="button"
                onClick={() => handleToggleTemp('celsius')}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                  tempUnit === 'celsius'
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-white/60 hover:text-white'
                }`}
              >
                °C
              </button>
              <button
                type="button"
                onClick={() => handleToggleTemp('fahrenheit')}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                  tempUnit === 'fahrenheit'
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-white/60 hover:text-white'
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
              className="p-2 sm:p-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white transition-all group"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-sky-400' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
            </button>

            {/* Settings & Themes Button */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              title="Settings & display options"
              className="p-2 sm:p-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white transition-all"
            >
              <Sliders className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="backdrop-blur-xl bg-rose-500/15 border border-rose-500/30 text-rose-200 px-4 py-3 rounded-2xl text-xs sm:text-sm font-medium flex items-center gap-2 shadow-lg animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Custom Theme Indicator (if preview active) */}
        {customTheme && (
          <div className="self-center px-4 py-1.5 rounded-full bg-white/10 border border-white/15 text-white/90 text-xs font-medium flex items-center gap-2 backdrop-blur-md">
            <span>Preview Mode: {customTheme.label}</span>
            <button
              type="button"
              onClick={() => setCustomTheme(null)}
              className="ml-1 text-sky-300 hover:text-white underline text-xs"
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
    </main>
  );
}
