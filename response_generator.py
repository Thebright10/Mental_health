def generate_response(emotion):

    responses = {

        "sad": "I'm sorry you're feeling sad. Try talking to someone you trust.",

        "stress": "It sounds like you're stressed. Try taking a short break and breathe slowly.",

        "anxiety": "Feeling anxious is common. Try focusing on slow breathing.",

        "anger": "Take a moment to relax and step away from the situation.",

        "happy": "That's great to hear! Keep doing things that make you happy.",

        "neutral": "Thanks for sharing. I'm here to listen."
    }

    return responses.get(emotion, "I'm here for you. Tell me more about how you feel.")