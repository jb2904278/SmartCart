from flask import Flask, request, jsonify, g
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import time
from dotenv import load_dotenv 
import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import random

app = Flask(__name__)
CORS(app)

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


limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

def firebase_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header.split("Bearer ")[1]
        try:
            decoded_token = auth.verify_id_token(token)
            g.user = decoded_token
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated_function

 
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


@app.route("/api-logs", methods=["GET"])
def get_api_logs():
    logs = db.collection("api_logs").order_by("time", direction=firestore.Query.DESCENDING).limit(10).get()
    return jsonify([log.to_dict() for log in logs]), 200


@app.route("/auth/signup", methods=["POST"])
@firebase_auth
def signup():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    user_id = g.user["uid"]
    avatar_url = f"https://api.dicebear.com/9.x/pixel-art/svg?seed={user_id}"
    try:
        db.collection("profiles").document(user_id).set({
            "email": email,
            "name": name,
            "avatarUrl": avatar_url,
            "dietaryPrefs": {
                "vegan": False,
                "glutenFree": False,
                "nutFree": False,
                "organic": False,
                "nonGMO": False,
                "lowCarb": False,
                "highFiber": False,
                "lowSodium": False,
                "dairyFree": False,
                "keto": False,
                "paleo": False
            },
            "cart": []
        })
        if db:
            db.collection("api_logs").add({
                "endpoint": "auth/signup",
                "status": "success",
                "user_id": user_id,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"message": "User created", "userId": user_id}), 201
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "auth/signup",
                "status": "error",
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500


@app.route("/auth/login", methods=["POST"])
@limiter.limit("100/hour")
def login():
    try:
        data = request.json
        email = data.get("email")
        token = data.get("token")
        if not token:
            return jsonify({"error": "Token required"}), 401
        decoded = auth.verify_id_token(token)
        user = auth.get_user_by_email(email)
        if decoded["uid"] != user.uid:
            return jsonify({"error": "Invalid token"}), 401
        if db:
            db.collection("api_logs").add({
                "endpoint": "auth/login",
                "status": "success",
                "user_id": user.uid,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"uid": user.uid, "token": token}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "auth/login",
                "status": "error",
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": "Invalid email or token"}), 401



@app.route("/profile/update", methods=["POST"])
@firebase_auth
def update_profile():
    user_id = g.user["uid"]
    data = request.get_json()
    name = data.get("name")
    avatar_url = data.get("avatarUrl")
    dietary_prefs = data.get("dietaryPrefs", {
        "vegan": False,
        "glutenFree": False,
        "nutFree": False,
        "organic": False,
        "nonGMO": False,
        "lowCarb": False,
        "highFiber": False,
        "lowSodium": False,
        "dairyFree": False,
        "keto": False,
        "paleo": False
    })
    try:
        db.collection("profiles").document(user_id).update({
            "name": name,
            "avatarUrl": avatar_url,
            "dietaryPrefs": dietary_prefs
        })
        if db:
            db.collection("api_logs").add({
                "endpoint": "profile/update",
                "status": "success",
                "user_id": user_id,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"message": "Profile updated"}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "profile/update",
                "status": "error",
                "user_id": user_id,
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Update failed: {str(e)}"}), 500




@app.route("/profile/<userId>", methods=["GET"])
@firebase_auth
def get_profile(userId):
    if g.user["uid"] != userId:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        doc = db.collection("profiles").document(userId).get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200
        return jsonify({
            "email": g.user.get("email", ""),
            "name": g.user.get("email", "").split("@")[0],
            "avatarUrl": f"https://api.dicebear.com/9.x/pixel-art/svg?seed={userId}",
            "dietaryPrefs": {
                "vegan": False,
                "glutenFree": False,
                "nutFree": False,
                "organic": False,
                "nonGMO": False,
                "lowCarb": False,
                "highFiber": False,
                "lowSodium": False,
                "dairyFree": False,
                "keto": False,
                "paleo": False
            },
            "cart": []
        }), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "profile/<userId>",
                "status": "error",
                "user_id": userId,
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Error fetching profile: {str(e)}"}), 500


@app.route("/profile-logs", methods=["GET"])
def get_profile_logs():
    logs = db.collection("profile_logs").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
    return jsonify([log.to_dict() for log in logs]), 200

@app.route("/cart/add", methods=["POST"])
@firebase_auth
@limiter.limit("10 per minute")
def add_to_cart():
    user_id = g.user["uid"]
    item = request.get_json().get("item")
    if not item:
        return jsonify({"error": "Missing item in request"}), 400
    try:
        doc_ref = db.collection("profiles").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            cart = doc.to_dict().get("cart", [])
            item["price"] = float(item.get("price", 0))
            if "id" not in item:
                item["id"] = str(len(cart) + 1)
            item["quantity"] = item.get("quantity", 1)
            existing_item = next((i for i in cart if i["id"] == item["id"]), None)
            if existing_item:
                existing_item["quantity"] = existing_item.get("quantity", 1) + item["quantity"]
            else:
                cart.append(item)
            doc_ref.update({"cart": cart})
            if db:
                db.collection("api_logs").add({
                    "endpoint": "cart/add",
                    "status": "success",
                    "user_id": user_id,
                    "item_id": item["id"],
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
            return jsonify({"message": "Item added", "itemId": item["id"]}), 200
        return jsonify({"error": "Profile not found"}), 404
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "cart/add",
                "status": "error",
                "user_id": user_id,
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Add to cart failed: {str(e)}"}), 500

@app.route("/cart/get", methods=["GET"])
@firebase_auth
def get_cart():
    user_id = g.user["uid"]
    try:
        doc = db.collection("profiles").document(user_id).get()
        if doc.exists:
            cart = doc.to_dict().get("cart", [])
            if db:
                db.collection("api_logs").add({
                    "endpoint": "cart/get",
                    "status": "success",
                    "user_id": user_id,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
            return jsonify({"items": cart}), 200
        return jsonify({"items": []}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "cart/get",
                "status": "error",
                "user_id": user_id,
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Get cart failed: {str(e)}"}), 500


@app.route("/cart/remove", methods=["POST"])
@firebase_auth
def remove_from_cart():
    user_id = g.user["uid"]
    item_id = request.get_json().get("item_id")
    if not item_id:
        return jsonify({"error": "Missing item_id in request"}), 400
    try:
        doc_ref = db.collection("profiles").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            cart = doc.to_dict().get("cart", [])
            cart = [item for item in cart if item["id"] != item_id]
            doc_ref.update({"cart": cart})
            if db:
                db.collection("api_logs").add({
                    "endpoint": "cart/remove",
                    "status": "success",
                    "user_id": user_id,
                    "item_id": item_id,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
            return jsonify({"message": "Item removed"}), 200
        return jsonify({"error": "Profile not found"}), 404
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "cart/remove",
                "status": "error",
                "user_id": user_id,
                "error": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"error": f"Remove from cart failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)