/**
 * SkyCast Resilient Geolocation Resolver
 * Chain: Browser GPS (4s) -> BigDataCloud Reverse Geocoding -> IP Geolocation -> Chennai Default
 */

export const CHENNAI_DEFAULT = {
  name: 'Chennai',
  admin1: 'Tamil Nadu',
  country: 'India',
  latitude: 13.0827,
  longitude: 80.2707
};

export async function reverseGeocode(lat, lon) {
  try {
    const res = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`,
      { signal: AbortSignal.timeout ? AbortSignal.timeout(4000) : undefined }
    );
    if (res.ok) {
      const data = await res.json();
      const city = data.city || data.locality || data.principalSubdivision || 'Current Location';
      const admin1 = data.principalSubdivision || '';
      const country = data.countryName || '';
      return {
        name: city,
        admin1,
        country,
        latitude: lat,
        longitude: lon
      };
    }
  } catch (e) {
    // Fall back to Open-Meteo reverse search if BigDataCloud is slow or unavailable
  }

  try {
    const res = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${lat.toFixed(2)},${lon.toFixed(2)}&count=1&language=en&format=json`,
      { signal: AbortSignal.timeout ? AbortSignal.timeout(3000) : undefined }
    );
    if (res.ok) {
      const data = await res.json();
      const first = data.results?.[0];
      if (first) {
        return {
          name: first.name || 'Current Location',
          admin1: first.admin1 || '',
          country: first.country || '',
          latitude: lat,
          longitude: lon
        };
      }
    }
  } catch (e) {
    // Ignore
  }

  return {
    name: 'Current Location',
    admin1: '',
    country: '',
    latitude: lat,
    longitude: lon
  };
}

export async function detectLocationByIP() {
  // Try ipwho.is first (reliable, CORS-friendly, zero key)
  try {
    const res = await fetch('https://ipwho.is/', {
      signal: AbortSignal.timeout ? AbortSignal.timeout(3500) : undefined
    });
    if (res.ok) {
      const data = await res.json();
      if (data.success && data.latitude && data.longitude) {
        return {
          name: data.city || 'Detected Location',
          admin1: data.region || '',
          country: data.country || '',
          latitude: data.latitude,
          longitude: data.longitude
        };
      }
    }
  } catch (e) {
    // Fall back to ipapi.co
  }

  try {
    const res = await fetch('https://ipapi.co/json/', {
      signal: AbortSignal.timeout ? AbortSignal.timeout(3500) : undefined
    });
    if (res.ok) {
      const data = await res.json();
      if (data.latitude && data.longitude) {
        return {
          name: data.city || 'Detected Location',
          admin1: data.region || '',
          country: data.country_name || '',
          latitude: data.latitude,
          longitude: data.longitude
        };
      }
    }
  } catch (e) {
    // Fallback to default
  }

  return CHENNAI_DEFAULT;
}

export function detectBrowserGeolocation(timeoutMs = 4000) {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => resolve(pos.coords),
      (err) => reject(err),
      { timeout: timeoutMs, enableHighAccuracy: false, maximumAge: 60000 }
    );
  });
}

export async function resolveUserLocation() {
  // 1. Try Browser GPS (4-second timeout)
  try {
    const coords = await detectBrowserGeolocation(4000);
    const location = await reverseGeocode(coords.latitude, coords.longitude);
    return location;
  } catch (e) {
    // GPS denied or timed out
  }

  // 2. Fall back to IP Geolocation
  try {
    const ipLocation = await detectLocationByIP();
    if (ipLocation && ipLocation.latitude) return ipLocation;
  } catch (e) {
    // IP blocked or offline
  }

  // 3. Fall back gracefully to Chennai, India
  return CHENNAI_DEFAULT;
}
