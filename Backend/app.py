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
    

@app.route("/grocery-items", methods=["GET"])
def get_grocery_items():
    start_time = time.time()
    try:
        # Fetch real data from Open Food Facts API
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "action": "process",
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": "groceries",  # Broad category; adjust as needed (e.g., "snacks", "beverages")
            "json": 1,
            "page_size": 10,  # Limit to 10 items
            "fields": "product_name,generic_name,categories_tags,nutriscore_grade"  # Relevant fields
        }
        headers = {"User-Agent": "GroceryElegance - Python - Version 1.0"}  # Required by Open Food Facts
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse Open Food Facts response
        data = response.json()
        items = []
        for product in data.get("products", [])[:10]:  # Ensure we get up to 10 items
            name = product.get("product_name", "Unknown Product")
            if not name:  # Skip if no name
                continue
            item = {
                "name": name,
                "category": product.get("generic_name", "Miscellaneous"),
                "tags": product.get("categories_tags", []),
                "price": 1.00  # Dummy price; Open Food Facts doesn’t provide this
            }
            items.append(item)
        
        if not items:
            raise Exception("No valid grocery items found in API response")
        
        # Log success and cache in Firebase
        db.collection("api_logs").add({"endpoint": "grocery-items", "status": "success", "time": time.time() - start_time})
        db.collection("grocery_cache").document("latest").set({"items": items, "timestamp": firestore.SERVER_TIMESTAMP})
        return jsonify({"items": items}), 200
    except Exception as e:
        db.collection("api_logs").add({"endpoint": "grocery-items", "status": "error", "time": time.time() - start_time, "error": str(e)})
        # Fallback to cached data if available
        cached = db.collection("grocery_cache").document("latest").get().to_dict()
        if cached and "items" in cached:
            return jsonify(cached), 200
        return jsonify({"error": str(e)}), 500

@app.route("/daily-offers", methods=["GET"])
def get_daily_offers():
    start_time = time.time()
    try:
        # Simulate offers with Open Food Facts data, since Flipp API key is unavailable
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "action": "process",
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": "snacks",  # Example category; we will change down the road
            "json": 1,
            "page_size": 5,  # Limit to 5 offers
            "fields": "product_name"
        }
        headers = {"User-Agent": "GroceryElegance - Python - Version 1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse response and create mock offers
        data = response.json()
        offers = []
        for product in data.get("products", [])[:5]:
            name = product.get("product_name", "Unknown Product")
            if not name:
                continue
            offers.append({
                "name": name,
                "original": 1.00,  # Dummy original price (Need to chage in future)
                "sale": 0.75     # Dummy sale price (25% off)
            })
        
        if not offers:
            raise Exception("No valid offer items found in API response")
        
        # Log success and cache in Firebase
        db.collection("offers_cache").document("latest").set({"offers": offers, "timestamp": firestore.SERVER_TIMESTAMP})
        db.collection("api_logs").add({"endpoint": "daily-offers", "status": "success", "time": time.time() - start_time})
        return jsonify({"offers": offers}), 200
    except Exception as e:
        db.collection("api_logs").add({"endpoint": "daily-offers", "status": "error", "time": time.time() - start_time, "error": str(e)})
        # Fallback to cached data
        cached = db.collection("offers_cache").document("latest").get().to_dict()
        if cached and "offers" in cached:
            return jsonify(cached), 200
        return jsonify({"error": str(e)}), 500


@app.route("/meal-recommendations", methods=["POST"])
def get_meal_recommendations():
    start_time = time.time()
    cart_items = request.json.get("cart_items", [])
    try:
        if not cart_items:
            meals = []
        elif not SPOONACULAR_API_KEY:
            # Fallback to dummy data if API key is missing
            meals = [
                {"meal": f"{cart_items[0]} Stew", "ingredients": cart_items},
                {"meal": f"{cart_items[0]} Salad", "ingredients": cart_items[:2]},
                {"meal": f"{cart_items[0]} Stir-Fry", "ingredients": cart_items}
            ]
        else:
            # Real Spoonacular API call
            ingredients = ",".join(cart_items)
            url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&number=3&apiKey={SPOONACULAR_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad status codes
            recipes = response.json()
            meals = [
                {
                    "meal": recipe["title"],
                    "ingredients": [ing["name"] for ing in recipe["usedIngredients"] + recipe["missedIngredients"]]
                }
                for recipe in recipes
            ]

        if db:
            # Use set with merge=True to create or update the document
            db.collection("users").document("dummy_user").set({"recommendations": meals}, merge=True)
            db.collection("api_logs").add({"endpoint": "meal-recommendations", "status": "success", "time": time.time() - start_time})
        return jsonify({"meals": meals[:3]}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({"endpoint": "meal-recommendations", "status": "error", "time": time.time() - start_time})
        return jsonify({"error": str(e)}), 500


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
<<<<<<< HEAD
        return jsonify({"error": "Invalid email or password"}), 401
    
@app.route("/profile/update", methods=["POST"])
def update_profile():
    userId = request.json.get("userId")
    name = request.json.get("name")
    avatarUrl = request.json.get("avatarUrl", "https://default-avatar.com")
    try:
        db.collection("users").document(userId).update({"name": name, "avatarUrl": avatarUrl})
        return jsonify({"message": "Profile updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def verify_token(token):
    try:
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except:
        return None

=======
        return jsonify({"error": "Invalid email or password"}), 401
>>>>>>> 8edab77372e8535378d15005f3d0ef99d002251a
