from flask import Blueprint, jsonify
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
load_dotenv()

instant_bp = Blueprint("instant", __name__)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

@instant_bp.route("/instant", methods=["GET"])
def instant_music():
    random_queries = [
        "pop",
        "bollywood",
        "hip hop",
        "lofi",
        "rock",
        "edm",
        "indie",
        "party",
        "chill",
        "workout"
    ]

    query = random.choice(random_queries)

    results = sp.search(
        q=query,
        type="track",
        limit=30
    )

    tracks = []

    for item in results["tracks"]["items"]:
        tracks.append({
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "image": item["album"]["images"][0]["url"],
            "spotify_url": item["external_urls"]["spotify"],
            "track_id": item["id"]
        })

    return jsonify({
        "playlist": tracks
    })