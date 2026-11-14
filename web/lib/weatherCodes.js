/**
 * SkyCast Weather Codes & Atmospheric Palette Mapper
 * Standard WMO weather interpretation codes to icons, descriptions, and dynamic palettes
 */

export const WMO_MAP = {
  0: { label: "Clear Sky", iconDay: "sun", iconNight: "moon", theme: "clear" },
  1: { label: "Mainly Clear", iconDay: "partly", iconNight: "partly_night", theme: "clear" },
  2: { label: "Partly Cloudy", iconDay: "partly", iconNight: "partly_night", theme: "cloudy" },
  3: { label: "Overcast", iconDay: "cloud", iconNight: "cloud", theme: "cloudy" },
  45: { label: "Fog", iconDay: "fog", iconNight: "fog", theme: "fog" },
  48: { label: "Depositing Rime Fog", iconDay: "fog", iconNight: "fog", theme: "fog" },
  51: { label: "Light Drizzle", iconDay: "drizzle", iconNight: "drizzle", theme: "rain" },
  53: { label: "Moderate Drizzle", iconDay: "drizzle", iconNight: "drizzle", theme: "rain" },
  55: { label: "Dense Drizzle", iconDay: "drizzle", iconNight: "drizzle", theme: "rain" },
  56: { label: "Freezing Drizzle", iconDay: "snow", iconNight: "snow", theme: "snow" },
  57: { label: "Dense Freezing Drizzle", iconDay: "snow", iconNight: "snow", theme: "snow" },
  61: { label: "Slight Rain", iconDay: "rain", iconNight: "rain", theme: "rain" },
  63: { label: "Moderate Rain", iconDay: "rain", iconNight: "rain", theme: "rain" },
  65: { label: "Heavy Rain", iconDay: "rain", iconNight: "rain", theme: "rain" },
  66: { label: "Freezing Rain", iconDay: "snow", iconNight: "snow", theme: "snow" },
  67: { label: "Heavy Freezing Rain", iconDay: "snow", iconNight: "snow", theme: "snow" },
  71: { label: "Slight Snow", iconDay: "snow", iconNight: "snow", theme: "snow" },
  73: { label: "Moderate Snow", iconDay: "snow", iconNight: "snow", theme: "snow" },
  75: { label: "Heavy Snow", iconDay: "snow", iconNight: "snow", theme: "snow" },
  77: { label: "Snow Grains", iconDay: "snow", iconNight: "snow", theme: "snow" },
  80: { label: "Slight Rain Showers", iconDay: "rain", iconNight: "rain", theme: "rain" },
  81: { label: "Moderate Rain Showers", iconDay: "rain", iconNight: "rain", theme: "rain" },
  82: { label: "Violent Rain Showers", iconDay: "rain", iconNight: "rain", theme: "rain" },
  85: { label: "Slight Snow Showers", iconDay: "snow", iconNight: "snow", theme: "snow" },
  86: { label: "Heavy Snow Showers", iconDay: "snow", iconNight: "snow", theme: "snow" },
  95: { label: "Thunderstorm", iconDay: "thunder", iconNight: "thunder", theme: "thunderstorm" },
  96: { label: "Thunderstorm with Slight Hail", iconDay: "thunder", iconNight: "thunder", theme: "thunderstorm" },
  99: { label: "Thunderstorm with Heavy Hail", iconDay: "thunder", iconNight: "thunder", theme: "thunderstorm" },
};

export function getWeatherInfo(wmoCode, isDay = 1) {
  const item = WMO_MAP[wmoCode] || { label: "Cloudy", iconDay: "cloud", iconNight: "cloud", theme: "cloudy" };
  const icon = isDay ? item.iconDay : item.iconNight;
  return {
    label: item.label,
    icon,
    theme: item.theme
  };
}

export function calculateAqiFromPm25(pm25) {
  const c = Math.max(0, Number(pm25) || 0);
  const breakpoints = [
    { cLow: 0.0, cHigh: 12.0, iLow: 0, iHigh: 50 },
    { cLow: 12.1, cHigh: 35.4, iLow: 51, iHigh: 100 },
    { cLow: 35.5, cHigh: 55.4, iLow: 101, iHigh: 150 },
    { cLow: 55.5, cHigh: 150.4, iLow: 151, iHigh: 200 },
    { cLow: 150.5, cHigh: 250.4, iLow: 201, iHigh: 300 },
    { cLow: 250.5, cHigh: 350.4, iLow: 301, iHigh: 400 },
    { cLow: 350.5, cHigh: 500.4, iLow: 401, iHigh: 500 }
  ];

  for (const b of breakpoints) {
    if (c >= b.cLow && c <= b.cHigh) {
      return Math.round(((b.iHigh - b.iLow) / (b.cHigh - b.cLow)) * (c - b.cLow) + b.iLow);
    }
  }

  if (c > 500.4) return 500;
  return Math.round(c * 3.5);
}

