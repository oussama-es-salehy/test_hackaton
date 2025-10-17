from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
ELEVENLABS_API_KEY = "f64339ffe9b62d741994a567fe09866e2fdf0ec5875a12aad700410f91e4129b"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'webm', 'mp4'}

# Créer le dossier uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil de l'API"""
    return jsonify({
        'service': 'ElevenLabs Speech-to-Text API',
        'version': '1.0',
        'endpoints': {
            '/health': 'Vérifier l\'état de l\'API',
            '/transcribe': 'POST - Transcrire un fichier audio',
            '/transcribe-url': 'POST - Transcrire depuis une URL'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Vérifier l'état de l'API"""
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(ELEVENLABS_API_KEY)
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcrire un fichier audio avec ElevenLabs
    
    Body (multipart/form-data):
    - audio: fichier audio (required)
    - language: code langue (optional, ex: 'fr', 'en')
    """
    
    # Vérifier si un fichier est présent
    if 'audio' not in request.files:
        return jsonify({'error': 'Aucun fichier audio fourni'}), 400
    
    file = request.files['audio']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Format non supporté. Formats acceptés: {ALLOWED_EXTENSIONS}'
        }), 400
    
    try:
        # Sauvegarder temporairement
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Préparer les paramètres
        language = request.form.get('language', None)
        
        # Envoyer à ElevenLabs
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        with open(filepath, "rb") as audio_file:
            files = {
                "file": audio_file
            }
            data = {
                "model_id": "scribe_v1"
            }
            
            if language:
                data['language_code'] = language
            
            print(f"📤 Envoi vers ElevenLabs: {filename}")
            response = requests.post(url, headers=headers, files=files, data=data)
        
        # Supprimer le fichier temporaire
        os.remove(filepath)
        
        # Traiter la réponse
        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "")
            
            print(f"✅ Transcription réussie: {len(text)} caractères")
            
            return jsonify({
                'success': True,
                'text': text,
                'language': language,
                'model': 'scribe_v1'
            })
        else:
            print(f"❌ Erreur ElevenLabs: {response.status_code}")
            return jsonify({
                'error': 'Erreur ElevenLabs',
                'status_code': response.status_code,
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        # Nettoyer en cas d'erreur
        if os.path.exists(filepath):
            os.remove(filepath)
        
        print(f"❌ Erreur: {str(e)}")
        return jsonify({
            'error': 'Erreur lors du traitement',
            'details': str(e)
        }), 500

@app.route('/transcribe-url', methods=['POST'])
def transcribe_url():
    """
    Transcrire un audio depuis une URL
    
    Body (JSON):
    {
        "url": "https://example.com/audio.mp3",
        "language": "fr" (optional)
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL manquante'}), 400
    
    try:
        audio_url = data['url']
        language = data.get('language', None)
        
        # Télécharger l'audio
        print(f"📥 Téléchargement: {audio_url}")
        audio_response = requests.get(audio_url)
        
        if audio_response.status_code != 200:
            return jsonify({'error': 'Impossible de télécharger l\'audio'}), 400
        
        # Sauvegarder temporairement
        filename = 'temp_audio.mp3'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_response.content)
        
        # Envoyer à ElevenLabs
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        with open(filepath, "rb") as audio_file:
            files = {
                "file": audio_file
            }
            params = {
                "model_id": "scribe_v1"
            }
            
            if language:
                params['language_code'] = language
            
            print(f"📤 Envoi vers ElevenLabs")
            response = requests.post(url, headers=headers, files=files, data=params)
        
        # Supprimer le fichier temporaire
        os.remove(filepath)
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "")
            
            print(f"✅ Transcription réussie: {len(text)} caractères")
            
            return jsonify({
                'success': True,
                'text': text,
                'language': language,
                'model': 'scribe_v1'
            })
        else:
            print(f"❌ Erreur ElevenLabs: {response.status_code}")
            return jsonify({
                'error': 'Erreur ElevenLabs',
                'status_code': response.status_code,
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        
        print(f"❌ Erreur: {str(e)}")
        return jsonify({
            'error': 'Erreur lors du traitement',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 API ElevenLabs Speech-to-Text")
    print("=" * 50)
    print(f"📍 URL: http://localhost:5000")
    print(f"🔑 Clé API: Configurée")
    print(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
    print("=" * 50)
    print("\n📚 Endpoints disponibles:")
    print("  GET  / - Documentation")
    print("  GET  /health - État de l'API")
    print("  POST /transcribe - Transcrire un fichier")
    print("  POST /transcribe-url - Transcrire depuis URL")
    print("\n✅ Serveur démarré!\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)