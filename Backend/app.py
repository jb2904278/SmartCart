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

# Get Spoonacular API key from environment
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
if not SPOONACULAR_API_KEY:
    print("Warning: SPOONACULAR_API_KEY not set in .env, using dummy data")

# Dummy data for APIs (to simulate when real APIs are unavailable)
DUMMY_GROCERY_ITEMS = [
    {"name": "Tomato", "category": "vegetable", "tags": ["vegan", "gluten-free"]},
    {"name": "Apple", "category": "fruit", "tags": ["vegan", "gluten-free", "nut-free"]},
    {"name": "Bread", "category": "bakery", "tags": ["vegan"]},
    {"name": "Chicken", "category": "meat", "tags": []},
    {"name": "Pasta", "category": "grain", "tags": ["gluten-free"]}
]
 
@app.route("/test-apis", methods=["GET"])
def test_apis():
    try:
        # Test Open Food Facts API
        open_food_response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/737628064502.json").json()
        # Test Flipp API (mocked as it requires auth; using dummy data)
        flipp_response = {"offers": [{"name": "Apple", "original": 1.00, "sale": 0.75}]}
        # Test Spoonacular API (using free tier key, replace with your own)
        spoonacular_response = requests.get(f"https://api.spoonacular.com/recipes/findByIngredients?ingredients=apple&apiKey={SPOONACULAR_API_KEY}").json()
        
        db.collection("api_tests").add({
            "open_food": open_food_response.get("product", {}).get("product_name", "N/A"),
            "flipp": flipp_response["offers"][0],
            "spoonacular": spoonacular_response[0]["title"] if spoonacular_response else "N/A",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return jsonify({"status": "success", "message": "APIs tested"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
