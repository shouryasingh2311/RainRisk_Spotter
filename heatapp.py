"""
heatapp.py — RainRisk Spotter (DYNAMIC REMASTER)
Flask backend with Open-Meteo real-time weather integration.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import pandas as pd
from joblib import load
import folium
from folium.plugins import HeatMap
import io
import numpy as np
from weather_service import get_current_weather, BENGALURU_LAT, BENGALURU_LON

app = Flask(__name__)

# Cache weather so we don't hammer the API on every page reload
_weather_cache = {"data": None, "fetched_at": None}
CACHE_TTL_SECONDS = 900  # 15 minutes


def get_cached_weather():
    """Returns cached weather data, refreshing if older than 15 minutes."""
    import time
    now = time.time()
    if (
        _weather_cache["data"] is None
        or _weather_cache["fetched_at"] is None
        or (now - _weather_cache["fetched_at"]) > CACHE_TTL_SECONDS
    ):
        _weather_cache["data"] = get_current_weather()
        _weather_cache["fetched_at"] = now
    return _weather_cache["data"]


def force_refresh_weather():
    """Clears the cache and fetches fresh data immediately."""
    _weather_cache["data"] = get_current_weather()
    import time
    _weather_cache["fetched_at"] = time.time()
    return _weather_cache["data"]


def predict_risk(rainfall, elevation, drainage):
    """Loads the ML model and predicts flood risk score (0 to 1)."""
    try:
        model = load(os.path.join(os.path.dirname(__file__), 'trained_model.joblib'))
        input_data = pd.DataFrame(
            [[rainfall, elevation, drainage]],
            columns=['Input_Rain', 'Elevation', 'Drainage']
        )
        risk_score = model.predict(input_data)[0]
        return max(0.0, min(1.0, risk_score))
    except FileNotFoundError:
        print("ERROR: trained_model.joblib not found.", file=sys.stderr)
        return 0.5


def generate_html_map_data(current_rainfall_mm, drainage_penalty=0.0):
    """
    Generates the Folium flood-risk heatmap.
    drainage_penalty: subtracted from each zone's drainage score (live weather context).
    """
    csv_path = os.path.join(os.path.dirname(__file__), 'bengaluru_zones.csv')
    if not os.path.exists(csv_path):
        return "<h1>Error: bengaluru_zones.csv not found!</h1>", None, None

    zones = pd.read_csv(csv_path).fillna(0)
    map_center = [BENGALURU_LAT, BENGALURU_LON]

    m = folium.Map(
        location=map_center,
        zoom_start=11,
        tiles="cartodbdark_matter"
    )

    # Add city center reference marker
    folium.Marker(
        location=map_center,
        popup=folium.Popup(
            "<div style='font-family:sans-serif;color:#fff;background:#0f172a;padding:8px;border-radius:6px'>"
            "<b style='color:#00f0ff'>📍 Bengaluru City Center</b><br>"
            f"<small>Live Rainfall: {current_rainfall_mm} mm</small></div>",
            max_width=200
        ),
        icon=folium.Icon(color='blue', icon='home', prefix='fa')
    ).add_to(m)

    heatmap_data = []
    alerts = {'high': [], 'medium': [], 'low': []}

    for _, zone in zones.iterrows():
        elevation = zone['Elevation']
        # Apply weather-based drainage penalty
        raw_drainage = zone['Drainage_Score']
        effective_drainage = max(1, raw_drainage - drainage_penalty)
        historical_flood = zone['Historical_Flood']

        risk_score = predict_risk(current_rainfall_mm, elevation, effective_drainage)

        # Extra risk bump for zones with historical flooding + active rain
        if historical_flood == 1 and current_rainfall_mm > 30:
            risk_score = min(1.0, risk_score * 1.15)

        heatmap_weight = risk_score * 10.0

        if risk_score >= 0.7:
            color = 'red'
            risk_level_text = "🔴 HIGH ALERT — FLOOD IMMINENT"
            historical_msg = "⚠️ High Historical Flood Risk" if historical_flood == 1 else "📋 No History"
            alerts['high'].append({'name': zone['Location_Name'], 'risk': risk_score * 100,
                                   'drainage': effective_drainage, 'elevation': elevation})
        elif risk_score >= 0.4:
            color = 'orange'
            risk_level_text = "🟠 MEDIUM RISK — Monitor Closely"
            historical_msg = "🚨 Past Incidents Reported" if historical_flood == 1 else "📋 No History"
            alerts['medium'].append({'name': zone['Location_Name'], 'risk': risk_score * 100,
                                     'drainage': effective_drainage, 'elevation': elevation})
        else:
            color = 'green'
            risk_level_text = "🟢 LOW RISK — Safe Passage"
            historical_msg = "✅ Clean History"
            alerts['low'].append({'name': zone['Location_Name'], 'risk': risk_score * 100,
                                  'drainage': effective_drainage, 'elevation': elevation})

        heatmap_data.append([zone['Latitude'], zone['Longitude'], heatmap_weight])

        drainage_bar = "█" * int(effective_drainage) + "░" * (10 - int(effective_drainage))
        risk_bar_filled = int(risk_score * 10)
        risk_bar = "█" * risk_bar_filled + "░" * (10 - risk_bar_filled)

        penalty_note = f"<br><span style='color:#fbbf24;font-size:10px'>⚡ Drainage reduced by {drainage_penalty:.1f} due to live rain</span>" if drainage_penalty > 0 else ""

        popup_html = f"""
        <div style='font-family:Inter,sans-serif;min-width:270px;background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px;border:1px solid #334155;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                <div style='width:10px;height:10px;border-radius:50%;background:{color};box-shadow:0 0 8px {color}'></div>
                <b style='color:{color};font-size:15px'>{zone['Location_Name']}</b>
            </div>
            <div style='font-size:11px;color:{color};font-weight:bold;margin-bottom:8px;padding:4px 8px;background:{color}22;border-radius:4px'>{risk_level_text}</div>
            <hr style='border-color:#334155;margin:6px 0'>
            <table style='width:100%;font-size:12px;border-collapse:collapse'>
                <tr><td style='color:#94a3b8;padding:2px 0'>Risk Score</td><td style='color:#fff;font-weight:bold'>{risk_score*100:.1f}%</td></tr>
                <tr><td style='color:#94a3b8'>Risk Level</td><td style='font-family:monospace;font-size:10px;color:{color}'>{risk_bar}</td></tr>
                <tr><td style='color:#94a3b8'>Rainfall</td><td style='color:#60a5fa'>{current_rainfall_mm:.1f} mm</td></tr>
                <tr><td style='color:#94a3b8'>Elevation</td><td style='color:#a78bfa'>{elevation:.0f} m</td></tr>
                <tr><td style='color:#94a3b8'>Eff. Drainage</td><td style='color:#34d399'>{effective_drainage:.1f}/10</td></tr>
            </table>
            <div style='font-family:monospace;font-size:9px;color:#475569;margin-top:4px'>Drainage: [{drainage_bar}]{penalty_note}</div>
            <hr style='border-color:#334155;margin:6px 0'>
            <div style='font-size:11px;color:#94a3b8'>{historical_msg}</div>
        </div>
        """

        folium.Marker(
            location=[zone['Latitude'], zone['Longitude']],
            popup=folium.Popup(popup_html, max_width=310),
            icon=folium.Icon(color=color, icon='tint', prefix='fa', icon_color='white')
        ).add_to(m)

    HeatMap(heatmap_data, radius=32, blur=22, max_opacity=0.85, max_val=5.0).add_to(m)

    buf = io.BytesIO()
    m.save(buf, close_file=False)
    m_html = buf.getvalue().decode()

    for key in alerts:
        alerts[key] = sorted(alerts[key], key=lambda x: x['risk'], reverse=True)

    high_count = len(alerts['high'])
    stats = {
        'total_zones': len(zones),
        'total_high_alerts': high_count,
        'total_medium_alerts': len(alerts['medium']),
        'total_low_alerts': len(alerts['low']),
        'drainage_status': "Critical" if high_count > 5 else ("Warning" if high_count > 0 else "Optimal"),
        'city_risk_score': round(
            (high_count * 3 + len(alerts['medium']) * 1.5) / max(len(zones), 1) * 10, 1
        ),
    }

    return m_html, alerts, stats


# ────────────────────────────────────────────────────────────────────────────
# FLASK ROUTES
# ────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = get_cached_weather()
    map_html = None
    alerts = None
    rainfall = round(weather.get('rain_24h', 0) if weather.get('success') else 20.0, 1)
    stats = {
        'total_zones': 16,
        'total_high_alerts': 0,
        'total_medium_alerts': 0,
        'total_low_alerts': 0,
        'drainage_status': "N/A",
        'city_risk_score': 0,
    }
    mode = "live"

    if request.method == 'POST':
        try:
            rainfall_input = request.form.get('rainfall_input')
            rainfall = float(rainfall_input)
            mode = request.form.get('mode', 'simulator')
        except (ValueError, TypeError):
            rainfall = 20.0
            mode = "simulator"

        drainage_penalty = weather.get('drainage_penalty', 0.0) if mode == "live" else 0.0
        result = generate_html_map_data(rainfall, drainage_penalty)

        if isinstance(result, tuple) and len(result) == 3:
            map_html, alerts, stats = result
        else:
            map_html = result

    elif request.method == 'GET':
        # On initial load, auto-run with live rainfall
        drainage_penalty = weather.get('drainage_penalty', 0.0)
        live_rain = weather.get('rain_24h', 0) if weather.get('success') else 20.0
        rainfall = round(live_rain, 1)
        result = generate_html_map_data(rainfall, drainage_penalty)
        if isinstance(result, tuple) and len(result) == 3:
            map_html, alerts, stats = result
        else:
            map_html = result

    return render_template(
        'index.html',
        map_html=map_html,
        current_rainfall=rainfall,
        alerts=alerts,
        stats=stats,
        weather=weather,
        mode=mode,
    )


@app.route('/api/weather')
def api_weather():
    """JSON endpoint to get fresh weather data (used by auto-refresh JS)."""
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        data = force_refresh_weather()
    else:
        data = get_cached_weather()
    return jsonify(data)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """JSON endpoint to run a quick prediction for given rainfall value."""
    try:
        body = request.get_json(force=True)
        rainfall = float(body.get('rainfall', 20))
        use_live_drainage = body.get('use_live_drainage', True)
        weather = get_cached_weather()
        dp = weather.get('drainage_penalty', 0.0) if use_live_drainage else 0.0
        _, alerts, stats = generate_html_map_data(rainfall, dp)
        return jsonify({'success': True, 'alerts': alerts, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    print("[RainRisk Spotter] Dynamic Edition - Starting up...")
    print("[Weather] Fetching live data from Open-Meteo...")
    w = get_cached_weather()
    if w.get('success'):
        print(f"[Weather] OK: {w['weather_desc']}, {w['temperature']}C, Rain 24h: {w['rain_24h']}mm")
    else:
        print(f"[Weather] API issue: {w.get('error')}. Using defaults.")
    print("[Flask] Starting server at http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
