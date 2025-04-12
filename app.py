from flask import Flask, request, jsonify, render_template
from pate import ask_pate, get_progress, detect_language  # Import necessary functions from pate.py

app = Flask(__name__)

# Homepage - shows the chat UI
@app.route("/")
def home():
    return render_template("index.html")  # Render the chat UI

# Chat API - called by the frontend
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"]
    user_id = data.get("user_id", "web_user")  # Default to "web_user" if user_id is not provided
    
    try:
        # Detect language of the message
        lang = detect_language(message)
        
        # Get reply from Pate (using Cohere API)
        reply = ask_pate(message, user_id, language=lang)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": f"Error processing message: {e}"}), 500

# Progress tracking endpoint (optional)
@app.route("/progress", methods=["POST"])
def progress():
    data = request.json
    user_id = data.get("user_id", "web_user")  # Default to "web_user" if user_id is not provided
    
    try:
        # Get the user's progress
        progress = get_progress(user_id)
        return jsonify({"progress": progress})
    except Exception as e:
        return jsonify({"error": f"Error retrieving progress: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
