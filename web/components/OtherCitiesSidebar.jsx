'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Check, Trash2, MapPin } from 'lucide-react';
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

  // Fetch weather for all favourite cities
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
    <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-3xl p-5 sm:p-6 shadow-2xl flex flex-col justify-between h-full">
      {/* Sidebar Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-white/10">
        <div>
          <h3 className="text-base font-bold text-white tracking-wide">Other Cities</h3>
          <p className="text-[11px] text-slate-400">Pinned Indian Metros & Favourites</p>
        </div>

        <button
          type="button"
          onClick={() => (isCurrentFav ? onRemoveFavorite(currentCity.name) : onAddFavorite(currentCity))}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md ${
            isCurrentFav
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30'
              : 'bg-sky-500 text-white hover:bg-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.4)]'
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

      {/* Stacked Cards */}
      <div className="my-4 flex flex-col gap-2.5 flex-1 overflow-y-auto no-scrollbar max-h-[500px]">
        {citiesData.map((city, idx) => {
          const isSelected = (city.name || '').toLowerCase() === (currentCity.name || '').toLowerCase();

          return (
            <div
              key={city.name || idx}
              onClick={() => onSelectCity(city)}
              className={`p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer flex items-center justify-between relative group ${
                isSelected
                  ? 'bg-sky-500/15 border-sky-400/40 shadow-[0_0_15px_rgba(56,189,248,0.2)]'
                  : 'bg-white/[0.03] border-white/5 hover:bg-white/[0.07] hover:border-white/20'
              }`}
            >
              <div className="flex flex-col gap-0.5 truncate pr-2">
                <span className="text-[11px] font-medium text-slate-400 truncate">
                  {city.admin1 ? `${city.admin1}, ` : ''}{city.country || 'India'}
                </span>
                <span className="text-sm font-bold text-white group-hover:text-sky-300 transition-colors truncate">
                  {city.name}
                </span>
                <span className="text-xs font-semibold text-sky-400 truncate">
                  {city.condition || 'Clear'}
                </span>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                {city.temp !== null && (
                  <span className="text-xl font-extrabold text-white">
                    {city.temp}{tempSym}
                  </span>
                )}

                <button
                  type="button"
                  title="Remove city"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFavorite(city.name);
                  }}
                  className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors opacity-70 group-hover:opacity-100"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}

        {!citiesData.length && !loading && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-slate-400 gap-2">
            <MapPin className="w-8 h-8 text-slate-600" />
            <p className="text-xs">No favourite cities pinned yet.</p>
            <p className="text-[11px] text-slate-500">Click &apos;+ Add Fav&apos; above to save the current city.</p>
          </div>
        )}
      </div>

      <div className="pt-2 text-center text-[11px] text-slate-500 border-t border-white/5">
        Click any card to switch cities instantly
      </div>
    </div>
  );
}
