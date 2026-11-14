'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X, Loader2 } from 'lucide-react';

export default function SearchBar({ onSelectCity, onUseMyLocation }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);

  // Debounced autocomplete lookup
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const res = await fetch(
          `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
            trimmed
          )}&count=5&language=en&format=json`
        );
        if (!res.ok) throw new Error('Geocoding failed');
        const data = await res.json();
        setSuggestions(data.results || []);
        setIsOpen(true);
      } catch (err) {
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (item) => {
    onSelectCity({
      name: item.name,
      admin1: item.admin1 || '',
      country: item.country || '',
      latitude: item.latitude,
      longitude: item.longitude
    });
    setQuery('');
    setIsOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'Return' || e.key === 'Enter') {
      if (suggestions.length > 0) {
        handleSelect(suggestions[0]);
      }
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-md">
      <div className="relative flex items-center">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 pointer-events-none" />

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
          placeholder="Search City, Region or Country..."
          className="w-full pl-10 pr-10 py-2 rounded-2xl bg-slate-900/50 border border-white/10 text-white placeholder-slate-400 text-xs sm:text-sm font-medium focus:outline-none focus:border-sky-400/60 focus:ring-2 focus:ring-sky-500/20 backdrop-blur-md transition-all shadow-inner"
        />

        {isLoading ? (
          <Loader2 className="w-4 h-4 text-sky-400 absolute right-3 animate-spin pointer-events-none" />
        ) : query ? (
          <button
            type="button"
            onClick={() => setQuery('')}
            className="absolute right-3 p-0.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : null}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute top-full mt-2 left-0 right-0 z-50 backdrop-blur-2xl bg-slate-950/90 border border-white/15 rounded-2xl shadow-2xl p-1.5 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {suggestions.map((item) => {
            const locText = [item.name, item.admin1, item.country].filter(Boolean).join(', ');
            return (
              <button
                key={`${item.latitude}-${item.longitude}-${item.name}`}
                type="button"
                onClick={() => handleSelect(item)}
                className="w-full text-left px-3.5 py-2.5 rounded-xl hover:bg-sky-500/20 hover:border-sky-500/30 border border-transparent transition-all flex items-center gap-2.5 text-xs sm:text-sm font-medium text-slate-200 hover:text-white group"
              >
                <MapPin className="w-4 h-4 text-sky-400 shrink-0 group-hover:scale-110 transition-transform" />
                <span className="truncate">{locText}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
