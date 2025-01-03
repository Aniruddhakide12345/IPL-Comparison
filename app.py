from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import pandas as pd
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration for image uploads
UPLOAD_FOLDER = 'player_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database initialization
def init_db():
    conn = sqlite3.connect('cricket.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS players
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT UNIQUE,
         image_path TEXT)
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
init_db()

# Load player data from CSV
df = pd.read_csv(r'C:\Users\HP\OneDrive\Desktop\Coding\Projects\P2\batinfo(1).csv')
df['Player'] = df['Player'].str.lower()

@app.route('/upload_player_image', methods=['POST'])
def upload_player_image():
    if 'image' not in request.files or 'player_name' not in request.form:
        return jsonify({'error': 'No image or player name provided'}), 400
    
    file = request.files['image']
    player_name = request.form['player_name'].lower()
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{player_name}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = sqlite3.connect('cricket.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO players (name, image_path) VALUES (?, ?)',
                 (player_name, filepath))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Image uploaded successfully'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/player_image/<player_name>')
def get_player_image(player_name):
    conn = sqlite3.connect('cricket.db')
    c = conn.cursor()
    c.execute('SELECT image_path FROM players WHERE name = ?', (player_name.lower(),))
    result = c.fetchone()
    conn.close()
    
    if result and os.path.exists(result[0]):
        return send_file(result[0], mimetype='image/jpeg')
    else:
        return send_file('player_images/default.png', mimetype='image/jpeg')

@app.route('/players', methods=['GET'])
def get_all_players():
    try:
        conn = sqlite3.connect('cricket.db')
        c = conn.cursor()
        c.execute('SELECT name FROM players')
        players_with_images = {row[0] for row in c.fetchall()}
        conn.close()

        players = df['Player'].str.title().tolist()
        return jsonify(players)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Failed to fetch players list'}), 500

@app.route('/stats', methods=['POST'])
def get_player_stats():
    try:
        data = request.get_json()
        if 'name' not in data:
            return jsonify({'error': 'Please provide a player name'}), 400
        
        name = data['name'].lower()
        player = df[df['Player'] == name]
        
        if player.empty:
            return jsonify({'error': 'Player not found'}), 404
        
        stats = {
            'Matches': int(player.iloc[0]['Mat']),
            'Innings': int(player.iloc[0]['Inns']),
            'Runs': int(player.iloc[0]['Runs']),
            'Average': float(player.iloc[0]['Ave']),
            'Strike_Rate': float(player.iloc[0]['SR']),
            'Centuries': int(player.iloc[0]['100']),
            'Fifties': int(player.iloc[0]['50']),
            'Fours': int(player.iloc[0]['4s']),
            'Sixes': int(player.iloc[0]['6s'])
        }
        return jsonify(stats)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Failed to fetch player stats'}), 500

if __name__ == '__main__':
    app.run(debug=True)
