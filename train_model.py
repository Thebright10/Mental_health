import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# load dataset
data = pd.read_csv("dataset/emotions.csv")

X = data["text"]
y = data["emotion"]

# create ML pipeline
model = Pipeline([
    ("vectorizer", TfidfVectorizer()),
    ("classifier", LogisticRegression())
])

# train model
model.fit(X, y)

# create model folder if not exists
os.makedirs("model", exist_ok=True)

# save model
joblib.dump(model, "model/emotion_model.pkl")

print("Model trained and saved successfully!")