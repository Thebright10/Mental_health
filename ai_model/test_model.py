import joblib

model = joblib.load("saved_models/emotion_model.pkl")

text = "I feel very depressed and lonely"

prediction = model.predict([text])

print("Predicted emotion:", prediction[0])