export function getAqiCategory(aqi) {
  const val = Number(aqi) || 0;
  if (val <= 50) return { label: "Good", color: "#10b981", badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" };
  if (val <= 100) return { label: "Moderate", color: "#f59e0b", badge: "bg-amber-500/20 text-amber-300 border-amber-500/30" };
  if (val <= 150) return { label: "Unhealthy for Sensitive", color: "#f97316", badge: "bg-orange-500/20 text-orange-300 border-orange-500/30" };
  if (val <= 200) return { label: "Unhealthy", color: "#ef4444", badge: "bg-rose-500/20 text-rose-300 border-rose-500/30" };
  if (val <= 300) return { label: "Very Unhealthy", color: "#a855f7", badge: "bg-purple-500/20 text-purple-300 border-purple-500/30" };
  return { label: "Hazardous", color: "#ec4899", badge: "bg-pink-500/20 text-pink-300 border-pink-500/30" };
}

export function getUvCategory(uv) {
  const val = Number(uv) || 0;
  if (val < 3) return { label: "Low", color: "#10b981" };
  if (val < 6) return { label: "Moderate", color: "#f59e0b" };
  if (val < 8) return { label: "Very High", color: "#ef4444" };
  return { label: "Extreme", color: "#a855f7" };
}

export function getAtmosphericConfig(theme = 'clear', isDay = 1, wmoCode = 0) {
  if (!isDay) {
    if (theme === 'rain' || theme === 'thunderstorm') {
      return {
        wallpaper: '/backgrounds/rain_night.jpg',
        skyGradient: 'from-slate-950 via-indigo-950/60 to-black',
        ambientGlow1: 'bg-indigo-600/20',
        ambientGlow2: 'bg-purple-600/20',
        tint: 'bg-slate-950/70',
        label: theme === 'thunderstorm' ? 'Thunderstorm Night' : 'Rainy Night'
      };
    }
    if (theme === 'snow') {
      return {
        wallpaper: '/backgrounds/snow.jpg',
        skyGradient: 'from-slate-950 via-sky-950/50 to-black',
        ambientGlow1: 'bg-sky-500/20',
        ambientGlow2: 'bg-indigo-500/20',
        tint: 'bg-slate-950/75',
        label: 'Snow Night'
      };
    }
    return {
      wallpaper: '/backgrounds/clear_night.jpg',
      skyGradient: 'from-[#030712] via-[#090d16] to-[#02040a]',
      ambientGlow1: 'bg-indigo-500/20',
      ambientGlow2: 'bg-violet-600/20',
      tint: 'bg-slate-950/65',
      label: 'Clear Night'
    };
  }

  switch (theme) {
    case 'thunderstorm':
      return {
        wallpaper: '/backgrounds/rain_night.jpg',
        skyGradient: 'from-purple-950/80 via-slate-950/90 to-black',
        ambientGlow1: 'bg-violet-500/25',
        ambientGlow2: 'bg-fuchsia-600/20',
        tint: 'bg-slate-950/70',
        label: 'Thunderstorm'
      };
    case 'rain':
      return {
        wallpaper: '/backgrounds/rain_night.jpg',
        skyGradient: 'from-slate-900/90 via-sky-950/80 to-slate-950',
        ambientGlow1: 'bg-cyan-500/20',
        ambientGlow2: 'bg-blue-600/20',
        tint: 'bg-slate-950/65',
        label: 'Rain'
      };
    case 'snow':
      return {
        wallpaper: '/backgrounds/snow.jpg',
        skyGradient: 'from-slate-800/80 via-sky-950/70 to-slate-950',
        ambientGlow1: 'bg-sky-300/20',
        ambientGlow2: 'bg-cyan-400/20',
        tint: 'bg-slate-950/60',
        label: 'Snow'
      };
    case 'fog':
      return {
        wallpaper: '/backgrounds/fog.jpg',
        skyGradient: 'from-slate-800/85 via-zinc-900/85 to-slate-950',
        ambientGlow1: 'bg-slate-400/20',
        ambientGlow2: 'bg-zinc-500/20',
        tint: 'bg-slate-950/65',
        label: 'Fog'
      };
    case 'cloudy':
      if (wmoCode === 3) {
        return {
          wallpaper: '/backgrounds/cloudy.jpg',
          skyGradient: 'from-slate-800/85 via-slate-900/85 to-slate-950',
          ambientGlow1: 'bg-sky-600/20',
          ambientGlow2: 'bg-slate-500/20',
          tint: 'bg-slate-950/60',
          label: 'Overcast'
        };
      }
      return {
        wallpaper: '/backgrounds/partly_cloudy.jpg',
        skyGradient: 'from-sky-900/70 via-slate-900/80 to-slate-950',
        ambientGlow1: 'bg-sky-400/25',
        ambientGlow2: 'bg-indigo-500/20',
        tint: 'bg-slate-950/55',
        label: 'Partly Cloudy'
      };
    case 'clear':
    default:
      return {
        wallpaper: '/backgrounds/clear_day.jpg',
        skyGradient: 'from-sky-800/70 via-slate-900/80 to-slate-950',
        ambientGlow1: 'bg-sky-400/30',
        ambientGlow2: 'bg-amber-400/25',
        tint: 'bg-slate-950/50',
        label: 'Clear Day'
      };
  }
}

export const DEFAULT_INDIAN_FAVORITES = [
  { name: "Bengaluru", country: "India", admin1: "Karnataka", latitude: 12.9716, longitude: 77.5946 },
  { name: "Mumbai", country: "India", admin1: "Maharashtra", latitude: 19.0760, longitude: 72.8777 },
  { name: "New Delhi", country: "India", admin1: "Delhi", latitude: 28.6139, longitude: 77.2090 },
  { name: "Hyderabad", country: "India", admin1: "Telangana", latitude: 17.3850, longitude: 78.4867 },
  { name: "Kolkata", country: "India", admin1: "West Bengal", latitude: 22.5726, longitude: 88.3639 }
];
