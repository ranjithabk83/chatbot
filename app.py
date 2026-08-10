from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

# ✅ AI CLIENT
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ CHAT ROUTE
@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")

    # 🔥 SMART PROMPT (THIS IS THE MAGIC)
    prompt = f"""
You are a friendly AI assistant like ChatGPT.

Rules:
- Talk in a natural, friendly tone
- No markdown symbols (** ### etc)
- Keep answers clean and readable
- If user says "mini", give short answer
- If user says "detailed", give full explanation
- Always format nicely with simple paragraphs or bullet points
- Avoid symbols like *** or ###

User message:
{user_input}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response.choices[0].message.content

    return jsonify({"response": reply})


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)