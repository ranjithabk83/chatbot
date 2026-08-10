from flask import Flask, render_template, request, jsonify
import os
import sqlite3
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_response TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_chat(user, bot):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO chats (user_message, bot_response) VALUES (?, ?)", (user, bot))
    conn.commit()
    conn.close()

def get_chats():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT id, user_message, bot_response FROM chats ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data

# ---------------- MEMORY ----------------
chat_history = []

# ---------------- ROUTES ----------------

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")

    chat_history.append({"role": "user", "content": user_input})

    system_prompt = {
        "role": "system",
        "content": """
You are a friendly AI assistant like ChatGPT.

Rules:
- Talk naturally 😊
- No markdown symbols (** ###)
- If user says "mini" → short answer
- If user says "detailed" → full answer
- Be friendly and clear
"""
    }

    messages = [system_prompt] + chat_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    reply = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": reply})

    # ✅ SAVE TO DB
    save_chat(user_input, reply)

    return jsonify({"response": reply})


@app.route("/history")
def history():
    return jsonify(get_chats())


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)