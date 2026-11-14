'use client';

import React from 'react';
import { X, Sliders, RotateCcw, Trash2, Sun, Moon, CloudRain, Zap, Snowflake, Cloud, Sparkles } from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
  tempUnit,
  onToggleTempUnit,
  windUnit,
  onSetWindUnit,
  onApplyThemePreset,
  onRestoreLiveWeather,
  onResetFavorites,
  isCustomThemeActive
}) {
  if (!isOpen) return null;

  const presets = [
    { label: 'Sunny Day', theme: 'clear', isDay: 1, icon: Sun },
    { label: 'Clear Night', theme: 'clear', isDay: 0, icon: Moon },
    { label: 'Cloudy Sky', theme: 'cloudy', isDay: 1, icon: Cloud },
    { label: 'Rainy Day', theme: 'rain', isDay: 1, icon: CloudRain },
    { label: 'Thunderstorm', theme: 'thunderstorm', isDay: 0, icon: Zap },
    { label: 'Snow Day', theme: 'snow', isDay: 1, icon: Snowflake },
    { label: 'Misty Fog', theme: 'fog', isDay: 1, icon: Cloud },
    { label: 'Overcast Night', theme: 'cloudy', isDay: 0, icon: Moon }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-black/60 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md backdrop-blur-2xl bg-slate-950/90 border border-white/15 rounded-3xl p-6 shadow-2xl flex flex-col gap-5 text-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold tracking-normal text-white">Settings & Display</h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full hover:bg-white/10 text-white/60 hover:text-white transition-colors flex items-center justify-center"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1. Temperature Unit */}
        <div>
          <label className="text-xs font-medium uppercase tracking-wider text-white/60 block mb-2">
            Temperature Unit
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onToggleTempUnit('celsius')}
              className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                tempUnit === 'celsius'
                  ? 'bg-sky-500 text-white border-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.3)]'
                  : 'bg-white/5 text-white/70 border-white/10 hover:bg-white/10 hover:text-white'
              }`}
            >
              °C Celsius
            </button>
            <button
              type="button"
              onClick={() => onToggleTempUnit('fahrenheit')}
              className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                tempUnit === 'fahrenheit'
                  ? 'bg-sky-500 text-white border-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.3)]'
                  : 'bg-white/5 text-white/70 border-white/10 hover:bg-white/10 hover:text-white'
              }`}
            >
              °F Fahrenheit
            </button>
          </div>
        </div>

        {/* 2. Wind Speed Unit */}
        <div>
          <label className="text-xs font-medium uppercase tracking-wider text-white/60 block mb-2">
            Wind Speed Unit
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['kmh', 'mph', 'ms'].map((u) => (
              <button
                key={u}
                type="button"
                onClick={() => onSetWindUnit(u)}
                className={`py-1.5 px-2 rounded-xl text-xs font-medium border transition-all ${
                  windUnit === u
                    ? 'bg-sky-500 text-white border-sky-400'
                    : 'bg-white/5 text-white/70 border-white/10 hover:bg-white/10 hover:text-white'
                }`}
              >
                {u === 'kmh' ? 'km/h' : (u === 'ms' ? 'm/s' : 'mph')}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Live Animated Weather Preview */}
        <div>
          <label className="text-xs font-medium uppercase tracking-wider text-white/60 block mb-2">
            Weather Animation Previews
          </label>
          <div className="grid grid-cols-2 gap-2">
            {presets.map((p) => {
              const IconComp = p.icon;
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => onApplyThemePreset(p.theme, p.isDay, p.label)}
                  className="py-2 px-3 rounded-xl text-xs font-normal bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 flex items-center gap-2 text-white/80 hover:text-white transition-all text-left"
                >
                  <IconComp className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span className="truncate">{p.label}</span>
                </button>
              );
            })}
          </div>

          {/* Auto Live Weather Button */}
          <button
            type="button"
            onClick={onRestoreLiveWeather}
            className={`w-full mt-2.5 py-2 px-4 rounded-xl text-xs font-medium flex items-center justify-center gap-2 border transition-all ${
              !isCustomThemeActive
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{!isCustomThemeActive ? '✓ Auto Live Weather' : 'Restore Auto Live Weather'}</span>
          </button>
        </div>

        {/* 4. Reset & Cache Actions */}
        <div className="pt-2 border-t border-white/10 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={onResetFavorites}
            className="flex-1 py-2 px-3 rounded-xl text-xs font-normal bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white transition-all flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5 text-white/50" />
            <span>Reset Favorites</span>
          </button>

          <button
            type="button"
            onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}
            className="py-2 px-3 rounded-xl text-xs font-normal bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 transition-all flex items-center justify-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Cache</span>
          </button>
        </div>
      </div>
    </div>
  );
}
