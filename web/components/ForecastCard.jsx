'use client';

import React, { useState } from 'react';
import { getWeatherInfo } from '../lib/weatherCodes';
import { CloudRain, Sun, Moon, Cloud, Zap, Snowflake, Wind } from 'lucide-react';

function WeatherIcon({ name, className = "w-6 h-6" }) {
  switch (name) {
    case 'sun':
      return <Sun className={`${className} text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]`} />;
    case 'moon':
      return <Moon className={`${className} text-cyan-200 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]`} />;
    case 'partly':
      return (
        <div className="relative inline-flex items-center justify-center">
          <Sun className="w-4 h-4 text-amber-400 absolute -top-1 -right-1" />
          <Cloud className={`${className} text-slate-200`} />
        </div>
      );
    case 'partly_night':
      return (
        <div className="relative inline-flex items-center justify-center">
          <Moon className="w-3.5 h-3.5 text-cyan-300 absolute -top-1 -right-1" />
          <Cloud className={`${className} text-slate-300`} />
        </div>
      );
    case 'rain':
    case 'drizzle':
      return <CloudRain className={`${className} text-sky-400 drop-shadow-[0_0_6px_rgba(56,189,248,0.4)]`} />;
    case 'thunder':
      return <Zap className={`${className} text-amber-300 drop-shadow-[0_0_8px_rgba(252,211,77,0.7)]`} />;
    case 'snow':
      return <Snowflake className={`${className} text-sky-100 drop-shadow-[0_0_6px_rgba(240,249,255,0.6)]`} />;
    default:
      return <Cloud className={`${className} text-slate-300`} />;
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

  // Compute SVG Spline Path for 24h temperature
  const minTemp = hourlyTemps.length ? Math.min(...hourlyTemps) - 1 : 0;
  const maxTemp = hourlyTemps.length ? Math.max(...hourlyTemps) + 1 : 40;
  const rangeTemp = Math.max(maxTemp - minTemp, 1);

  const chartW = 580;
  const chartH = 90;
  const paddingX = 24;
  const paddingY = 16;
  const usableW = chartW - paddingX * 2;
  const usableH = chartH - paddingY * 2;

  const points = hourlyTemps.map((temp, i) => {
    const x = paddingX + (i / (hourlyTemps.length - 1)) * usableW;
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

  const areaD = pathD
    ? `${pathD} L ${points[points.length - 1].x} ${chartH} L ${points[0].x} ${chartH} Z`
    : '';

  // Max and Min points
  const maxPoint = points.reduce((prev, curr) => (curr.temp > prev.temp ? curr : prev), points[0] || {});
  const minPoint = points.reduce((prev, curr) => (curr.temp < prev.temp ? curr : prev), points[0] || {});

  // Daily cards slice
  const dailyCount = activeTab === 'Week' ? 7 : (activeTab === '16 Days' ? 16 : 0);
  const dailyTimes = (daily.time || []).slice(0, dailyCount);
  const dailyMaxs = (daily.temperature_2m_max || []).slice(0, dailyCount);
  const dailyMins = (daily.temperature_2m_min || []).slice(0, dailyCount);
  const dailyWmos = (daily.weather_code || []).slice(0, dailyCount);
  const dailyRains = (daily.precipitation_probability_max || []).slice(0, dailyCount);

  return (
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 shadow-2xl flex flex-col justify-between relative overflow-hidden transition-all duration-300">
      {/* Tabs Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/5">
        <div className="flex items-center gap-2 p-1 rounded-2xl bg-slate-950/40 border border-white/5">
          {['Today', 'Week', '16 Days'].map((tab) => {
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 ${
                  isActive
                    ? 'bg-sky-500 text-white shadow-[0_0_15px_rgba(14,165,233,0.5)]'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab}
              </button>
            );
          })}
        </div>
        <span className="text-xs font-medium text-slate-400 hidden sm:inline-block">
          {activeTab === 'Today' ? '24h Timeline' : `${dailyCount}-Day Forecast`}
        </span>
      </div>

      {/* Hourly / Daily Mini Cards */}
      <div className="my-4 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-2.5 min-w-max pb-1">
          {activeTab === 'Today' &&
            hourlyTimes.slice(0, 10).map((t, i) => {
              const dt = new Date(t);
              const hour = dt.getHours();
              const hourLabel = i === 0 ? 'Now' : `${hour.toString().padStart(2, '0')}:00`;
              const isNightHour = hour < 6 || hour >= 18;
              const isD = isNightHour ? 0 : (hourlyIsDay[i] !== undefined ? hourlyIsDay[i] : 1);
              const info = getWeatherInfo(hourlyWmo[i], isD);
              const rainProb = hourlyRains[i] || 0;
              const tempVal = Math.round(hourlyTemps[i]);

              return (
                <div
                  key={t}
                  className="w-20 p-2.5 rounded-2xl bg-white/[0.03] border border-white/5 flex flex-col items-center gap-1.5 hover:bg-white/[0.08] hover:border-sky-500/30 transition-all cursor-pointer group"
                  onMouseEnter={() => setHoverIndex(i)}
                  onMouseLeave={() => setHoverIndex(null)}
                >
                  <span className="text-[11px] font-semibold text-slate-300">{hourLabel}</span>
                  <WeatherIcon name={info.icon} className="w-6 h-6 my-0.5" />
                  <span className="text-xs font-bold text-white group-hover:text-sky-300 transition-colors">
                    {tempVal}{tempSym}
                  </span>
                  {rainProb > 0 ? (
                    <span className="text-[10px] font-medium text-sky-400 flex items-center gap-0.5">
                      <CloudRain className="w-2.5 h-2.5" /> {rainProb}%
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">--</span>
                  )}
                </div>
              );
            })}

          {(activeTab === 'Week' || activeTab === '16 Days') &&
            dailyTimes.map((t, i) => {
              const dt = new Date(t);
              const dayLabel = i === 0 ? 'Today' : dt.toLocaleDateString('en-US', { weekday: 'short' });
              const info = getWeatherInfo(dailyWmos[i], 1);
              const rainProb = dailyRains[i] || 0;
              const maxT = Math.round(dailyMaxs[i]);
              const minT = Math.round(dailyMins[i]);

              return (
                <div
                  key={t}
                  className="w-24 p-2.5 rounded-2xl bg-white/[0.03] border border-white/5 flex flex-col items-center gap-1.5 hover:bg-white/[0.08] hover:border-sky-500/30 transition-all"
                >
                  <span className="text-[11px] font-semibold text-slate-300">{dayLabel}</span>
                  <WeatherIcon name={info.icon} className="w-6 h-6 my-0.5" />
                  <div className="flex items-center gap-1 text-xs">
                    <span className="font-bold text-white">{maxT}°</span>
                    <span className="font-medium text-slate-400">{minT}°</span>
                  </div>
                  {rainProb > 0 ? (
                    <span className="text-[10px] font-medium text-sky-400 flex items-center gap-0.5">
                      <CloudRain className="w-2.5 h-2.5" /> {rainProb}%
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">0%</span>
                  )}
                </div>
              );
            })}
        </div>
      </div>

      {/* Interactive 24-Hour Spline Chart (Rendered when 'Today' tab is active) */}
      {activeTab === 'Today' && (
        <div className="pt-2 border-t border-white/5 relative">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 mb-1 px-1">
            <span>24h Temperature Curve</span>
            {hoverIndex !== null && points[hoverIndex] && (
              <span className="text-sky-300 animate-pulse">
                {new Date(points[hoverIndex].time).toLocaleTimeString([], { hour: 'numeric' })}: {Math.round(points[hoverIndex].temp)}{tempSym}
              </span>
            )}
          </div>

          <div className="relative w-full h-[95px]">
            <svg
              viewBox={`0 0 ${chartW} ${chartH}`}
              className="w-full h-full overflow-visible"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Area Under Curve */}
              {areaD && <path d={areaD} fill="url(#curveGradient)" />}

              {/* Baseline Grid */}
              <line x1={paddingX} y1={chartH - 8} x2={chartW - paddingX} y2={chartH - 8} stroke="rgba(255,255,255,0.08)" strokeWidth="1" strokeDasharray="3 3" />

              {/* Spline Path */}
              {pathD && (
                <path
                  d={pathD}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  className="filter drop-shadow-[0_0_8px_rgba(56,189,248,0.7)]"
                />
              )}

              {/* Max Temp Pin */}
              {maxPoint && (
                <g>
                  <circle cx={maxPoint.x} cy={maxPoint.y} r="3.5" fill="#fbbf24" stroke="#ffffff" strokeWidth="1.5" />
                  <text x={maxPoint.x} y={maxPoint.y - 7} fill="#fbbf24" fontSize="10" fontWeight="bold" textAnchor="middle">
                    High {Math.round(maxPoint.temp)}{tempSym}
                  </text>
                </g>
              )}

              {/* Min Temp Pin */}
              {minPoint && (
                <g>
                  <circle cx={minPoint.x} cy={minPoint.y} r="3.5" fill="#38bdf8" stroke="#ffffff" strokeWidth="1.5" />
                  <text x={minPoint.x} y={minPoint.y + 14} fill="#38bdf8" fontSize="10" fontWeight="bold" textAnchor="middle">
                    Low {Math.round(minPoint.temp)}{tempSym}
                  </text>
                </g>
              )}

              {/* Interactive Hover Nodes */}
              {points.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={hoverIndex === idx ? "5" : "3"}
                  fill={hoverIndex === idx ? "#38bdf8" : "transparent"}
                  className="cursor-pointer transition-all hover:stroke-white hover:stroke-2"
                  onMouseEnter={() => setHoverIndex(idx)}
                  onMouseLeave={() => setHoverIndex(null)}
                />
              ))}
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}
