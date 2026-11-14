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

export const DEFAULT_INDIAN_FAVORITES = [
  { name: "Bengaluru", country: "India", admin1: "Karnataka", latitude: 12.9716, longitude: 77.5946 },
  { name: "Mumbai", country: "India", admin1: "Maharashtra", latitude: 19.0760, longitude: 72.8777 },
  { name: "New Delhi", country: "India", admin1: "Delhi", latitude: 28.6139, longitude: 77.2090 },
  { name: "Hyderabad", country: "India", admin1: "Telangana", latitude: 17.3850, longitude: 78.4867 },
  { name: "Kolkata", country: "India", admin1: "West Bengal", latitude: 22.5726, longitude: 88.3639 }
];
