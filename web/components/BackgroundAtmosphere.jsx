'use client';

import React, { useState, useEffect } from 'react';
import { getAtmosphericConfig } from '../lib/weatherCodes';

export default function BackgroundAtmosphere({ weatherTheme = 'clear', isDay = 1, wmoCode = 0 }) {
  const config = getAtmosphericConfig(weatherTheme, isDay, wmoCode);

  const [currentWallpaper, setCurrentWallpaper] = useState(config.wallpaper);
  const [prevWallpaper, setPrevWallpaper] = useState(null);
  const [isCrossFading, setIsCrossFading] = useState(false);

  useEffect(() => {
    if (config.wallpaper !== currentWallpaper) {
      setPrevWallpaper(currentWallpaper);
      setCurrentWallpaper(config.wallpaper);
      setIsCrossFading(true);

      const timer = setTimeout(() => {
        setIsCrossFading(false);
        setPrevWallpaper(null);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [config.wallpaper, currentWallpaper]);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none bg-slate-950">
      {/* Base Dynamic Sky Gradient */}
      <div className={`absolute inset-0 bg-gradient-to-b ${config.skyGradient} transition-colors duration-1000`} />

      {/* Previous Wallpaper (cross-fading out) */}
      {prevWallpaper && (
        <img
          src={prevWallpaper}
          alt=""
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${
            isCrossFading ? 'opacity-0' : 'opacity-100'
          }`}
        />
      )}

      {/* Current Wallpaper (cross-fading in) */}
      <img
        src={currentWallpaper}
        alt=""
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${
          isCrossFading ? 'opacity-100 animate-in fade-in duration-1000' : 'opacity-100'
        }`}
      />

      {/* Atmospheric Contrast & Tint Overlay */}
      <div className={`absolute inset-0 ${config.tint} backdrop-brightness-95 transition-colors duration-1000`} />

      {/* Dynamic Ambient Neon Radial Light Orbs */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top-Left / Sun or Moon Glow */}
        <div
          className={`absolute top-1/6 left-1/4 w-[32rem] h-[32rem] ${config.ambientGlow1} rounded-full blur-[140px] transition-all duration-1000 animate-pulse`}
          style={{ animationDuration: '6s' }}
        />

        {/* Bottom-Right Horizon Ambient Fill */}
        <div
          className={`absolute bottom-1/4 right-1/5 w-[28rem] h-[28rem] ${config.ambientGlow2} rounded-full blur-[130px] transition-all duration-1000`}
        />
      </div>

      {/* Soft Vignette Border */}
      <div className="absolute inset-0 bg-radial-gradient from-transparent via-slate-950/20 to-slate-950/70" />
    </div>
  );
}
