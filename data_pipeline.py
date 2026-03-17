import pandas as pd
from joblib import load
from sklearn.linear_model import LinearRegression
import folium

# --- 1. CORE ML PREDICTION FUNCTION (Uses the saved 'brain') ---


def predict_risk(rainfall, elevation, drainage):
    """
    Loads the trained LinearRegression model and predicts a flood risk score (0 to 1).

    Inputs are: 
    - rainfall (float, in mm)
    - elevation (float, in meters)
    - drainage (int, 1-10 score)
    """
    try:
        # Load the saved model 'brain' file
        model = load('trained_model.joblib')

        # Format the three inputs into a pandas DataFrame row (required by scikit-learn)
        input_data = pd.DataFrame(
            [[rainfall, elevation, drainage]],
            columns=['Input_Rain', 'Elevation', 'Drainage']
        )

        # Predict the continuous risk score
        risk_score = model.predict(input_data)[0]

        # Ensure the score stays within a clean 0.0 to 1.0 range
        return max(0.0, min(1.0, risk_score))

    except FileNotFoundError:
        print("Error: 'trained_model.joblib' not found. Did you run train_model.py?")
        return 0.5  # Return a neutral score if the model isn't found

# --- 2. MAIN MAP GENERATION PIPELINE ---


def generate_risk_map(current_rainfall_mm, filename):
    """Generates an HTML map showing the flood risk for all Bengaluru zones based on rainfall."""

    print(f"\n--- Generating map for {current_rainfall_mm}mm rainfall ---")

    # Load the static data for the 8-10 Bengaluru locations
    # Make sure this CSV file is correctly populated with coordinates and scores!
    zones = pd.read_csv('bengaluru_zones.csv')

    # Set the Map Center (Approximate center of Bengaluru)
    map_center = [12.9716, 77.5946]
    m = folium.Map(location=map_center, zoom_start=11,
                   tiles="CartoDB positron")

    # Loop through every row (every zone) in the CSV
    for index, zone in zones.iterrows():
        elevation = zone['Elevation']
        drainage = zone['Drainage_Score']

        # Calculate the actual risk using the predictor function
        risk_score = predict_risk(current_rainfall_mm, elevation, drainage)

        # Determine Color and Icon based on Risk Score
        if risk_score >= 0.7:
            color = 'red'       # High Alert (70%+)
            risk_level_text = "HIGH ALERT"
            icon = 'times-circle'
        elif risk_score >= 0.4:
            color = 'orange'    # Medium Alert (40%-70%)
            risk_level_text = "MEDIUM RISK"
            icon = 'exclamation-triangle'
        else:
            color = 'green'     # Low Risk (below 40%)
            risk_level_text = "LOW RISK"
            icon = 'check-circle'

        # Create the HTML content for the pop-up marker
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

        # Add the marker to the map
        folium.Marker(
            location=[zone['Latitude'], zone['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon=icon,
                             prefix='fa')  # Font Awesome icons
        ).add_to(m)

    # Save the final interactive map to an HTML file
    m.save(filename)
    print(f"Map successfully saved as {filename}")
    return filename

# --- 3. TEST EXECUTION (FOR YOUR VERIFICATION) ---


# Test 1: Low Rainfall (Should show mostly GREEN spots)
generate_risk_map(current_rainfall_mm=20, filename='map_output_low_rain.html')

# Test 2: Heavy Rainfall (Should show RED spots, especially in low-drainage areas)
generate_risk_map(current_rainfall_mm=85, filename='map_output_high_rain.html')

print("\n--- Part A: Phase 3 COMPLETE ---")
print("Open the HTML files in your browser to verify the dynamic color-coding!")
