/**
 * SkyCast Shared Weather Engine for the Web Client.
 * Handles WMO weather code mapping, day/night variations, and theme classes.
 */

const WMO_CODES = {
  0: { condition: "Clear Sky", dayDesc: "Sunny and clear", nightDesc: "Clear skies", theme: "sunny", icon: "☀️", nightIcon: "🌙", animation: "sunbeam" },
  1: { condition: "Mainly Clear", dayDesc: "Mostly sunny", nightDesc: "Mostly clear", theme: "partly-cloudy", icon: "🌤️", nightIcon: "🌕", animation: "clouds" },
  2: { condition: "Partly Cloudy", dayDesc: "Partly cloudy", nightDesc: "Partly cloudy", theme: "partly-cloudy", icon: "⛅", nightIcon: "☁️", animation: "clouds" },
  3: { condition: "Overcast", dayDesc: "Cloudy skies", nightDesc: "Overcast", theme: "cloudy", icon: "☁️", nightIcon: "☁️", animation: "clouds" },
  45: { condition: "Fog", dayDesc: "Foggy conditions", nightDesc: "Dense fog", theme: "fog", icon: "🌫️", nightIcon: "🌫️", animation: "fog" },
  48: { condition: "Depositing Rime Fog", dayDesc: "Freezing fog", nightDesc: "Freezing fog", theme: "fog", icon: "🌫️", nightIcon: "🌫️", animation: "fog" },
  51: { condition: "Light Drizzle", dayDesc: "Light drizzling rain", nightDesc: "Light drizzle", theme: "rainy", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  53: { condition: "Moderate Drizzle", dayDesc: "Drizzling rain", nightDesc: "Steady drizzle", theme: "rainy", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  55: { condition: "Dense Drizzle", dayDesc: "Heavy drizzle", nightDesc: "Dense drizzle", theme: "rainy", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  61: { condition: "Slight Rain", dayDesc: "Light rain", nightDesc: "Light rain showers", theme: "rainy", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  63: { condition: "Moderate Rain", dayDesc: "Moderate rain", nightDesc: "Steady rain", theme: "rainy", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  65: { condition: "Heavy Rain", dayDesc: "Heavy downpour", nightDesc: "Torrential rain", theme: "rainy", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  71: { condition: "Slight Snow Fall", dayDesc: "Light flurries", nightDesc: "Light snow flurries", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  73: { condition: "Moderate Snow Fall", dayDesc: "Moderate snowfall", nightDesc: "Steady snow", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  75: { condition: "Heavy Snow Fall", dayDesc: "Heavy snowstorm", nightDesc: "Blizzard snow", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  77: { condition: "Snow Grains", dayDesc: "Snow grains", nightDesc: "Snow grains", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  80: { condition: "Slight Rain Showers", dayDesc: "Passing rain showers", nightDesc: "Night showers", theme: "rainy", icon: "🌦️", nightIcon: "🌧️", animation: "rain" },
  81: { condition: "Moderate Rain Showers", dayDesc: "Scattered showers", nightDesc: "Rain showers", theme: "rainy", icon: "🌧️", nightIcon: "🌧️", animation: "rain" },
  82: { condition: "Violent Rain Showers", dayDesc: "Violent downpours", nightDesc: "Violent showers", theme: "rainy", icon: "⛈️", nightIcon: "⛈️", animation: "rain" },
  85: { condition: "Slight Snow Showers", dayDesc: "Scattered snow showers", nightDesc: "Snow showers", theme: "snow", icon: "🌨️", nightIcon: "🌨️", animation: "snow" },
  86: { condition: "Heavy Snow Showers", dayDesc: "Heavy snow showers", nightDesc: "Heavy snow showers", theme: "snow", icon: "❄️", nightIcon: "❄️", animation: "snow" },
  95: { condition: "Thunderstorm", dayDesc: "Thunderstorms with lightning", nightDesc: "Night thunderstorms", theme: "thunderstorm", icon: "⚡", nightIcon: "🌩️", animation: "thunderstorm" },
  96: { condition: "Thunderstorm with Slight Hail", dayDesc: "Thunderstorm & hail", nightDesc: "Thunderstorm & hail", theme: "thunderstorm", icon: "⛈️", nightIcon: "⛈️", animation: "thunderstorm" },
  99: { condition: "Thunderstorm with Heavy Hail", dayDesc: "Severe thunderstorm with hail", nightDesc: "Severe thunderstorm & hail", theme: "thunderstorm", icon: "⛈️", nightIcon: "⛈️", animation: "thunderstorm" }
};

const DEFAULT_ENTRY = {
  condition: "Atmospheric",
  dayDesc: "Live conditions reported",
  nightDesc: "Live conditions reported",
  theme: "partly-cloudy",
  icon: "🌤️",
  nightIcon: "🌙",
  animation: "clouds"
};

export function getWeatherInfo(code, isDay = 1) {
  const item = WMO_CODES[code] || DEFAULT_ENTRY;
  const isDayBool = Boolean(isDay);
  const desc = isDayBool ? item.dayDesc : item.nightDesc;
  const icon = isDayBool ? item.icon : item.nightIcon;
  const timeSuffix = isDayBool ? "day" : "night";
  const themeClass = `theme-${item.theme}-${timeSuffix}`;

  return {
    code,
    condition: item.condition,
    description: desc,
    icon,
    animation: item.animation,
    themeClass,
    isDay: isDayBool
  };
}
