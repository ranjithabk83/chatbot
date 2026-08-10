from flask import Flask, render_template, request, jsonify
import os
import PyPDF2
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

# Load env

load_dotenv()

app = Flask(**name**)

# API Key

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
raise ValueError("GROQ_API_KEY not found!")

client = Groq(api_key=api_key)

# Upload folder

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
os.makedirs(UPLOAD_FOLDER)

pdf_sentences = []

# Read PDF

def read_pdf(path):
text = ""
with open(path, "rb") as file:
reader = PyPDF2.PdfReader(file)
for page in reader.pages:
t = page.extract_text()
if t:
text += t
return text

# Process PDF

def process_pdf(path):
global pdf_sentences
text = read_pdf(path)
pdf_sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]

# Format response

def format_response(text):
parts = text.split(". ")
result = ""

```
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
```

# Chat API

@app.route("/ask", methods=["POST"])
def ask():
user_input = request.json.get("message")

```
if pdf_sentences:
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(pdf_sentences + [user_input])

    similarity = cosine_similarity(vectors[-1], vectors[:-1])
    index = similarity.argmax()

    response = pdf_sentences[index]

else:
    prompt = f"""
    Answer clearly using structured format.

    Rules:
    - Use headings
    - Use bullet points
    - Keep it short

    Question: {user_input}
    """

    chat = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    response = chat.choices[0].message.content

return jsonify({"response": format_response(response)})
```

# Upload

@app.route("/upload", methods=["POST"])
def upload():
file = request.files.get("file")

```
if not file:
    return jsonify({"error": "No file"}), 400

path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
file.save(path)

process_pdf(path)

return jsonify({"message": "PDF uploaded successfully"})
```

@app.route("/")
def home():
return render_template("index.html")

if **name** == "**main**":
app.run(debug=True)
