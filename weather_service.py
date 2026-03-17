"""
weather_service.py — Open-Meteo API Integration for RainRisk Spotter
No API key required. Fetches live and forecast weather data for Bengaluru.
"""

import requests
from datetime import datetime, timezone
import pytz

# Bengaluru coordinates
BENGALURU_LAT = 12.9716
BENGALURU_LON = 77.5946
BENGALURU_TZ = pytz.timezone("Asia/Kolkata")

OPENMETEO_BASE = "https://api.open-meteo.com/v1/forecast"


def get_current_weather():
    """
    Fetches current weather conditions for Bengaluru from Open-Meteo.
    Returns a dict with temperature, humidity, rain, wind_speed, weather_code, etc.
    """
    params = {
        "latitude": BENGALURU_LAT,
        "longitude": BENGALURU_LON,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
        ],
        "hourly": [
            "precipitation",
            "rain",
            "relative_humidity_2m",
            "temperature_2m",
        ],
        "daily": [
            "precipitation_sum",
            "rain_sum",
            "temperature_2m_max",
            "temperature_2m_min",
            "weather_code",
        ],
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
        "past_days": 3,
    }

    try:
        response = requests.get(OPENMETEO_BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})

        # Parse current conditions
        rain_mm = current.get("rain", 0) or 0
        precip_mm = current.get("precipitation", 0) or 0
        total_rain = max(rain_mm, precip_mm)  # Take whichever is larger

        # Parse hourly data for last 24h accumulated rain
        hourly_times = hourly.get("time", [])
        hourly_rain = hourly.get("rain", [])
        hourly_precip = hourly.get("precipitation", [])
        hourly_humidity = hourly.get("relative_humidity_2m", [])
        hourly_temp = hourly.get("temperature_2m", [])

        # Accumulate rain over last 24 hours
        now_str = current.get("time", "")
        rain_24h = 0.0
        rain_3h = 0.0
        rain_chart_labels = []
        rain_chart_values = []
        humidity_chart_values = []

        try:
            now_dt = datetime.fromisoformat(now_str)
        except Exception:
            now_dt = datetime.now()

        for i, t in enumerate(hourly_times):
            try:
                t_dt = datetime.fromisoformat(t)
                diff_hours = (now_dt - t_dt).total_seconds() / 3600.0
                r = (hourly_rain[i] or 0) if i < len(hourly_rain) else 0
                p = (hourly_precip[i] or 0) if i < len(hourly_precip) else 0
                rain_val = max(r, p)

                if 0 <= diff_hours <= 24:
                    rain_24h += rain_val
                if 0 <= diff_hours <= 3:
                    rain_3h += rain_val

                # Chart: last 7 days hourly (sample every 6 hours)
                if -168 <= diff_hours <= 0 and i % 6 == 0:
                    rain_chart_labels.append(t_dt.strftime("%d %b %H:%M"))
                    rain_chart_values.append(round(rain_val, 2))
                    h_val = hourly_humidity[i] if i < len(hourly_humidity) else 60
                    humidity_chart_values.append(h_val)
            except Exception:
                continue

        # Parse daily forecast (next 7 days)
        daily_times = daily.get("time", [])
        daily_rain_sum = daily.get("rain_sum", [])
        daily_precip_sum = daily.get("precipitation_sum", [])
        daily_temp_max = daily.get("temperature_2m_max", [])
        daily_temp_min = daily.get("temperature_2m_min", [])
        daily_weather_code = daily.get("weather_code", [])

        forecast_days = []
        for i, day_str in enumerate(daily_times):
            try:
                day_dt = datetime.fromisoformat(day_str)
                diff = (day_dt.date() - now_dt.date()).days
                if 0 <= diff <= 6:
                    r = (daily_rain_sum[i] or 0) if i < len(daily_rain_sum) else 0
                    p = (daily_precip_sum[i] or 0) if i < len(daily_precip_sum) else 0
                    rain_val = max(r, p)
                    forecast_days.append({
                        "date": day_dt.strftime("%a, %d %b"),
                        "rain_mm": round(rain_val, 1),
                        "temp_max": round(daily_temp_max[i], 1) if i < len(daily_temp_max) and daily_temp_max[i] else "—",
                        "temp_min": round(daily_temp_min[i], 1) if i < len(daily_temp_min) and daily_temp_min[i] else "—",
                        "weather_code": daily_weather_code[i] if i < len(daily_weather_code) else 0,
                        "icon": get_weather_icon(daily_weather_code[i] if i < len(daily_weather_code) else 0),
                        "description": get_weather_description(daily_weather_code[i] if i < len(daily_weather_code) else 0),
                    })
            except Exception:
                continue

        weather_code = current.get("weather_code", 0) or 0
        humidity = current.get("relative_humidity_2m", 60) or 60

        # Dynamic drainage penalty: rain accumulation reduces effective drainage
        # This is used to adjust zone drainage scores in the main app
        drainage_penalty = calculate_drainage_penalty(rain_24h, humidity)

        return {
            "success": True,
            "temperature": round(current.get("temperature_2m", 25), 1),
            "feels_like": round(current.get("apparent_temperature", 25), 1),
            "humidity": humidity,
            "rain_current": round(total_rain, 2),
            "rain_3h": round(rain_3h, 2),
            "rain_24h": round(rain_24h, 2),
            "wind_speed": round(current.get("wind_speed_10m", 0), 1),
            "wind_direction": current.get("wind_direction_10m", 0),
            "pressure": round(current.get("surface_pressure", 1013), 1),
            "weather_code": weather_code,
            "weather_icon": get_weather_icon(weather_code),
            "weather_desc": get_weather_description(weather_code),
            "forecast": forecast_days,
            "chart_labels": rain_chart_labels,
            "chart_rain": rain_chart_values,
            "chart_humidity": humidity_chart_values,
            "drainage_penalty": drainage_penalty,
            "alert_level": get_alert_level(rain_24h, rain_3h),
            "alert_message": get_alert_message(rain_24h, rain_3h),
            "fetched_at": datetime.now(BENGALURU_TZ).strftime("%d %b %Y, %I:%M %p IST"),
        }

    except requests.exceptions.ConnectionError:
        return _fallback_weather("Connection error — check internet")
    except requests.exceptions.Timeout:
        return _fallback_weather("API timeout — using defaults")
    except Exception as e:
        return _fallback_weather(f"API error: {str(e)[:60]}")


