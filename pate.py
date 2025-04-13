import os
import cohere
import sqlite3
import subprocess
import requests
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
from difflib import get_close_matches

# Initialize Cohere API
COHERE_API_KEY = "hXeSL5eDuVlwe3uSzfAUKWVi37guE05QppzkNvHd"
co = cohere.Client(COHERE_API_KEY)

DB_FILE = "pate_memory.db"

# Personalities
PERSONALITY_MODES = {
    "default": "A highly intelligent AI that provides detailed, accurate answers.",
    "friendly": "A warm and friendly AI that enjoys casual conversations.",
    "teacher": "An AI tutor that gives clear and structured explanations.",
    "romantic": "A flirty and affectionate AI.",
}
current_personality = "default"

# ----------------- DATABASE FUNCTIONS -----------------
def initialize_database():
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

def save_conversation(user_input, pate_response):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_input, pate_response) VALUES (?, ?)", (user_input, pate_response))
    conn.commit()
    conn.close()

def get_related_memory(user_input):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, pate_response FROM conversations")
    past_convos = cursor.fetchall()
    conn.close()
    questions = [q for q, _ in past_convos]
    matches = get_close_matches(user_input, questions, n=1, cutoff=0.6)
    if matches:
        for q, r in past_convos:
            if q == matches[0]:
                return f"(From memory) {r}"
    return None

def save_progress(user_id, progress):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO user_progress (user_id, progress) VALUES (?, ?)", (user_id, progress))
    conn.commit()
    conn.close()

def get_progress(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT progress FROM user_progress WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "No progress found."

# ----------------- LANGUAGE & TRANSLATION -----------------
def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

def translate_text(text, target_lang="en"):
    source_lang = detect_language(text)
    if source_lang != target_lang:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    return text

# ----------------- FALLBACK INTERNET SCRAPER -----------------
def web_fallback_search(query):
    try:
        response = requests.get(f"https://www.google.com/search?q={query}", headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        snippets = soup.select("div.BNeawe.s3v9rd.AP7Wnd")
        return snippets[0].text if snippets else "No useful results found."
    except Exception as e:
        return f"Web error: {e}"

# ----------------- MAIN CHAT FUNCTION -----------------
def ask_pate(question, user_id, language="en"):
    # Hardcoded identity
    if "who created you" in question.lower():
        return "I was created by IntelliBotics."

    translated_question = translate_text(question, "en")

    # Check memory first
    memory_response = get_related_memory(translated_question)
    if memory_response:
        return translate_text(memory_response, language)

    # Build AI prompt
    prompt = f"""{PERSONALITY_MODES[current_personality]}\nUser: {translated_question}\nPate:"""

    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            stop_sequences=["User:"],
        )
        pate_reply = response.generations[0].text.strip() if response.generations else None
    except cohere.errors.UnauthorizedError:
        return "Error: Invalid Cohere API key."
    except Exception as e:
        pate_reply = f"Error: {str(e)}"

    # Web fallback if blank or poor answer
    if not pate_reply or "I don't know" in pate_reply:
        pate_reply = web_fallback_search(translated_question)

    save_conversation(question, pate_reply)
    return translate_text(pate_reply, language)

# ----------------- INTERFACE -----------------
if __name__ == "__main__":
    initialize_database()
    print("Pate is ready! Type 'exit' to quit.")

    user_id = "unique_user_123"

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if user_input.startswith("/search "):
            query = user_input.split("/search ", 1)[1]
            print("Pate:", web_fallback_search(query))
            continue

        if user_input.startswith("/progress"):
            print("Your Progress:", get_progress(user_id))
            continue

        language = detect_language(user_input)
        answer = ask_pate(user_input, user_id, language)
        print("Pate:", answer)
