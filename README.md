# RainRisk Spotter 🌧️

**Real-time flood risk intelligence dashboard for Bengaluru, powered by live weather data and machine learning.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![Open-Meteo](https://img.shields.io/badge/Weather-Open--Meteo-cyan.svg)](https://open-meteo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌦️ **Live Weather** | Real-time temperature, humidity, rainfall, wind via [Open-Meteo](https://open-meteo.com) (no API key needed) |
| 🗺️ **Flood Risk Heatmap** | Interactive Folium map with zone-level risk scoring for 16 Bengaluru locations |
| 🤖 **ML Prediction Engine** | scikit-learn Linear Regression model trained on 100 flood scenarios |
| 🚰 **Dynamic Drainage Scoring** | Drainage capacity auto-adjusted based on live rain accumulation and humidity |
| ⚡ **Auto-Refresh** | Dashboard refreshes weather data every 15 minutes automatically |
| 📊 **7-Day Rainfall Chart** | Historical and forecast rainfall trend via Chart.js |
| 🗓️ **5-Day Forecast** | Daily weather forecast with flood risk implications |
| 🔴 **Smart Alert System** | 4-level alert banner: Safe → Watch → Warning → Emergency |
| 🔬 **What-If Simulator** | Manually input any rainfall value to test hypothetical scenarios |
| 📍 **City Risk Index** | Single aggregate score summarizing Bengaluru's overall flood risk |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/shouryasingh2311/RainRisk_Spotter.git
cd RainRisk_Spotter

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train the ML model (first time only)
python train_model.py

# Run the app
python heatapp.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET / POST | Main dashboard with live weather and map |
| `/api/weather` | GET | JSON: current weather data |
| `/api/weather?refresh=true` | GET | JSON: force-refresh weather cache |
| `/api/predict` | POST | JSON: run risk prediction for given rainfall |

### Example: `/api/predict`
```json
POST /api/predict
{ "rainfall": 65.0, "use_live_drainage": true }

→ { "success": true, "stats": {...}, "alerts": {"high": [...], "medium": [...]} }
```

---

## 🏗️ Architecture

```
RainRisk_Spotter/
├── heatapp.py          # Flask app + map generation + API routes
├── weather_service.py  # Open-Meteo integration + alert logic
├── train_model.py      # ML model training script
├── generate_data.py    # Training data generator
├── data_pipeline.py    # Standalone map generation pipeline
├── bengaluru_zones.csv # 16 Bengaluru flood-risk zones
├── training_data.csv   # 100 training scenarios
├── trained_model.joblib # Serialized ML model
├── requirements.txt
└── templates/
    └── index.html      # Full dashboard UI (Vanilla CSS + Chart.js)
```

---

## 🧠 ML Model

- **Algorithm**: Linear Regression (scikit-learn)
- **Features**: `rainfall_mm`, `elevation_m`, `effective_drainage_score`
- **Target**: Flood risk probability (0.0 – 1.0)
- **Training set**: 100 synthetically generated Bengaluru scenarios
- **Drainage penalty**: Live rainfall accumulation dynamically reduces each zone's drainage score before prediction

### Risk Thresholds
| Score | Level | Color |
|-------|-------|-------|
| ≥ 0.70 | HIGH ALERT | 🔴 Red |
| 0.40 – 0.69 | MEDIUM RISK | 🟠 Orange |
| < 0.40 | LOW RISK | 🟢 Green |

---

## 🌍 Weather Data Source

All weather data comes from **[Open-Meteo](https://open-meteo.com)** — a free, open-source weather API that requires **no API key**.

Data fetched:
- Current temperature, humidity, rain, wind, pressure
- Hourly precipitation (last 3 days + 7-day forecast)
- Daily max/min temperatures and weather codes

---

## 📍 Monitored Zones (Bengaluru)

Silk Board Junction • Madiwala Lake Area • Electronic City Phase 1 • Indiranagar • KR Puram Bridge • Whitefield Main Road • Marathahalli Bridge • HSR Layout • Malleswaram Junction • Malleshwaram 18th Cross • Yeshwanthpur • Nagawara • Rajajinagar • Peenya Industrial Area • Hebbal Bridge • Outer Ring Road

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask 3.x |
| ML | scikit-learn, pandas, numpy |
| Maps | Folium (Leaflet.js) |
| Weather | Open-Meteo REST API |
| Frontend | Vanilla HTML/CSS/JS |
| Charts | Chart.js 4.x |
| Fonts | Google Fonts (Inter, Space Grotesk) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

*Built with ❤️ for Bengaluru flood awareness*
