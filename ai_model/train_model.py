import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import os

# Load dataset
data = pd.read_csv("../dataset/goemotions_combined.csv")

# Input and output
X = data["text"]
y = data["labels"]

print("Dataset size:", len(data))

# Create ML pipeline
model = Pipeline([
    ("vectorizer", TfidfVectorizer(max_features=20000)),
    ("classifier", LogisticRegression(max_iter=500))
])

# Train model
model.fit(X, y)

# Create folder for saved models
os.makedirs("saved_models", exist_ok=True)

# Save trained model
joblib.dump(model, "saved_models/emotion_model.pkl")

print("Model trained and saved successfully!")