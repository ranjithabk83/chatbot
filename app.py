from flask import Flask, render_template, request, jsonify
import os
import sqlite3
import PyPDF2
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

load_dotenv()

app = Flask(__name__)

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
    c.execute("SELECT user_message, bot_response FROM chats ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data

# ---------------- AI ----------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found!")

client = Groq(api_key=api_key)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pdf_sentences = []

def read_pdf(path):
    text = ""
    with open(path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t
    return text

def process_pdf(path):
    global pdf_sentences
    text = read_pdf(path)
    pdf_sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]

def format_response(text):
    parts = text.split(". ")
    result = ""

    if len(parts) > 0:
        result += f"📌 <b>Overview:</b><br>{parts[0]}.<br><br>"

    if len(parts) > 1:
        result += "🔹 <b>Key Points:</b><br>"
        for p in parts[1:4]:
            result += f"✔ {p}.<br>"
        result += "<br>"

    if len(parts) > 4:
        result += "💡 <b>Extra:</b><br>"
        for p in parts[4:]:
            result += f"- {p}.<br>"

    return result

# ---------------- ROUTES ----------------

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")

    if pdf_sentences:
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(pdf_sentences + [user_input])

        similarity = cosine_similarity(vectors[-1], vectors[:-1])
        index = similarity.argmax()

        response = pdf_sentences[index]

    else:
        prompt = f"""
        Answer clearly using structured format.

        Question: {user_input}
        """

        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )

        response = chat.choices[0].message.content

    formatted = format_response(response)

    # ✅ SAVE TO DATABASE
    save_chat(user_input, formatted)

    return jsonify({"response": formatted})

# GET CHAT HISTORY FROM DB
@app.route("/history")
def history():
    chats = get_chats()
    return jsonify(chats)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)