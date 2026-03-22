from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from ytmusicapi import YTMusic
from bson.objectid import ObjectId
import jwt
import os
import random
from functools import wraps

music_bp = Blueprint('music', __name__)
ytmusic = YTMusic()

client = MongoClient(os.getenv("MONGODBPASS"))
db = client['emotion_music']
users_collection = db['users']

SECRET_KEY = os.environ.get("JWT_SECRET", "my_super_secret_dev_key")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1] 
        if not token:
            return jsonify({'error': 'Token is missing! Please log in.'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = users_collection.find_one({'_id': ObjectId(data['user_id'])})
        except:
            return jsonify({'error': 'Token is invalid or expired!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# ==========================================
# 🎵 CORE RECOMMENDATION ENGINE
# ==========================================
@music_bp.route('/recommend', methods=['POST'])
@token_required
def recommend_music(current_user):
    data = request.get_json()
    detected_emotion = data.get('emotion')

    if not detected_emotion:
        return jsonify({"error": "No emotion provided"}), 400

    # 1. Get User Data
    age = int(current_user.get('age', 25))
    
    # 2. STRICT LANGUAGE FILTERING
    # We pull the exact array of languages they checked during Sign Up
    languages = current_user.get('languages', [])
    if not languages:
        languages = ['English'] # Fallback just in case

    # Pick a random language from their specific list so the playlist stays fresh!
    selected_language = random.choice(languages)

    # 3. Adjust Vibe by Age
    vibe = "modern hits"
    if age > 40:
        vibe = "classic retro hits"
    elif age > 30:
        vibe = "2000s popular hits"
    else:
        vibe = "trending hits"

    # 4. THE MAGIC QUERY
    # We add "Official Audio" to force YouTube to give us verified artist accounts
    search_query = f"{detected_emotion} {selected_language} {vibe} official audio"
    print(f"Searching YouTube Music for: {search_query}")

    try:
        # filter="songs" is the ultimate safeguard. It tells YouTube to ONLY 
        # return tracks from official Music catalog, ignoring user video uploads.
        search_results = ytmusic.search(search_query, filter="songs", limit=10)
        
        if not search_results:
            return jsonify({"error": "Could not find matching songs."}), 404

        playlist = []
        for song in search_results:
            # Double check that we actually got a playable videoId
            if song.get('videoId'):
                playlist.append({
                    "title": song.get('title'),
                    "artist": song['artists'][0]['name'] if song.get('artists') else "Unknown Artist",
                    "videoId": song.get('videoId'),
                    "thumbnail": song['thumbnails'][-1]['url'] if song.get('thumbnails') else None,
                    "language_used": selected_language # Tagging it so we know it worked
                })

        return jsonify({
            "message": "Playlist generated!",
            "playlist": playlist
        }), 200

    except Exception as e:
        print(f"YouTube Search Error: {e}")
        return jsonify({"error": "Failed to fetch music from YouTube."}), 500

# ==========================================
# ❤️ HISTORY MANAGEMENT (Add, Remove, Get)
# ==========================================
@music_bp.route('/history', methods=['GET', 'POST', 'DELETE'])
@token_required
def handle_history(current_user):
    if request.method == 'GET':
        history = current_user.get('history', [])
        saved_ids = [song.get('videoId') for song in history if isinstance(song, dict)]
        
        # CHANGED: We now return the full 'history' array alongside the IDs!
        return jsonify({
            "history": history, 
            "savedVideoIds": saved_ids
        }), 200
    
    if request.method == 'POST':
        data = request.get_json()
        song = data.get('song')
        if not song:
            return jsonify({"error": "No song provided"}), 400

        users_collection.update_one(
            {'_id': current_user['_id']},
            {'$addToSet': {'history': song}}
        )
        return jsonify({"message": "Song saved to history!"}), 200

    if request.method == 'DELETE':
        data = request.get_json()
        video_id = data.get('videoId')
        if not video_id:
            return jsonify({"error": "No videoId provided"}), 400

        users_collection.update_one(
            {'_id': current_user['_id']},
            {'$pull': {'history': {'videoId': video_id}}}
        )
        return jsonify({"message": "Song removed from history!"}), 200