'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Check, X, MapPin } from 'lucide-react';
import { getWeatherInfo } from '../lib/weatherCodes';

export default function OtherCitiesSidebar({
  currentCity,
  onSelectCity,
  favorites,
  onAddFavorite,
  onRemoveFavorite,
  tempUnit = 'celsius'
}) {
  const [citiesData, setCitiesData] = useState([]);
  const [loading, setLoading] = useState(false);
  const tempSym = tempUnit === 'fahrenheit' ? '°F' : '°C';

  const isCurrentFav = favorites.some(
    (f) => f.name.toLowerCase() === (currentCity.name || '').toLowerCase()
  );

  // Fetch live weather for all favorite cities
  useEffect(() => {
    if (!favorites.length) {
      setCitiesData([]);
      return;
    }

    let isMounted = true;
    setLoading(true);

    const fetchAllFavs = async () => {
      try {
        const promises = favorites.map(async (fav) => {
          try {
            const tempParam = tempUnit === 'fahrenheit' ? '&temperature_unit=fahrenheit' : '';
            const res = await fetch(
              `https://api.open-meteo.com/v1/forecast?latitude=${fav.latitude}&longitude=${fav.longitude}&current=temperature_2m,weather_code,is_day${tempParam}&timezone=auto`
            );
            if (!res.ok) throw new Error('Failed to fetch');
            const data = await res.json();
            const curr = data.current || {};
            const info = getWeatherInfo(curr.weather_code, curr.is_day);
            return {
              ...fav,
              temp: curr.temperature_2m !== undefined ? Math.round(curr.temperature_2m) : null,
              condition: info.label,
              icon: info.icon
            };
          } catch (e) {
            return {
              ...fav,
              temp: null,
              condition: 'Unavailable'
            };
          }
        });

        const results = await Promise.all(promises);
        if (isMounted) {
          setCitiesData(results);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) setLoading(false);
      }
    };

    fetchAllFavs();

    return () => {
      isMounted = false;
    };
  }, [favorites, tempUnit]);

  return (
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 sm:p-6 shadow-2xl flex flex-col justify-between h-full overflow-hidden">
      {/* Sidebar Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-white/10">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wider text-white/60">Other Cities</h3>
          <p className="text-[11px] text-white/40 mt-0.5">Quick Switch & Favorites</p>
        </div>

        <button
          type="button"
          onClick={() => (isCurrentFav ? onRemoveFavorite(currentCity.name) : onAddFavorite(currentCity))}
          className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all shadow-sm ${
            isCurrentFav
              ? 'bg-white/10 text-white/90 border border-white/20 hover:bg-white/15'
              : 'bg-sky-500 text-white hover:bg-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.3)]'
          }`}
        >
          {isCurrentFav ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Saved</span>
            </>
          ) : (
            <>
              <Plus className="w-3.5 h-3.5" />
              <span>+ Add Fav</span>
            </>
          )}
        </button>
      </div>

      {/* Stacked Cards with guaranteed right padding & clipping fix */}
      <div className="my-4 flex flex-col gap-2.5 flex-1 overflow-y-auto no-scrollbar max-h-[500px] pr-0.5">
        {citiesData.map((city, idx) => {
          const isSelected = (city.name || '').toLowerCase() === (currentCity.name || '').toLowerCase();

          return (
            <div
              key={city.name || idx}
              onClick={() => onSelectCity(city)}
              className={`px-4 py-3 rounded-2xl border transition-all duration-200 cursor-pointer flex items-center justify-between relative group ${
                isSelected
                  ? 'bg-white/15 border-white/30 shadow-[0_0_15px_rgba(255,255,255,0.1)]'
                  : 'bg-white/[0.03] border-white/5 hover:bg-white/[0.08] hover:border-white/20'
              }`}
            >
              <div className="flex flex-col gap-0.5 min-w-0 pr-3">
                <span className="text-[11px] font-normal text-white/50 truncate">
                  {city.admin1 ? `${city.admin1}, ` : ''}{city.country || 'India'}
                </span>
                <span className="text-sm font-semibold text-white truncate">
                  {city.name}
                </span>
                <span className="text-xs font-normal text-white/70 truncate">
                  {city.condition || 'Clear'}
                </span>
              </div>

              {/* Right Side: Temperature + Clear Delete Button (Never Clipped) */}
              <div className="flex items-center gap-3 shrink-0 pl-1">
                {city.temp !== null && (
                  <span className="text-xl font-light text-white tabular-nums tracking-tight">
                    {city.temp}<span className="text-sm font-normal text-white/60 ml-0.5">{tempSym}</span>
                  </span>
                )}

                <button
                  type="button"
                  title={`Remove ${city.name}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFavorite(city.name);
                  }}
                  className="w-6 h-6 rounded-lg text-white/40 hover:text-rose-400 hover:bg-rose-500/20 transition-all flex items-center justify-center shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}

        {!citiesData.length && !loading && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-white/40 gap-2">
            <MapPin className="w-8 h-8 text-white/20" />
            <p className="text-xs">No favorite cities pinned.</p>
            <p className="text-[11px] text-white/40">Click &apos;+ Add Fav&apos; to pin current location.</p>
          </div>
        )}
      </div>

      <div className="pt-2 text-center text-[11px] text-white/40 border-t border-white/5">
        Click any city to switch view
      </div>
    </div>
  );
}
