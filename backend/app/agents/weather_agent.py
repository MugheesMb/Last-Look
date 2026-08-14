
from datetime import date, timedelta

from app.models import CountdownState
from app.weather_client import geocode_city, get_forecast_for_date


async def weather_agent(state: CountdownState) -> CountdownState:
    location = state.get("location")
    if not location:
        return {"weather_summary": None}

    try:
        geo = await geocode_city(location)
        if not geo:
            return {"weather_summary": None}

        target_date = date.today() + timedelta(days=state["days_until"])
        forecast = await get_forecast_for_date(geo["latitude"], geo["longitude"], target_date)
        if not forecast:
            return {"weather_summary": None}

        summary = (
            f"{geo['display_name']} — {forecast['condition']}, "
            f"{round(forecast['temp_min'])}-{round(forecast['temp_max'])}°C, "
            f"{forecast['precipitation_probability']}% chance of rain"
        )
        return {"weather_summary": summary}
    except Exception as e:
        # Weather is an enhancement, not a required input — a failed lookup
        # shouldn't sink the whole countdown, just skip the weather framing.
        print(f"[weather] lookup failed: {e!r}")
        return {"weather_summary": None}
