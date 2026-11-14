'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, Clock, Sparkles } from 'lucide-react';
import { getWeatherInfo } from '../lib/weatherCodes';

export default function HeroCard({ currentCity, weatherData, tempUnit = 'celsius' }) {
  const [localTime, setLocalTime] = useState('');

  const current = weatherData?.current || {};
  const daily = weatherData?.daily || {};
  const tempSym = tempUnit === 'fahrenheit' ? '°F' : '°C';

  const tempVal = current.temperature_2m !== undefined ? Math.round(current.temperature_2m) : 28;
  const apparentVal = current.apparent_temperature !== undefined ? Math.round(current.apparent_temperature) : 31;
  const wmoCode = current.weather_code !== undefined ? current.weather_code : 0;
  const isDay = current.is_day !== undefined ? current.is_day : 1;
  const info = getWeatherInfo(wmoCode, isDay);

  // Live local clock updating every second
  useEffect(() => {
    if (!weatherData) return;
    const offsetSec = weatherData.utc_offset_seconds || 0;

    const updateClock = () => {
      const now = new Date();
      const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
      const targetDate = new Date(utcMs + offsetSec * 1000);
      setLocalTime(
        targetDate.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        })
      );
    };

    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, [weatherData]);

  // Synthesize weather summary
  const windSpd = Math.round(current.wind_speed_10m || 12);
  const precipProb = daily.precipitation_probability_max?.[0] || 0;
  let summary = `Clear skies with light winds (${windSpd} km/h). Enjoy comfortable outdoor weather.`;
  if (precipProb > 50) {
    summary = `Showers expected throughout the day (${precipProb}% rain chance). Keep an umbrella handy.`;
  } else if (windSpd > 25) {
    summary = `Breezy conditions with ${info.label.toLowerCase()} skies and gusts up to ${windSpd} km/h.`;
  } else if (tempVal > 35) {
    summary = `High heat warning with intense sun. Stay hydrated and avoid peak afternoon sun.`;
  }

  const regionString = [currentCity.name, currentCity.admin1, currentCity.country]
    .filter(Boolean)
    .join(', ');

  return (
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-6 sm:p-7 shadow-2xl relative overflow-hidden flex flex-col justify-between group">
      {/* Dynamic Ambient Glow Behind Card */}
      <div className="absolute -top-20 -left-20 w-56 h-56 bg-sky-500/20 rounded-full blur-3xl pointer-events-none group-hover:bg-sky-500/30 transition-all duration-700" />
      <div className="absolute -bottom-20 -right-20 w-56 h-56 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />

      {/* Top Location & Clock Header */}
      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-1.5 text-sky-400 font-semibold text-sm">
            <MapPin className="w-4 h-4" />
            <span className="truncate max-w-[220px] sm:max-w-xs">{currentCity.name || 'Chennai'}</span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 ml-5.5 truncate max-w-[220px] sm:max-w-xs">
            {currentCity.admin1 ? `${currentCity.admin1}, ` : ''}{currentCity.country || 'India'}
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950/40 border border-white/10 text-xs text-slate-300 font-medium">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>{localTime || 'Loading...'}</span>
        </div>
      </div>

      {/* Main Temperature & Condition Block */}
      <div className="my-6 z-10 flex items-baseline gap-4 sm:gap-6 flex-wrap">
        <div className="text-6xl sm:text-7xl font-extrabold tracking-tight text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.5)]">
          {tempVal}<span className="text-sky-400 font-semibold text-4xl sm:text-5xl">{tempSym}</span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="px-3 py-1 rounded-xl bg-sky-500/15 border border-sky-500/30 text-sky-300 text-xs sm:text-sm font-semibold w-max backdrop-blur-md shadow-[0_0_12px_rgba(56,189,248,0.25)]">
            {info.label}
          </span>
          <span className="text-xs font-medium text-slate-300 pl-0.5">
            Feels like <strong className="text-white font-bold">{apparentVal}{tempSym}</strong>
          </span>
        </div>
      </div>

      {/* Dynamic Summary Sentence */}
      <div className="z-10 pt-3 border-t border-white/10 flex items-start gap-2">
        <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5 animate-pulse" />
        <p className="text-xs sm:text-[13px] text-slate-200 leading-relaxed font-medium">
          {summary}
        </p>
      </div>
    </div>
  );
}
