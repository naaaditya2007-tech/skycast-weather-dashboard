'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X, Loader2 } from 'lucide-react';

export default function SearchBar({ onSelectCity }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const wrapperRef = useRef(null);

  // Debounced autocomplete lookup (300ms)
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      setHasSearched(false);
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
        setHasSearched(true);
        setIsOpen(true);
      } catch (err) {
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside to dismiss
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
    setSuggestions([]);
    setIsOpen(false);
  };

  const handleKeyDown = async (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'Return' || e.key === 'Enter') {
      if (suggestions.length > 0) {
        handleSelect(suggestions[0]);
      } else if (query.trim().length >= 2) {
        setIsLoading(true);
        try {
          const res = await fetch(
            `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
              query.trim()
            )}&count=1&language=en&format=json`
          );
          if (res.ok) {
            const data = await res.json();
            if (data.results && data.results.length > 0) {
              handleSelect(data.results[0]);
            } else {
              setHasSearched(true);
              setIsOpen(true);
            }
          }
        } catch (err) {
          // Ignore
        } finally {
          setIsLoading(false);
        }
      }
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-md">
      <div className="relative flex items-center">
        <Search className="w-4 h-4 text-white/40 absolute left-3.5 pointer-events-none" />

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
          placeholder="Search City, Region or Country..."
          className="w-full pl-10 pr-10 py-2 rounded-full bg-white/5 border border-white/10 text-white placeholder-white/40 text-xs sm:text-sm font-normal focus:outline-none focus:border-white/30 focus:bg-white/10 backdrop-blur-md transition-all"
        />

        {isLoading ? (
          <Loader2 className="w-4 h-4 text-white/60 absolute right-3.5 animate-spin pointer-events-none" />
        ) : query ? (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setSuggestions([]);
              setIsOpen(false);
            }}
            className="absolute right-3.5 p-0.5 rounded-full hover:bg-white/10 text-white/40 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : null}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="absolute top-full mt-2 left-0 right-0 z-50 backdrop-blur-2xl bg-slate-950/95 border border-white/15 rounded-2xl shadow-2xl p-1.5 overflow-hidden animate-in fade-in duration-150">
          {suggestions.length > 0 ? (
            suggestions.map((item) => {
              const locText = [item.name, item.admin1, item.country].filter(Boolean).join(', ');
              return (
                <button
                  key={`${item.latitude}-${item.longitude}-${item.name}`}
                  type="button"
                  onClick={() => handleSelect(item)}
                  className="w-full text-left px-3.5 py-2.5 rounded-xl hover:bg-white/10 border border-transparent transition-all flex items-center gap-2.5 text-xs sm:text-sm font-normal text-white/90 hover:text-white group"
                >
                  <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span className="truncate">{locText}</span>
                </button>
              );
            })
          ) : hasSearched && !isLoading ? (
            <div className="px-4 py-3 text-xs text-white/40 text-center font-normal">
              No matching cities found
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
