'use client';

import React from 'react';
import { Droplets, SunMedium, Eye, Wind, Gauge, Activity, Sunrise, Sunset } from 'lucide-react';
import { getAqiCategory, getUvCategory } from '../lib/weatherCodes';

export default function OverviewGrid({ weatherData, aqiData, windUnit = 'kmh' }) {
  if (!weatherData) return null;

  const current = weatherData.current || {};
  const daily = weatherData.daily || {};

  // 1. Humidity & Dew Point
  const humidity = current.relative_humidity_2m !== undefined ? Math.round(current.relative_humidity_2m) : 68;
  const dewPoint = current.dew_point_2m !== undefined ? Math.round(current.dew_point_2m) : 21;

  // 2. UV Index
  const uvVal = current.uv_index !== undefined ? Number(current.uv_index).toFixed(1) : 4.5;
  const uvCat = getUvCategory(uvVal);
  const uvPercent = Math.min(Math.max((Number(uvVal) / 12) * 100, 5), 100);

  // 3. Visibility
  const visMeters = current.visibility !== undefined ? current.visibility : 10000;
  const visKm = (visMeters / 1000).toFixed(1);
  const visStatus = visMeters >= 10000 ? 'Clear & unobstructed' : (visMeters >= 5000 ? 'Moderate haze' : 'Dense fog');

  // 4. Wind
  const windSpd = current.wind_speed_10m !== undefined ? Math.round(current.wind_speed_10m) : 14;
  const windDeg = current.wind_direction_10m !== undefined ? current.wind_direction_10m : 45;
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const dirIndex = Math.round(windDeg / 45) % 8;
  const cardinal = directions[dirIndex];
  const windUnitLabel = windUnit === 'mph' ? 'mph' : (windUnit === 'ms' ? 'm/s' : 'km/h');

  // 5. Pressure & Cloud Cover
  const pressure = current.surface_pressure !== undefined ? Math.round(current.surface_pressure) : 1013;
  const cloudCover = current.cloud_cover !== undefined ? current.cloud_cover : 35;

  // 6. Air Quality & Solar Times
  const aqiVal = aqiData?.current?.european_aqi || aqiData?.current?.us_aqi || 42;
  const aqiInfo = getAqiCategory(aqiVal);
  const sunrise = daily.sunrise?.[0] ? daily.sunrise[0].split('T')[1].slice(0, 5) : '06:05';
  const sunset = daily.sunset?.[0] ? daily.sunset[0].split('T')[1].slice(0, 5) : '17:58';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* 1. Humidity */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-sky-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>Humidity</span>
          <Droplets className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="my-2">
          <div className="text-3xl font-extrabold text-white tracking-tight">{humidity}%</div>
        </div>
        <div className="text-xs font-medium text-sky-300 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Dew Point: {dewPoint}°</span>
          <span className="text-slate-400 text-[11px]">{humidity > 70 ? 'Humid air' : 'Comfortable'}</span>
        </div>
      </div>

      {/* 2. UV Index with Vertical / Horizontal Thermometer Bar */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-amber-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>UV Index</span>
          <SunMedium className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="my-2 flex items-baseline justify-between">
          <div className="text-3xl font-extrabold text-white tracking-tight">{uvVal}</div>
          <span className="text-xs font-bold px-2 py-0.5 rounded-lg bg-amber-400/10 text-amber-300 border border-amber-400/20">
            {uvCat.label}
          </span>
        </div>
        {/* Gradient Progress Bar */}
        <div className="w-full pt-2 border-t border-white/5">
          <div className="w-full h-2 rounded-full bg-slate-950/60 overflow-hidden relative border border-white/5">
            <div
              className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500"
              style={{ width: `${uvPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* 3. Visibility */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-emerald-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>Visibility</span>
          <Eye className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="my-2">
          <div className="text-3xl font-extrabold text-white tracking-tight">{visKm} <span className="text-lg font-semibold text-slate-400">km</span></div>
        </div>
        <div className="text-xs font-medium text-slate-300 pt-2 border-t border-white/5 truncate">
          {visStatus}
        </div>
      </div>

      {/* 4. Wind Speed & Direction */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-cyan-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>Wind</span>
          <div className="relative w-5 h-5 flex items-center justify-center">
            <Wind className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <div className="text-3xl font-extrabold text-white tracking-tight">{windSpd}</div>
          <span className="text-sm font-semibold text-slate-400">{windUnitLabel}</span>
        </div>
        <div className="text-xs font-medium text-slate-300 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Direction: <strong className="text-white">{cardinal}</strong> ({windDeg}°)</span>
          <span className="text-slate-400 text-[11px]">{windSpd < 15 ? 'Gentle' : 'Breezy'}</span>
        </div>
      </div>

      {/* 5. Pressure & Cloud Cover */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-sky-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>Pressure</span>
          <Gauge className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="my-2">
          <div className="text-3xl font-extrabold text-white tracking-tight">{pressure} <span className="text-lg font-semibold text-slate-400">hPa</span></div>
        </div>
        <div className="text-xs font-medium text-sky-300 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Cloud Cover: {cloudCover}%</span>
          <span className="text-slate-400 text-[11px]">{pressure >= 1013 ? 'High pressure' : 'Low pressure'}</span>
        </div>
      </div>

      {/* 6. Air Quality & Solar Times */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-purple-500/30 transition-all duration-300 group">
        <div className="flex items-center justify-between text-slate-300 text-xs font-semibold">
          <span>Air Quality</span>
          <Activity className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="my-2 flex items-baseline justify-between">
          <div className="text-3xl font-extrabold text-white tracking-tight">{aqiVal} <span className="text-sm font-semibold text-slate-400">AQI</span></div>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-lg border ${aqiInfo.badge}`}>
            {aqiInfo.label}
          </span>
        </div>
        <div className="text-xs font-medium text-slate-300 flex items-center justify-between pt-2 border-t border-white/5">
          <span className="flex items-center gap-1 text-amber-300">
            <Sunrise className="w-3.5 h-3.5" /> {sunrise}
          </span>
          <span className="flex items-center gap-1 text-indigo-300">
            <Sunset className="w-3.5 h-3.5" /> {sunset}
          </span>
        </div>
      </div>
    </div>
  );
}
