import os
import cohere
import sqlite3
import subprocess
from langdetect import detect
from deep_translator import GoogleTranslator

# Initialize Cohere API
COHERE_API_KEY = "hXeSL5eDuVlwe3uSzfAUKWVi37guE05QppzkNvHd"  # 🔹 Replace with your working API key
co = cohere.Client(COHERE_API_KEY)

# Database setup
DB_FILE = "pate_memory.db"

# Personality settings
PERSONALITY_MODES = {
    "default": "A highly intelligent AI that provides detailed, accurate answers.",
    "friendly": "A warm and friendly AI that enjoys casual conversations.",
    "teacher": "An AI tutor that gives clear and structured explanations.",
    "romantic": "A flirty and affectionate AI.",
}

current_personality = "default"

# ----------------- DATABASE FUNCTIONS -----------------
def initialize_database():
    """Creates the necessary tables if they don’t exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            user_input TEXT,
            pate_response TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_learning (
            topic TEXT,
            details TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id TEXT PRIMARY KEY,
            progress TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_progress(user_id, progress):
    """Saves the user's learning progress."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO user_progress (user_id, progress) VALUES (?, ?)", (user_id, progress))
    conn.commit()
    conn.close()

def get_progress(user_id):
    """Retrieves the user's learning progress."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT progress FROM user_progress WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "No progress found."

# ----------------- WEB SEARCH FUNCTION -----------------
def search(query):
    """Runs a web search."""
    try:
        result = subprocess.run(["search", query], capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else "No results found."
    except Exception as e:
        return f"Error: {e}"

# ----------------- AI CHAT FUNCTIONS -----------------
def detect_language(text):
    """Detects the language of the input text."""
    try:
        return detect(text)
    except:
        return "en"  # Default to English if detection fails

def translate_text(text, target_lang="en"):
    """Translates text to the target language."""
    source_lang = detect_language(text)
    if source_lang != target_lang:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    return text

def ask_pate(question, user_id, language="en"):
    """Ask Pate a question and get an AI-generated response."""
    # Special case for questions about Pate's creation
    if "who created you" in question.lower() or "who made you" in question.lower():
        return "I was created by IntelliBotics."

    translated_question = translate_text(question, "en")  # Translate to English for processing
    prompt = f"""
    {PERSONALITY_MODES[current_personality]}
    User: {translated_question}
    Pate:
    """
    
    try:
        # Generate response from Cohere API
        response = co.generate(
            model="command-r-plus",  # Ensure the correct model is being used
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            stop_sequences=["User:"],
        )
        
        if response and response.generations:
            pate_reply = response.generations[0].text.strip()
        else:
            pate_reply = "Sorry, I couldn't generate a response. Please try again."
    
    except cohere.errors.UnauthorizedError:
        return "Error: Invalid Cohere API key! Please update it in the script."
    except Exception as e:
        pate_reply = f"Error: {str(e)}"
    
    # If AI doesn't know, use web search as fallback
    if not pate_reply or "I don't know" in pate_reply:
        pate_reply = "Sorry, I couldn't find an answer. Let me try again."
    
    # Save conversation history
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_input, pate_response) VALUES (?, ?)", (question, pate_reply))
    conn.commit()
    conn.close()

    # Translate the response back to the user's language
    return translate_text(pate_reply, language)

# ----------------- CHATBOT INTERFACE -----------------
if __name__ == "__main__":
    initialize_database()  # Ensure database is set up
    print("Pate is ready! Type 'exit' to quit.")

    user_id = "unique_user_123"  # Replace with actual user tracking system

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if user_input.startswith("/search "):
            query = user_input.split("/search ")[1]
            print("Pate:", search(query))
            continue

        if user_input.startswith("/progress"):
            print("Your Progress:", get_progress(user_id))
            continue

        language = detect_language(user_input)
        answer = ask_pate(user_input, user_id, language)
        print("Pate:", answer)
