from flask import Flask, request, render_template, redirect, url_for, flash
import requests
import os
import json
import cv2
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

API_KEY = 'AIzaSyA-cmhj7csz3zXyXkcJeK-Y8I7o7DVgW_M'
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=' + API_KEY

def load_profiles():
    if os.path.exists('profiles.json'):
        try:
            with open('profiles.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_profiles(profiles):
    with open('profiles.json', 'w') as f:
        json.dump(profiles, f)

@app.route('/', methods=['GET', 'POST'])
def home():
    profiles = load_profiles()
    if request.method == 'POST':
        profile_name = request.form.get('profile')
        file = request.files.get('file')
        if not profile_name:
            flash('Por favor, selecione um perfil.')
            return redirect(url_for('home'))
        if not file:
            flash('Por favor, faça o upload de um arquivo.')
            return redirect(url_for('home'))
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                caption = generate_caption_image(filepath, profiles.get(profile_name, ""))
            elif file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
                caption = generate_caption_video(filepath, profiles.get(profile_name, ""))
            else:
                flash('Formato de arquivo não suportado.')
                return redirect(url_for('home'))
            return render_template('results.html', caption=caption, file_url=filepath)
    return render_template('index.html', profiles=profiles)

def generate_caption_image(image_path, profile_description):
    img = Image.open(image_path)
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "contents": [{
            "parts": [{
                "text": f"Crie uma legenda de Instagram para minha imagem. {profile_description}"
            }]
        }]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raises exception for bad status codes
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            parts = result['candidates'][0]['content']['parts']
            caption_text = "\n".join(part['text'] for part in parts)
            return caption_text
        else:
            print("Resposta inesperada da API:", result)
            return "Erro ao gerar legenda: formato de resposta inesperado"
    except requests.exceptions.RequestException as e:
        print("Erro na requisição para a API:", e)
        return "Erro ao gerar legenda"

def generate_caption_video(video_path, profile_description):
    # Extrair um frame do vídeo
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        return "Erro ao processar o vídeo"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'frame.jpg')
    cv2.imwrite(image_path, frame)
    cap.release()
    return generate_caption_image(image_path, profile_description)

@app.route('/add_profile', methods=['GET', 'POST'])
def add_profile():
    if request.method == 'POST':
        profile_name = request.form['profile_name']
        profile_description = request.form['profile_description']
        profiles = load_profiles()
        profiles[profile_name] = profile_description
        save_profiles(profiles)
        flash('Perfil adicionado com sucesso!')
        return redirect(url_for('home'))
    return render_template('add_profile.html')

@app.route('/edit_profile/<profile_name>', methods=['GET', 'POST'])
def edit_profile(profile_name):
    profiles = load_profiles()
    if request.method == 'POST':
        profile_description = request.form['profile_description']
        profiles[profile_name] = profile_description
        save_profiles(profiles)
        flash('Perfil atualizado com sucesso!')
        return redirect(url_for('home'))
    return render_template('edit_profile.html', profile_name=profile_name, profile_description=profiles.get(profile_name, ""))

@app.route('/delete_profile/<profile_name>', methods=['POST'])
def delete_profile(profile_name):
    profiles = load_profiles()
    if profile_name in profiles:
        del profiles[profile_name]
        save_profiles(profiles)
        flash('Perfil excluído com sucesso!')
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
