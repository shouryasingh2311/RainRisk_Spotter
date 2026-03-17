import os
from flask import Flask, render_template, request
import pandas as pd
from joblib import load
import folium
import io

# --- 1. SETUP & CORE LOGIC ---
app = Flask(__name__)


def predict_risk(rainfall, elevation, drainage):
    """Loads the model and predicts a flood risk score (0 to 1)."""
    try:
        model = load('trained_model.joblib')
        input_data = pd.DataFrame(
            [[rainfall, elevation, drainage]],
            columns=['Input_Rain', 'Elevation', 'Drainage']
        )
        risk_score = model.predict(input_data)[0]
        return max(0.0, min(1.0, risk_score))
    except FileNotFoundError:
        return 0.5

# --- 2. MAP GENERATION LOGIC ---


def generate_html_map_data(current_rainfall_mm):
    """Generates the Folium map and returns the HTML content as a string."""

    if not os.path.exists('bengaluru_zones.csv'):
        return "<h1>Error: bengaluru_zones.csv not found in the project folder!</h1>"

    zones = pd.read_csv('bengaluru_zones.csv')

    map_center = [12.9716, 77.5946]
    m = folium.Map(location=map_center, zoom_start=11,
                   tiles="CartoDB positron")

    for index, zone in zones.iterrows():
        elevation = zone['Elevation']
        drainage = zone['Drainage_Score']

        # Calculate the actual risk
        risk_score = predict_risk(current_rainfall_mm, elevation, drainage)

        # Determine Color and Icon
        if risk_score >= 0.7:
            color = 'red'
            risk_level_text = "HIGH ALERT"
            icon = 'times-circle'
        elif risk_score >= 0.4:
            color = 'orange'
            risk_level_text = "MEDIUM RISK"
            icon = 'exclamation-triangle'
        else:
            color = 'green'
            risk_level_text = "LOW RISK"
            icon = 'check-circle'

        popup_html = f"""
        <div style='font-family: sans-serif;'>
            <b>Location: {zone['Location_Name']}</b><br>
            <hr style='margin: 5px 0;'>
            <b>Rainfall Input:</b> {current_rainfall_mm} mm<br>
            <b>Elevation:</b> {elevation} m<br>
            <b>Drainage:</b> {drainage}/10<br>
            <hr style='margin: 5px 0;'>
            <span style='font-size: 16px; color: {color}'>
                <b>{risk_level_text}: {risk_score*100:.1f}%</b>
            </span>
        </div>
        """

        folium.Marker(
            location=[zone['Latitude'], zone['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)

    data = io.BytesIO()
    m.save(data, close_file=False)
    m_html = data.getvalue().decode()

    return m_html

# --- 3. FLASK ROUTES ---


@app.route('/', methods=['GET', 'POST'])
def index():
    # Set map_html to None on default, so map is hidden initially
    map_html = None
    rainfall = 50

    if request.method == 'POST':
        try:
            rainfall_input = request.form.get('rainfall_input')
            rainfall = float(rainfall_input)

            # Map is calculated ONLY on POST (button click)
            map_html = generate_html_map_data(rainfall)

        except ValueError:
            map_html = "<h1>Invalid rainfall value entered. Please use a number.</h1>"

    # elif request.method == 'GET':
        # Removed map generation here. map_html remains None unless it's a POST request.

    return render_template('index.html', map_html=map_html, current_rainfall=rainfall)


if __name__ == '__main__':
    # Use your specific IPv4 Address here and port
    app.run(debug=True, host='192.168.56.1', port=5000)
