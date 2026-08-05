from flask import Flask, render_template, request, jsonify
import os
import PyPDF2
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

# 🔐 Load env
load_dotenv()

# ✅ Flask app
app = Flask(__name__)

# 🔑 API Key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file!")

client = Groq(api_key=api_key)

# 📁 Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 🧠 Store PDF content
pdf_sentences = []

# 📄 Read PDF
def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
    return text

# 🧠 Process PDF
def process_pdf(file_path):
    global pdf_sentences
    text = read_pdf(file_path)
    pdf_sentences = text.split(".")


# 🤖 Chat API
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
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": user_input}],
            model="llama-3.3-70b-versatile"
        )
        response = chat.choices[0].message.content

    return jsonify({"response": response})


# 📤 Upload API
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    process_pdf(path)

    return jsonify({"message": "PDF uploaded successfully"})


# 🌐 Home
@app.route("/")
def home():
    return render_template("index.html")


# ▶ Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)