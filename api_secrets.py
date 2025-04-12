
#
# from flask import Flask, request, jsonify, render_template
# import requests
# import time
# import os
# from werkzeug.utils import secure_filename
# from transformers import MarianMTModel, MarianTokenizer
# from api_secrets import API_KEY_ASSEMBLYAI
#
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#
# upload_endpoint = 'https://api.assemblyai.com/v2/upload'
# transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
# headers = {'authorization': API_KEY_ASSEMBLYAI}
#
# # Load MarianMT model for English to French translation
# model_name = "./models/opus-mt-en-fr"
# tokenizer = MarianTokenizer.from_pretrained(model_name)
# model = MarianMTModel.from_pretrained(model_name)
#
# def read_file(filename, chunk_size=5242880):
#     with open(filename, 'rb') as _file:
#         while True:
#             data = _file.read(chunk_size)
#             if not data:
#                 break
#             yield data
#
# def upload_to_assemblyai(filepath):
#     response = requests.post(
#         upload_endpoint,
#         headers=headers,
#         data=read_file(filepath)
#     )
#     return response.json().get('upload_url')
#
# def request_transcription(audio_url):
#     transcript_request = {"audio_url": audio_url}
#     response = requests.post(
#         transcript_endpoint,
#         json=transcript_request,
#         headers=headers
#     )
#     return response.json().get('id')
#
# def poll_transcription(transcript_id):
#     polling_endpoint = f"{transcript_endpoint}/{transcript_id}"
#     while True:
#         response = requests.get(polling_endpoint, headers=headers)
#         data = response.json()
#         if data['status'] == 'completed':
#             return data['text']
#         elif data['status'] == 'error':
#             return f"Error: {data['error']}"
#         time.sleep(30)
#
# # Function to translate text from English to French using MarianMT model
# def translate_text(text, target_language='jp'):
#     # Tokenize the text and translate
#     translated = model.generate(**tokenizer(text, return_tensors="pt", padding=True))
#     translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
#     return translated_text
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# @app.route('/upload', methods=['POST'])
# def upload():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file uploaded'}), 400
#
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
#
#     filename = secure_filename(file.filename)
#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     file.save(filepath)
#
#     try:
#         # Upload and transcribe the audio file
#         audio_url = upload_to_assemblyai(filepath)
#         transcript_id = request_transcription(audio_url)
#         transcription = poll_transcription(transcript_id)
#
#         # Translate the transcription to French using MarianMT
#         french_translation = translate_text(transcription, 'jp')
#
#         return jsonify({
#             'transcription': transcription,
#             'french_translation': french_translation
#         })
#
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         os.remove(filepath)
#
# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify, render_template
import requests
import time
import os
from werkzeug.utils import secure_filename
from transformers import MarianMTModel, MarianTokenizer
from api_secrets import API_KEY_ASSEMBLYAI

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization': API_KEY_ASSEMBLYAI}

# Mapping of supported languages to MarianMT model names (French and Japanese only)
LANGUAGE_MODELS = {
    'fr': "./models/opus-mt-en-fr",  # French model
    'ja': "./models/opus-mt-en-jap",  # Japanese model
    'hi': "./models/opus-mt-en-hi"
}


def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data


def upload_to_assemblyai(filepath):
    response = requests.post(
        upload_endpoint,
        headers=headers,
        data=read_file(filepath)
    )

    return response.json().get('upload_url')


def request_transcription(audio_url):
    transcript_request = {"audio_url": audio_url}
    response = requests.post(
        transcript_endpoint,
        json=transcript_request,
        headers=headers
    )
    return response.json().get('id')


def poll_transcription(transcript_id):
    polling_endpoint = f"{transcript_endpoint}/{transcript_id}"
    while True:
        response = requests.get(polling_endpoint, headers=headers)
        data = response.json()
        if data['status'] == 'completed':
            return data['text']
        elif data['status'] == 'error':
            return f"Error: {data['error']}"
        time.sleep(30)


# Function to translate text using MarianMT model
def translate_text(text, target_language='fr'):
    # Check if the target language is supported

    if target_language not in LANGUAGE_MODELS:
        return f"Error: Language '{target_language}' is not supported."

    model_name = LANGUAGE_MODELS[target_language]
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    # Tokenize the text and translate
    translated = model.generate(**tokenizer(text, return_tensors="pt", padding=True))
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return translated_text


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get the target language from the request (default is French)
    target_language = request.form.get('language', 'fr')

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Upload and transcribe the audio file
        audio_url = upload_to_assemblyai(filepath)
        transcript_id = request_transcription(audio_url)
        transcription = poll_transcription(transcript_id)

        # Translate the transcription to the selected language
        translation = translate_text(transcription, target_language)

        return jsonify({
            'transcription': transcription,
            'translation': translation
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(filepath)


if __name__ == '__main__':
    app.run(debug=True)

