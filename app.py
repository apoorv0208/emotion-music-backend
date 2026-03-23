from flask import Flask, request, make_response
from flask_cors import CORS
from routes.detect import detect_bp
import os
from dotenv import load_dotenv
from routes.instant import instant_bp
from routes.auth import auth_bp
from routes.music import music_bp

load_dotenv()

app = Flask(__name__)

# ✅ Restrict CORS to frontend only
CORS(app, resources={r"/*": {"origins": "*"}})
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = make_response()
        res.headers.add('Access-Control-Allow-Origin', '*')
        res.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        res.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        return res, 200
app.register_blueprint(instant_bp)
app.register_blueprint(detect_bp, url_prefix='/api/detect')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(music_bp, url_prefix='/api/music')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)