'use client';

import React, { useState } from 'react';
import { getWeatherInfo } from '../lib/weatherCodes';
import { CloudRain, Sun, Moon, Cloud, Zap, Snowflake } from 'lucide-react';

function WeatherIcon({ name, className = "w-6 h-6" }) {
  switch (name) {
    case 'sun':
      return <Sun className={`${className} text-amber-400`} />;
    case 'moon':
      return <Moon className={`${className} text-cyan-200`} />;
    case 'partly':
      return (
        <div className="relative inline-flex items-center justify-center">
          <Sun className="w-3.5 h-3.5 text-amber-400 absolute -top-1 -right-1" />
          <Cloud className={`${className} text-white/80`} />
        </div>
      );
    case 'partly_night':
      return (
        <div className="relative inline-flex items-center justify-center">
          <Moon className="w-3 h-3 text-cyan-200 absolute -top-1 -right-1" />
          <Cloud className={`${className} text-white/70`} />
        </div>
      );
    case 'rain':
    case 'drizzle':
      return <CloudRain className={`${className} text-sky-400`} />;
    case 'thunder':
      return <Zap className={`${className} text-amber-300`} />;
    case 'snow':
      return <Snowflake className={`${className} text-sky-100`} />;
    default:
      return <Cloud className={`${className} text-white/80`} />;
  }
}

