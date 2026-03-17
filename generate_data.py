import pandas as pd
import numpy as np

NUM_SAMPLES = 100
LOW_ELEVATION = 890
HIGH_ELEVATION = 950
LOW_DRAINAGE = 2
HIGH_DRAINAGE = 9

# Randomly generate 50 values for each feature
rain = np.random.randint(5, 100, NUM_SAMPLES)
elevation = np.random.randint(LOW_ELEVATION, HIGH_ELEVATION, NUM_SAMPLES)
drainage = np.random.randint(LOW_DRAINAGE, HIGH_DRAINAGE, NUM_SAMPLES)


# R is high risk (positive factor), E and D are low risk (negative factors).
def calculate_risk(R, E, D):
    # We normalize them to keep the risk between ~0 and ~1.
    R_normalized = R / 100.0
    E_normalized = 1.0 - (E - LOW_ELEVATION) / \
        float(HIGH_ELEVATION - LOW_ELEVATION)
    D_normalized = 1.0 - D / float(HIGH_DRAINAGE)
    # We use a simple weighted average
    risk = (0.4 * R_normalized) + (0.35 * E_normalized) + (0.25 * D_normalized)
    # Clamp the result to stay between 0 and 1
    return np.clip(risk, 0.05, 0.95)


flood_risk = calculate_risk(rain, elevation, drainage)
df = pd.DataFrame({'Input_Rain': rain, 'Elevation': elevation,
                  'Drainage': drainage, 'Flood_Risk': flood_risk})
df.to_csv('training_data.csv', index=False)