def calculate_drainage_penalty(rain_24h, humidity):
    """
    Returns a drainage penalty (0.0 to 5.0) that gets subtracted from zone drainage scores.
    High recent rainfall and high humidity reduce effective drainage capacity.
    """
    rain_penalty = min(rain_24h / 25.0, 3.0)  # up to 3 penalty for heavy rain
    humidity_penalty = max(0, (humidity - 70) / 30.0) * 2.0  # up to 2 penalty when very humid
    return round(min(rain_penalty + humidity_penalty, 5.0), 2)


def get_alert_level(rain_24h, rain_3h):
    """Returns alert level: safe, watch, warning, emergency"""
    if rain_3h > 30 or rain_24h > 80:
        return "emergency"
    elif rain_3h > 15 or rain_24h > 40:
        return "warning"
    elif rain_3h > 5 or rain_24h > 15:
        return "watch"
    else:
        return "safe"


def get_alert_message(rain_24h, rain_3h):
    level = get_alert_level(rain_24h, rain_3h)
    messages = {
        "emergency": f"🚨 EMERGENCY: Extreme rainfall detected! {rain_24h:.1f}mm in 24h. Evacuation protocols may apply.",
        "warning": f"⚠️ WARNING: Heavy rainfall ({rain_24h:.1f}mm / 24h). High flood risk across multiple zones.",
        "watch": f"🟡 WATCH: Moderate rain activity ({rain_24h:.1f}mm / 24h). Monitor low-lying areas.",
        "safe": "✅ CONDITIONS NORMAL: No significant rainfall. Drainage systems operating normally.",
    }
    return messages.get(level, "Status unknown")


def get_weather_icon(code):
    """Maps WMO weather codes to Material Symbols icon names."""
    if code == 0:
        return "clear_day"
    elif code in [1, 2]:
        return "partly_cloudy_day"
    elif code == 3:
        return "cloud"
    elif code in [45, 48]:
        return "foggy"
    elif code in [51, 53, 55, 56, 57]:
        return "grain"
    elif code in [61, 63, 65, 66, 67]:
        return "rainy"
    elif code in [71, 73, 75, 77]:
        return "weather_snowy"
    elif code in [80, 81, 82]:
        return "rainy"
    elif code in [85, 86]:
        return "snowing"
    elif code in [95, 96, 99]:
        return "thunderstorm"
    else:
        return "cloud"


def get_weather_description(code):
    """Maps WMO weather interpretation codes to human-readable descriptions."""
    descriptions = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Icy Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Heavy Drizzle",
        56: "Freezing Drizzle",
        57: "Heavy Freezing Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        66: "Light Freezing Rain",
        67: "Heavy Freezing Rain",
        71: "Slight Snowfall",
        73: "Moderate Snowfall",
        75: "Heavy Snowfall",
        80: "Slight Showers",
        81: "Moderate Showers",
        82: "Violent Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Severe Thunderstorm",
    }
    return descriptions.get(code, "Cloudy")


def _fallback_weather(error_msg):
    """Returns a safe fallback payload when the API fails."""
    return {
        "success": False,
        "error": error_msg,
        "temperature": 27.0,
        "feels_like": 29.0,
        "humidity": 65,
        "rain_current": 0.0,
        "rain_3h": 0.0,
        "rain_24h": 0.0,
        "wind_speed": 8.0,
        "wind_direction": 270,
        "pressure": 1013.0,
        "weather_code": 1,
        "weather_icon": "partly_cloudy_day",
        "weather_desc": "Data Unavailable",
        "forecast": [],
        "chart_labels": [],
        "chart_rain": [],
        "chart_humidity": [],
        "drainage_penalty": 0.0,
        "alert_level": "safe",
        "alert_message": f"⚠️ Weather API Error: {error_msg}. Using default values.",
        "fetched_at": datetime.now(BENGALURU_TZ).strftime("%d %b %Y, %I:%M %p IST"),
    }
