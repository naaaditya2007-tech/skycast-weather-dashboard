'use client';

import React from 'react';
import { Droplets, SunMedium, Eye, Wind, Gauge, Activity, Sunrise, Sunset } from 'lucide-react';
import { getAqiCategory, getUvCategory, calculateAqiFromPm25 } from '../lib/weatherCodes';

export default function OverviewGrid({ weatherData, aqiData, windUnit = 'kmh' }) {
  if (!weatherData) return null;

  const current = weatherData.current || {};
  const daily = weatherData.daily || {};

  // 1. Humidity & Dew Point
  const humidity = current.relative_humidity_2m !== undefined ? Math.round(current.relative_humidity_2m) : 68;
  const dewPoint = current.dew_point_2m !== undefined ? Math.round(current.dew_point_2m) : 21;

  // 2. UV Index
  const uvVal = current.uv_index !== undefined ? Number(current.uv_index).toFixed(1) : '4.5';
  const uvCat = getUvCategory(uvVal);
  const uvPercent = Math.min(Math.max((Number(uvVal) / 12) * 100, 5), 100);

  // 3. Visibility
  const visMeters = current.visibility !== undefined ? current.visibility : 10000;
  const visKm = (visMeters / 1000).toFixed(1);
  const visStatus = visMeters >= 10000 ? 'Clear view' : (visMeters >= 5000 ? 'Moderate haze' : 'Dense fog');

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

  // 6. Air Quality (US/Indian 0-500 scale with PM2.5 calculation) & Solar Times
  const usAqi = aqiData?.current?.us_aqi;
  const pm25 = aqiData?.current?.pm2_5;
  const aqiVal = usAqi && usAqi > 0 ? usAqi : (pm25 ? calculateAqiFromPm25(pm25) : 48);
  const aqiInfo = getAqiCategory(aqiVal);
  const sunrise = daily.sunrise?.[0] ? daily.sunrise[0].split('T')[1].slice(0, 5) : '06:05';
  const sunset = daily.sunset?.[0] ? daily.sunset[0].split('T')[1].slice(0, 5) : '17:58';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* 1. Humidity */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>Humidity</span>
          <Droplets className="w-4 h-4 text-sky-400" />
        </div>
        <div className="my-3">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {humidity}<span className="text-base font-normal text-white/60 ml-1">%</span>
          </div>
        </div>
        <div className="text-xs font-normal text-white/70 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Dew Point: {dewPoint}°</span>
          <span className="text-white/50 text-[11px]">{humidity > 70 ? 'Humid' : 'Comfortable'}</span>
        </div>
      </div>

      {/* 2. UV Index */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>UV Index</span>
          <SunMedium className="w-4 h-4 text-amber-400" />
        </div>
        <div className="my-3 flex items-baseline justify-between">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {uvVal}
          </div>
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-white/10 text-white/90 border border-white/10">
            {uvCat.label}
          </span>
        </div>
        <div className="w-full pt-2 border-t border-white/5">
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden relative">
            <div
              className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-400"
              style={{ width: `${uvPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* 3. Visibility */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>Visibility</span>
          <Eye className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="my-3">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {visKm}<span className="text-base font-normal text-white/60 ml-1">km</span>
          </div>
        </div>
        <div className="text-xs font-normal text-white/60 pt-2 border-t border-white/5 truncate">
          {visStatus}
        </div>
      </div>

      {/* 4. Wind Speed & Direction */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>Wind</span>
          <Wind className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="my-3 flex items-baseline gap-1">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {windSpd}
          </div>
          <span className="text-base font-normal text-white/60 ml-1">{windUnitLabel}</span>
        </div>
        <div className="text-xs font-normal text-white/70 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Direction: <strong className="text-white font-medium">{cardinal}</strong> ({windDeg}°)</span>
          <span className="text-white/50 text-[11px]">{windSpd < 15 ? 'Gentle' : 'Breezy'}</span>
        </div>
      </div>

      {/* 5. Pressure & Cloud Cover */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>Pressure</span>
          <Gauge className="w-4 h-4 text-sky-400" />
        </div>
        <div className="my-3">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {pressure}<span className="text-base font-normal text-white/60 ml-1">hPa</span>
          </div>
        </div>
        <div className="text-xs font-normal text-white/70 flex items-center justify-between pt-2 border-t border-white/5">
          <span>Cloud Cover: {cloudCover}%</span>
          <span className="text-white/50 text-[11px]">{pressure >= 1013 ? 'Normal' : 'Low'}</span>
        </div>
      </div>

      {/* 6. Air Quality & Solar Times */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between hover:border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-white/60">
          <span>Air Quality</span>
          <Activity className="w-4 h-4 text-purple-400" />
        </div>
        <div className="my-3 flex items-baseline justify-between">
          <div className="text-3xl font-semibold text-white tracking-tight tabular-nums">
            {aqiVal}<span className="text-base font-normal text-white/60 ml-1">AQI</span>
          </div>
          <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${aqiInfo.badge}`}>
            {aqiInfo.label}
          </span>
        </div>
        <div className="text-xs font-normal text-white/70 flex items-center justify-between pt-2 border-t border-white/5">
          <span className="flex items-center gap-1 text-amber-300/90">
            <Sunrise className="w-3.5 h-3.5" /> {sunrise}
          </span>
          <span className="flex items-center gap-1 text-indigo-300/90">
            <Sunset className="w-3.5 h-3.5" /> {sunset}
          </span>
        </div>
      </div>
    </div>
  );
}
