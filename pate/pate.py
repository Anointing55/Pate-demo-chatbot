from flask import Flask, request, jsonify
from pate import pate

app = Flask(__name__)
pate.initialize_database()

@app.route("/")
def home():
    return "PATE AI Chatbot is Live!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"]
    user_id = data.get("user_id", "default_user")
    lang = pate.detect_language(message)

    reply = pate.ask_pate(message, user_id, language=lang)
    return jsonify({"reply": reply})

@app.route("/progress", methods=["POST"])
def progress():
    data = request.json
    user_id = data.get("user_id", "default_user")
    return jsonify({"progress": pate.get_progress(user_id)})

if __name__ == "__main__":
    app.run()