export default function ForecastCard({ weatherData, tempUnit = 'celsius' }) {
  const [activeTab, setActiveTab] = useState('Today'); // 'Today', 'Week', '16 Days'
  const [hoverIndex, setHoverIndex] = useState(null);

  if (!weatherData) return null;

  const hourly = weatherData.hourly || {};
  const daily = weatherData.daily || {};
  const tempSym = tempUnit === 'fahrenheit' ? '°F' : '°C';

  // Extract 24-hour timeline
  const hourlyTimes = (hourly.time || []).slice(0, 24);
  const hourlyTemps = (hourly.temperature_2m || []).slice(0, 24);
  const hourlyWmo = (hourly.weather_code || []).slice(0, 24);
  const hourlyRains = (hourly.precipitation_probability || []).slice(0, 24);
  const hourlyIsDay = (hourly.is_day || []).slice(0, 24);

  // Parse sunrise/sunset hour for accurate Day/Night icon validation
  const sunriseHour = daily.sunrise?.[0] ? parseInt(daily.sunrise[0].split('T')[1].slice(0, 2), 10) : 6;
  const sunsetHour = daily.sunset?.[0] ? parseInt(daily.sunset[0].split('T')[1].slice(0, 2), 10) : 18;

  // Compute SVG Spline Path for 24h temperature
  const minTemp = hourlyTemps.length ? Math.min(...hourlyTemps) - 1 : 0;
  const maxTemp = hourlyTemps.length ? Math.max(...hourlyTemps) + 1 : 40;
  const rangeTemp = Math.max(maxTemp - minTemp, 1);

  const chartW = 580;
  const chartH = 88;
  const paddingX = 28;
  const paddingY = 16;
  const usableW = chartW - paddingX * 2;
  const usableH = chartH - paddingY * 2;

  const points = hourlyTemps.map((temp, i) => {
    const x = paddingX + (i / Math.max(hourlyTemps.length - 1, 1)) * usableW;
    const y = paddingY + usableH - ((temp - minTemp) / rangeTemp) * usableH;
    return { x, y, temp, time: hourlyTimes[i] };
  });

  // Generate smooth cubic bezier SVG path
  let pathD = '';
  if (points.length > 0) {
    pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? i : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2] || p2;

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      pathD += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
  }

  const areaD = pathD && points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${chartH} L ${points[0].x} ${chartH} Z`
    : '';

  // Max and Min points
  const maxPoint = points.reduce((prev, curr) => (curr.temp > prev.temp ? curr : prev), points[0] || {});
  const minPoint = points.reduce((prev, curr) => (curr.temp < prev.temp ? curr : prev), points[0] || {});

  // Daily cards slice for Week (7) vs 16 Days (16)
  const dailyCount = activeTab === 'Week' ? 7 : (activeTab === '16 Days' ? 16 : 0);
  const dailyTimes = (daily.time || []).slice(0, dailyCount);
  const dailyMaxs = (daily.temperature_2m_max || []).slice(0, dailyCount);
  const dailyMins = (daily.temperature_2m_min || []).slice(0, dailyCount);
  const dailyWmos = (daily.weather_code || []).slice(0, dailyCount);
  const dailyRains = (daily.precipitation_probability_max || []).slice(0, dailyCount);

  // Global min/max across displayed days for proportional range bars
  const overallMin = dailyMins.length ? Math.min(...dailyMins) : 15;
  const overallMax = dailyMaxs.length ? Math.max(...dailyMaxs) : 35;
  const overallRange = Math.max(overallMax - overallMin, 1);

  return (
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 sm:p-6 shadow-2xl flex flex-col justify-between relative overflow-hidden transition-all duration-300">
      {/* Tabs Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-white/10">
        <div className="flex items-center gap-1.5 p-1 rounded-full bg-white/5 border border-white/10">
          {['Today', 'Week', '16 Days'].map((tab) => {
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-3.5 py-1 rounded-full text-xs font-medium tracking-normal transition-all duration-200 ${
                  isActive
                    ? 'bg-sky-500 text-white shadow-[0_0_12px_rgba(14,165,233,0.3)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab}
              </button>
            );
          })}
        </div>
        <span className="text-xs font-normal text-white/50 hidden sm:inline-block">
          {activeTab === 'Today' ? '24-Hour Timeline' : `${dailyCount}-Day Extended Forecast`}
        </span>
      </div>

      {/* TODAY TAB: 24-Hour Scrollable Row with Night Moon Icons */}
      {activeTab === 'Today' && (
        <div className="my-4 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-2.5 min-w-max pb-1">
            {hourlyTimes.map((t, i) => {
              const dt = new Date(t);
              const hour = dt.getHours();
              const hourLabel = i === 0 ? 'Now' : `${hour.toString().padStart(2, '0')}:00`;

              // Check if hour is nighttime: between sunset and sunrise
              const isNightHour = hour < sunriseHour || hour >= sunsetHour;
              const isD = isNightHour ? 0 : (hourlyIsDay[i] !== undefined ? hourlyIsDay[i] : 1);
              const info = getWeatherInfo(hourlyWmo[i], isD);
              const rainProb = hourlyRains[i] || 0;
              const tempVal = Math.round(hourlyTemps[i]);

              return (
                <div
                  key={t}
                  className="w-20 p-2.5 rounded-2xl bg-white/[0.03] border border-white/5 flex flex-col items-center gap-1.5 hover:bg-white/[0.08] hover:border-white/20 transition-all cursor-pointer group"
                  onMouseEnter={() => setHoverIndex(i)}
                  onMouseLeave={() => setHoverIndex(null)}
                >
                  <span className="text-[11px] font-normal text-white/60">{hourLabel}</span>
                  <WeatherIcon name={info.icon} className="w-5 h-5 my-0.5" />
                  <span className="text-xs font-semibold text-white tabular-nums">
                    {tempVal}{tempSym}
                  </span>
                  {rainProb > 0 ? (
                    <span className="text-[10px] font-normal text-sky-400 flex items-center gap-0.5">
                      <CloudRain className="w-2.5 h-2.5" /> {rainProb}%
                    </span>
                  ) : (
                    <span className="text-[10px] text-white/30">—</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TODAY TAB: Interactive 24-Hour Spline Chart */}
      {activeTab === 'Today' && (
        <div className="pt-2 border-t border-white/5 relative">
          <div className="flex items-center justify-between text-xs font-normal text-white/50 mb-1 px-1">
            <span>24h Temperature Curve</span>
            {hoverIndex !== null && points[hoverIndex] && (
              <span className="text-sky-300 font-medium">
                {new Date(points[hoverIndex].time).toLocaleTimeString([], { hour: 'numeric' })}: {Math.round(points[hoverIndex].temp)}{tempSym}
              </span>
            )}
          </div>

          <div className="relative w-full h-[88px]">
            <svg
              viewBox={`0 0 ${chartW} ${chartH}`}
              className="w-full h-full overflow-visible"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {areaD && <path d={areaD} fill="url(#curveGradient)" />}

              <line
                x1={paddingX}
                y1={chartH - 8}
                x2={chartW - paddingX}
                y2={chartH - 8}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />

              {pathD && (
                <path
                  d={pathD}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              )}

              {maxPoint && (
                <g>
                  <circle cx={maxPoint.x} cy={maxPoint.y} r="3" fill="#fbbf24" stroke="#ffffff" strokeWidth="1" />
                  <text x={maxPoint.x} y={maxPoint.y - 6} fill="#fbbf24" fontSize="10" fontWeight="500" textAnchor="middle">
                    High {Math.round(maxPoint.temp)}{tempSym}
                  </text>
                </g>
              )}

              {minPoint && (
                <g>
                  <circle cx={minPoint.x} cy={minPoint.y} r="3" fill="#38bdf8" stroke="#ffffff" strokeWidth="1" />
                  <text x={minPoint.x} y={minPoint.y + 13} fill="#38bdf8" fontSize="10" fontWeight="500" textAnchor="middle">
                    Low {Math.round(minPoint.temp)}{tempSym}
                  </text>
                </g>
              )}

              {points.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={hoverIndex === idx ? "4" : "2"}
                  fill={hoverIndex === idx ? "#38bdf8" : "transparent"}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHoverIndex(idx)}
                  onMouseLeave={() => setHoverIndex(null)}
                />
              ))}
            </svg>
          </div>
        </div>
      )}

      {/* WEEK & 16 DAYS TABS: Daily Forecast View with Range Bars */}
      {(activeTab === 'Week' || activeTab === '16 Days') && (
        <div className="my-2 flex flex-col gap-2 max-h-[220px] overflow-y-auto no-scrollbar pr-1">
          {dailyTimes.map((t, i) => {
            const dt = new Date(t);
            const dayLabel = i === 0 ? 'Today' : dt.toLocaleDateString('en-US', { weekday: 'short' });
            const dateStr = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const info = getWeatherInfo(dailyWmos[i], 1);
            const rainProb = dailyRains[i] || 0;
            const maxT = Math.round(dailyMaxs[i]);
            const minT = Math.round(dailyMins[i]);

            // Calculate percentage bar width and left offset
            const leftPct = Math.max(0, ((minT - overallMin) / overallRange) * 100);
            const widthPct = Math.max(8, ((maxT - minT) / overallRange) * 100);

            return (
              <div
                key={t}
                className="px-3 py-2 rounded-xl bg-white/[0.03] border border-white/5 flex items-center justify-between gap-3 text-xs"
              >
                <div className="w-24 shrink-0 flex flex-col">
                  <span className="font-medium text-white">{dayLabel}</span>
                  <span className="text-[10px] text-white/40">{dateStr}</span>
                </div>

                <div className="flex items-center gap-2 w-32 shrink-0">
                  <WeatherIcon name={info.icon} className="w-4 h-4 shrink-0" />
                  <span className="truncate text-white/70 text-[11px]">{info.label}</span>
                </div>

                <div className="w-12 text-right shrink-0">
                  {rainProb > 0 ? (
                    <span className="text-[11px] text-sky-400 font-normal">
                      {rainProb}%
                    </span>
                  ) : (
                    <span className="text-[11px] text-white/30">—</span>
                  )}
                </div>

                {/* Min / Max Range Bar */}
                <div className="flex-1 flex items-center gap-2 max-w-xs">
                  <span className="w-6 text-right tabular-nums text-white/60 text-xs font-normal">
                    {minT}°
                  </span>
                  <div className="flex-1 h-1.5 rounded-full bg-white/10 relative overflow-hidden">
                    <div
                      className="absolute h-full rounded-full bg-gradient-to-r from-sky-400 to-amber-300"
                      style={{
                        left: `${leftPct}%`,
                        width: `${Math.min(widthPct, 100 - leftPct)}%`
                      }}
                    />
                  </div>
                  <span className="w-6 text-left tabular-nums text-white text-xs font-medium">
                    {maxT}°
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
