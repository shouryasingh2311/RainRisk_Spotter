import pandas as pd
from sklearn.linear_model import LinearRegression  # Changed to LinearRegression
from joblib import dump

# 1. Load the training data (Your 100 scenarios)
data = pd.read_csv('training_data.csv')

# X are the features (inputs)
X = data[['Input_Rain', 'Elevation', 'Drainage']]
# y is the target (Flood_Risk score 0.0 to 1.0)
y = data['Flood_Risk']

# 2. Train the Machine Learning Model (Linear Regression for continuous score)
model = LinearRegression()
model.fit(X, y)

# 3. Check and Print Accuracy (R-squared score for regression)
score = model.score(X, y)
print("--- ML Model Training Complete ---")
print(f"Model Training R-squared Score: {score*100:.2f}%")

# 4. Save the Model
dump(model, 'trained_model.joblib')
print("Model successfully saved as trained_model.joblib")
