import os
import requests

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"

    print("CLIENT ID:", SPOTIFY_CLIENT_ID)
    print("CLIENT SECRET:", SPOTIFY_CLIENT_SECRET)

    response = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    print("Token status:", response.status_code)
    print("Token response:", response.text)

    if response.status_code != 200:
        return None

    return response.json().get("access_token")


def get_tracks_by_emotion(emotion):
    token = get_spotify_token()
    if not token:
        return []

    emotion_query_map = {
        "happy": "happy upbeat pop songs",
        "sad": "sad emotional acoustic songs",
        "angry": "hard rock metal songs",
        "neutral": "lofi chill relaxing songs",
        "surprise": "party dance hits",
        "no face": "top global hits"
    }
    query = emotion_query_map.get(emotion.lower(), "trending music")

    search_url = "https://api.spotify.com/v1/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": query,
        "type": "track",
        "limit": 20,
        "market": "IN"
    }

    response = requests.get(search_url, headers=headers, params=params)

    print("Spotify search query:", query)
    print("Search response:", response.status_code)
    print(response.text[:500])
    if response.status_code != 200:
        return []

    data = response.json()

    tracks = []

    for item in data["tracks"]["items"]:
        tracks.append({
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "image": item["album"]["images"][0]["url"] if item["album"]["images"] else "",
            "external_url": item["external_urls"]["spotify"],
            "track_id": item["id"]   # ✅ ADD THIS
        })

    return tracks