from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import jwt
import datetime
import os

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Connect to MongoDB (Make sure your local MongoDB server is running!)
# If you are using MongoDB Atlas, replace this URI with your cloud connection string.
client = MongoClient(os.getenv("MONGODBPASS"))
db = client['emotion_music']
users_collection = db['users']

# Secret key for generating JWT tokens (keep this safe in a real app!)
SECRET_KEY = os.environ.get("JWT_SECRET", "my_super_secret_dev_key")

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. Check if user already exists
    if users_collection.find_one({"email": data.get('email')}):
        return jsonify({"error": "User with this email already exists"}), 400

    # 2. Hash the password for security
    hashed_password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    
    # 3. Create the new user profile (Notice 'languages' is expecting a list)
    new_user = {
        "name": data.get('name'),
        "email": data.get('email'),
        "password": hashed_password,
        "age": data.get('age'),
        "languages": data.get('languages', []) # defaults to empty list if none provided
    }
    
    # 4. Save to MongoDB
    users_collection.insert_one(new_user)
    return jsonify({"message": "User registered successfully!"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Find the user by email
    user = users_collection.find_one({"email": data.get('email')})
    
    # 2. Check if user exists AND password is correct
    if user and bcrypt.check_password_hash(user['password'], data.get('password')):
        
        # 3. Generate a JWT Token valid for 24 hours
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        # 4. Send back the token and the user's data (including their languages)
        return jsonify({
            "token": token,
            "user": {
                "name": user['name'],
                "email": user['email'],
                "age": user['age'],
                "languages": user.get('languages', [])
            }
        }), 200
        
    # If email or password was wrong:
    return jsonify({"error": "Invalid email or password"}), 401