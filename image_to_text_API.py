import os
import pytesseract
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
from google import genai
from google.genai.types import Part
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import tempfile

# === Configuration ===
load_dotenv()
app = Flask(__name__, static_folder=".")

# Initialiser Gemini
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# === Route principale pour servir ton fichier HTML ===
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# === Route OCR avec Tesseract ===
@app.route("/ocr-tesseract", methods=["POST"])
def ocr_tesseract():
    try:
        if "image" not in request.files:
            return jsonify({"error": "Aucune image reçue"}), 400

        image_file = request.files["image"]
        language = request.form.get("language", "eng")

        # Enregistrer temporairement l'image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            image_path = tmp.name
            image_file.save(image_path)

        # OCR avec Tesseract
        text = pytesseract.image_to_string(Image.open(image_path), lang=language)

        # Statistiques simples
        word_count = len(text.split())
        confidence = 90  # Valeur indicative

        os.remove(image_path)
        return jsonify({
            "text": text,
            "word_count": word_count,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Route OCR avec Gemini Vision ===
@app.route("/ocr-gemini", methods=["POST"])
def ocr_gemini():
    try:
        if "image" not in request.files:
            return jsonify({"error": "Aucune image reçue"}), 400

        image_file = request.files["image"]
        mime_type = image_file.mimetype or "image/png"
        mode = request.form.get("mode", "text")
        image_bytes = image_file.read()

        # Préparer le prompt selon le mode choisi
        if mode == "structured":
            prompt = "Extract and format all text in JSON (with keys and values)."
        elif mode == "translate":
            prompt = "Extract all text and translate it into French."
        elif mode == "describe":
            prompt = "Describe in detail what you see in this image."
        else:
            prompt = "Extract all readable text from this image."

        image_part = Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=[prompt, image_part]
        )

        # Extraire le texte de la réponse
        text = response.candidates[0].content.parts[0].text
        word_count = len(text.split())

        return jsonify({
            "text": text,
            "word_count": word_count
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Route Comparaison Tesseract vs Gemini ===
@app.route("/ocr-compare", methods=["POST"])
def ocr_compare():
    try:
        if "image" not in request.files:
            return jsonify({"error": "Aucune image reçue"}), 400

        image_file = request.files["image"]
        mime_type = image_file.mimetype or "image/png"

        # --- Tesseract ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            path = tmp.name
            image_file.save(path)
        text_tess = pytesseract.image_to_string(Image.open(path))
        word_tess = len(text_tess.split())
        os.remove(path)

        # --- Gemini ---
        image_bytes = image_file.read()
        image_part = Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=["Extract all readable text from this image.", image_part]
        )
        text_gem = response.candidates[0].content.parts[0].text
        word_gem = len(text_gem.split())

        return jsonify({
            "tesseract": {
                "text": text_tess,
                "word_count": word_tess
            },
            "gemini": {
                "text": text_gem,
                "word_count": word_gem
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
