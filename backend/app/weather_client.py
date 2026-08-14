
from datetime import date

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_DESCRIPTIONS = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "rain showers", 81: "rain showers", 82: "violent rain showers",
    95: "thunderstorm",
}


async def geocode_city(location: str) -> dict | None:
    """Resolves a location string to coordinates, disambiguating by country
    when the user provides one (e.g. "Paris, France" vs "Paris, Texas").

    Without a country hint, Open-Meteo's top match is picked by population,
    which silently guesses wrong for common city names shared across
    countries (Springfield, San José, etc.) — there was no way to tell it
    got the wrong one. Returns the resolved display name too, so the UI can
    show exactly which place it used.
    """
    parts = [p.strip() for p in location.split(",", 1)]
    city_part = parts[0]
    country_hint = parts[1].lower() if len(parts) > 1 else None

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(GEOCODE_URL, params={"name": city_part, "count": 10})
        resp.raise_for_status()
        results = resp.json().get("results")
        if not results:
            return None

    match = results[0]  # default: most populous match, same as before
    if country_hint:
        for r in results:
            country = (r.get("country") or "").lower()
            country_code = (r.get("country_code") or "").lower()
            if country_hint in country or country_hint == country_code:
                match = r
                break

    display_name = f"{match['name']}, {match.get('country', '')}".strip(", ")
    return {"latitude": match["latitude"], "longitude": match["longitude"], "display_name": display_name}


async def get_forecast_for_date(lat: float, lon: float, target_date: date) -> dict | None:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
                "timezone": "auto",
                "forecast_days": 16,  # Open-Meteo's free-tier max lookahead
            },
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        dates = daily.get("time", [])
        target_str = target_date.isoformat()
        if target_str not in dates:
            return None  # event is further out than the forecast window
        idx = dates.index(target_str)
        code = daily["weathercode"][idx]
        return {
            "temp_max": daily["temperature_2m_max"][idx],
            "temp_min": daily["temperature_2m_min"][idx],
            "precipitation_probability": daily["precipitation_probability_max"][idx],
            "condition": WEATHER_CODE_DESCRIPTIONS.get(code, "variable conditions"),
        }
