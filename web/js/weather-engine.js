/**
 * SkyCast Shared Weather Engine — JavaScript Client Edition
 * ---------------------------------------------------------
 * Matches `shared/weather_codes.py` identically:
 * - WMO Weather Codes (0, 1-3, 45/48, 51-57, 61-67, 71-77, 80-82, 85-86, 95-99)
 * - Condition names, day/night descriptions & icons
 * - Theme keys (clear, cloudy, fog, drizzle, rain, snow, thunderstorm)
 * - Particle animations (sunbeam, clouds, rain, snow, thunderstorm)
 * - European AQI scale & WHO UV Index scales
 */

export const WMO_CODES = {
  0: { condition: "Clear Sky", dayDesc: "Sunny and clear", nightDesc: "Clear skies", theme: "clear", icon: "☀️", nightIcon: "🌙", animation: "sunbeam" },
  1: { condition: "Mainly Clear", dayDesc: "Mostly sunny", nightDesc: "Mostly clear", theme: "cloudy", icon: "🌤️", nightIcon: "🌕", animation: "clouds" },
  2: { condition: "Partly Cloudy", dayDesc: "Partly cloudy", nightDesc: "Partly cloudy", theme: "cloudy", icon: "⛅", nightIcon: "☁️", animation: "clouds" },
  3: { condition: "Overcast", dayDesc: "Overcast skies", nightDesc: "Overcast", theme: "cloudy", icon: "☁️", nightIcon: "☁️", animation: "clouds" },
  45: { condition: "Fog", dayDesc: "Foggy conditions", nightDesc: "Dense fog", theme: "fog", icon: "🌫️", nightIcon: "🌫️", animation: "clouds" },
  48: { condition: "Depositing Rime Fog", dayDesc: "Freezing rime fog", nightDesc: "Freezing rime fog", theme: "fog", icon: "🌫️", nightIcon: "🌫️", animation: "clouds" },
  51: { condition: "Light Drizzle", dayDesc: "Light patchy drizzle", nightDesc: "Light drizzle", theme: "drizzle", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  53: { condition: "Moderate Drizzle", dayDesc: "Moderate drizzle", nightDesc: "Moderate drizzle", theme: "drizzle", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  55: { condition: "Dense Drizzle", dayDesc: "Dense drizzle", nightDesc: "Heavy drizzle", theme: "drizzle", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  56: { condition: "Light Freezing Drizzle", dayDesc: "Freezing drizzle", nightDesc: "Freezing drizzle", theme: "drizzle", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  57: { condition: "Dense Freezing Drizzle", dayDesc: "Heavy freezing drizzle", nightDesc: "Heavy freezing drizzle", theme: "drizzle", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  61: { condition: "Slight Rain", dayDesc: "Light rain", nightDesc: "Light rain", theme: "rain", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  63: { condition: "Moderate Rain", dayDesc: "Moderate steady rain", nightDesc: "Steady rain", theme: "rain", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  65: { condition: "Heavy Rain", dayDesc: "Heavy downpour", nightDesc: "Heavy downpour", theme: "rain", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  66: { condition: "Light Freezing Rain", dayDesc: "Light freezing rain", nightDesc: "Light freezing rain", theme: "rain", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  67: { condition: "Heavy Freezing Rain", dayDesc: "Heavy freezing rain", nightDesc: "Heavy freezing rain", theme: "rain", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  71: { condition: "Slight Snow Fall", dayDesc: "Light snow flurries", nightDesc: "Light snow flurries", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  73: { condition: "Moderate Snow Fall", dayDesc: "Moderate snowfall", nightDesc: "Moderate snowfall", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  75: { condition: "Heavy Snow Fall", dayDesc: "Heavy snowstorm", nightDesc: "Heavy snowstorm", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  77: { condition: "Snow Grains", dayDesc: "Snow grains", nightDesc: "Snow grains", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  80: { condition: "Slight Rain Showers", dayDesc: "Passing rain showers", nightDesc: "Passing night showers", theme: "rain", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  81: { condition: "Moderate Rain Showers", dayDesc: "Moderate rain showers", nightDesc: "Moderate showers", theme: "rain", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  82: { condition: "Violent Rain Showers", dayDesc: "Torrential rain showers", nightDesc: "Torrential showers", theme: "rain", icon: "⛈️", nightIcon: "⛈️", animation: "rain" },
  85: { condition: "Slight Snow Showers", dayDesc: "Scattered snow showers", nightDesc: "Scattered snow showers", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  86: { condition: "Heavy Snow Showers", dayDesc: "Heavy snow showers", nightDesc: "Heavy snow showers", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  95: { condition: "Thunderstorm", dayDesc: "Thunderstorms with lightning", nightDesc: "Night thunderstorms", theme: "thunderstorm", icon: "⚡", nightIcon: "🌩️", animation: "thunderstorm" },
  96: { condition: "Thunderstorm with Slight Hail", dayDesc: "Thunderstorm with hail", nightDesc: "Thunderstorm with hail", theme: "thunderstorm", icon: "⛈️", nightIcon: "⛈️", animation: "thunderstorm" },
  99: { condition: "Thunderstorm with Heavy Hail", dayDesc: "Severe thunderstorm and hail", nightDesc: "Severe thunderstorm and hail", theme: "thunderstorm", icon: "⛈️", nightIcon: "⛈️", animation: "thunderstorm" }
};

const DEFAULT_WEATHER = {
  condition: "Partly Cloudy",
  dayDesc: "Scattered cloud cover",
  nightDesc: "Partly cloudy",
  theme: "cloudy",
  icon: "🌤️",
  nightIcon: "🌙",
  animation: "clouds"
};

export function getWeatherInfo(code, isDay = 1) {
  const item = WMO_CODES[code] || DEFAULT_WEATHER;
  const isDayBool = Boolean(isDay);
  const desc = isDayBool ? item.dayDesc : item.nightDesc;
  const icon = isDayBool ? item.icon : item.nightIcon;
  const timeSuffix = isDayBool ? "day" : "night";
  const themeClass = `theme-${item.theme}-${timeSuffix}`;

  return {
    code,
    condition: item.condition,
    description: desc,
    theme: item.theme,
    themeClass,
    isDay: isDayBool,
    icon,
    animation: item.animation
  };
}

export function getAqiLevel(val) {
  const num = Math.round(Number(val) || 0);
  if (num <= 20) return { val: num, label: "Good", color: "#10B981" };
  if (num <= 40) return { val: num, label: "Fair", color: "#FBBF24" };
  if (num <= 60) return { val: num, label: "Moderate", color: "#F97316" };
  if (num <= 80) return { val: num, label: "Poor", color: "#EF4444" };
  if (num <= 100) return { val: num, label: "Very Poor", color: "#A855F7" };
  return { val: num, label: "Extremely Poor", color: "#881337" };
}

export function getUvLevel(val) {
  const num = Math.round((Number(val) || 0) * 10) / 10;
  if (num <= 2.9) return { val: num, label: "Low", color: "#10B981" };
  if (num <= 5.9) return { val: num, label: "Moderate", color: "#FBBF24" };
  if (num <= 7.9) return { val: num, label: "High", color: "#F97316" };
  if (num <= 10.9) return { val: num, label: "Very High", color: "#EF4444" };
  return { val: num, label: "Extreme", color: "#A855F7" };
}
