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
    { label: 'Clear Day', theme: 'clear', isDay: 1, icon: Sun },
    { label: 'Clear Night', theme: 'clear', isDay: 0, icon: Moon },
    { label: 'Rain Day', theme: 'rain', isDay: 1, icon: CloudRain },
    { label: 'Thunderstorm', theme: 'thunderstorm', isDay: 0, icon: Zap },
    { label: 'Snow Day', theme: 'snow', isDay: 1, icon: Snowflake },
    { label: 'Misty Fog', theme: 'fog', isDay: 1, icon: Cloud },
    { label: 'Drizzle Day', theme: 'rain', isDay: 1, icon: CloudRain },
    { label: 'Overcast Night', theme: 'cloudy', isDay: 0, icon: Cloud }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-black/60 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md backdrop-blur-2xl bg-slate-950/90 border border-white/15 rounded-3xl p-6 shadow-2xl flex flex-col gap-5 text-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold">Settings & Weather Themes</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1. Temperature Unit */}
        <div>
          <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            Temperature Unit
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onToggleTempUnit('celsius')}
              className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                tempUnit === 'celsius'
                  ? 'bg-sky-500 text-white border-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.4)]'
                  : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
              }`}
            >
              °C Celsius
            </button>
            <button
              type="button"
              onClick={() => onToggleTempUnit('fahrenheit')}
              className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                tempUnit === 'fahrenheit'
                  ? 'bg-sky-500 text-white border-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.4)]'
                  : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
              }`}
            >
              °F Fahrenheit
            </button>
          </div>
        </div>

        {/* 2. Wind Unit */}
        <div>
          <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            Wind Speed Unit
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['kmh', 'mph', 'ms'].map((u) => (
              <button
                key={u}
                type="button"
                onClick={() => onSetWindUnit(u)}
                className={`py-1.5 px-2 rounded-xl text-xs font-bold border transition-all ${
                  windUnit === u
                    ? 'bg-sky-500 text-white border-sky-400'
                    : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
                }`}
              >
                {u === 'kmh' ? 'km/h' : (u === 'ms' ? 'm/s' : 'mph')}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Weather Animation Theme Previews */}
        <div>
          <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            60 FPS Atmospheric Animation Previews
          </label>
          <div className="grid grid-cols-2 gap-2">
            {presets.map((p) => {
              const IconComp = p.icon;
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => onApplyThemePreset(p.theme, p.isDay, p.label)}
                  className="py-2 px-3 rounded-xl text-xs font-semibold bg-white/5 hover:bg-sky-500/15 border border-white/10 hover:border-sky-500/30 flex items-center gap-2 text-slate-200 hover:text-white transition-all text-left"
                >
                  <IconComp className="w-4 h-4 text-sky-400 shrink-0" />
                  <span className="truncate">{p.label}</span>
                </button>
              );
            })}
          </div>

          {/* Restore Live Weather */}
          <button
            type="button"
            onClick={onRestoreLiveWeather}
            className={`w-full mt-2.5 py-2 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 border transition-all ${
              !isCustomThemeActive
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>{!isCustomThemeActive ? '✓ Live Weather Active' : '🔄 Restore Live Weather'}</span>
          </button>
        </div>

        {/* 4. Reset & Cache Actions */}
        <div className="pt-2 border-t border-white/10 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={onResetFavorites}
            className="flex-1 py-2 px-3 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-all flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5 text-sky-400" />
            <span>Reset Indian Metros</span>
          </button>

          <button
            type="button"
            onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}
            className="py-2 px-3 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 transition-all flex items-center justify-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Cache</span>
          </button>
        </div>
      </div>
    </div>
  );
}
