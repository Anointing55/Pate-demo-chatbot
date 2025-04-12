from flask import Flask, request, jsonify, render_template

# Move the import inside the function to avoid circular imports
def init_pate():
    from pate import pate
    pate.initialize_database()

app = Flask(__name__)

# Initialize database when the app starts
init_pate()

# Homepage - shows the chat UI
@app.route("/")
def home():
    return render_template("index.html")

# Chat API - called by the frontend
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"]
    user_id = data.get("user_id", "web_user")
    lang = pate.detect_language(message)

    reply = pate.ask_pate(message, user_id, language=lang)
    return jsonify({"reply": reply})

# Progress tracking endpoint (optional)
@app.route("/progress", methods=["POST"])
def progress():
    data = request.json
    user_id = data.get("user_id", "web_user")
    return jsonify({"progress": pate.get_progress(user_id)})

if __name__ == "__main__":
    app.run(debug=True)
