from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import time
from dotenv import load_dotenv 
import os

app = Flask(__name__)

load_dotenv()

cred = credentials.Certificate("firebase_config.json")  
firebase_admin.initialize_app(cred)

try:
    db = firestore.client()
except Exception as e:
    print(f"Firestore initialization failed: {e}")
    db = None  

@app.route("/auth/signup", methods=["POST"])
def signup():
    email = request.json.get("email")
    password = request.json.get("password")
    try:
        user = auth.create_user(email=email, password=password)
        db.collection("users").document(user.uid).set({"name": "New User", "avatarUrl": "https://default-avatar.com"})
        return jsonify({"uid": user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/auth/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")
    try:
        
        user = {"uid": "dummy_user"}  
        return jsonify({"uid": user["uid"], "token": "mock_token"}), 200
    except Exception as e:
        return jsonify({"error": "Invalid email or password"}), 401
