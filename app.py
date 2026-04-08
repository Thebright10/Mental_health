from flask import Flask, render_template, request, jsonify
import joblib
from response_generator import generate_response

app = Flask(__name__)

# load trained model
model = joblib.load("model/emotion_model.pkl")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    # predict emotion
    emotion = model.predict([user_message])[0]

    # generate response
    response = generate_response(emotion)

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)