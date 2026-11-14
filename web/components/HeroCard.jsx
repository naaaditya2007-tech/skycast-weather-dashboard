'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, Clock } from 'lucide-react';
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

  // Live local clock updating with city's UTC offset
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

  // Clean, natural weather summary
  const windSpd = Math.round(current.wind_speed_10m || 12);
  const precipProb = daily.precipitation_probability_max?.[0] || 0;
  let summary = `Clear skies with light winds at ${windSpd} km/h. Great conditions for outdoor activities.`;
  if (precipProb > 50) {
    summary = `Showers likely today (${precipProb}% chance of rain). Consider keeping an umbrella nearby.`;
  } else if (windSpd > 25) {
    summary = `Breezy conditions with ${info.label.toLowerCase()} skies and wind gusts around ${windSpd} km/h.`;
  } else if (tempVal > 34) {
    summary = `Warm day ahead. Stay hydrated and avoid prolonged exposure during peak sunlight.`;
  }

  return (
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-6 sm:p-7 shadow-2xl relative overflow-hidden flex flex-col justify-between group">
      {/* Soft Ambient Glow Behind Card */}
      <div className="absolute -top-20 -left-20 w-56 h-56 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-20 -right-20 w-56 h-56 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Location & Local Clock Header */}
      <div className="flex items-start justify-between z-10 gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-sky-400 font-medium text-sm">
            <MapPin className="w-4 h-4 shrink-0" />
            <span className="truncate text-base font-semibold text-white">
              {currentCity.name || 'Chennai'}
            </span>
          </div>
          <p className="text-xs text-white/60 mt-0.5 pl-5.5 truncate">
            {currentCity.admin1 ? `${currentCity.admin1}, ` : ''}{currentCity.country || 'India'}
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-white/80 font-normal shrink-0">
          <Clock className="w-3.5 h-3.5 text-white/60" />
          <span className="tabular-nums">{localTime || '—:—'}</span>
        </div>
      </div>

      {/* Main Temperature & Condition Block (Natural Apple/Google Typography) */}
      <div className="my-6 z-10 flex items-baseline gap-4 sm:gap-6 flex-wrap">
        <div className="text-7xl sm:text-8xl font-light tracking-tighter text-white tabular-nums">
          {tempVal}<span className="text-4xl sm:text-5xl font-light text-white/70 ml-1">{tempSym}</span>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="px-3 py-1 rounded-full bg-white/10 border border-white/15 text-white/90 text-xs sm:text-sm font-medium w-max backdrop-blur-md">
            {info.label}
          </span>
          <span className="text-xs font-normal text-white/60 pl-0.5">
            Feels like <span className="text-white/90 font-medium tabular-nums">{apparentVal}{tempSym}</span>
          </span>
        </div>
      </div>

      {/* Clean Dynamic Summary Sentence */}
      <div className="z-10 pt-3 border-t border-white/10">
        <p className="text-xs text-white/70 leading-relaxed font-normal">
          {summary}
        </p>
      </div>
    </div>
  );
}
