import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load and preprocess data
import os
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(base_dir, 'data', 'labeled_transactions.csv')
df = pd.read_csv(data_path)
le_location = LabelEncoder()
df['location_encoded'] = le_location.fit_transform(df['location'])

X = df[['amount', 'location_encoded']]
y = df['is_fraud']

# Train model
model = DecisionTreeClassifier()
model.fit(X, y)

# Save model and encoder
joblib.dump(model, 'fraud_model.pkl')
joblib.dump(le_location, 'location_encoder.pkl')

print("✅ Model trained and saved.")