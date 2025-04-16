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


# Get API keys
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Get Spoonacular API key from environment
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
if not SPOONACULAR_API_KEY:
    print("Warning: SPOONACULAR_API_KEY not set in .env, using dummy data")
if not USDA_API_KEY:
    print("Warning: USDA_API_KEY not set")
if not UNSPLASH_ACCESS_KEY:
    print("Warning: UNSPLASH_ACCESS_KEY not set")


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
@limiter.limit("100/hour")
def test_apis():
    try:
        open_food_response = requests.get("https://world.openfoodfacts.org/api/v0/product/737628064502.json").json()
        usda_response = requests.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={"api_key": USDA_API_KEY, "query": "vegetables", "pageSize": 1}
        ).json() if USDA_API_KEY else {"foods": [{"description": "Mock Vegetable"}]}
        spoonacular_response = requests.get(
            f"https://api.spoonacular.com/recipes/findByIngredients?ingredients=apple&apiKey={SPOONACULAR_API_KEY}"
        ).json() if SPOONACULAR_API_KEY else [{"title": "Mock Recipe"}]
        if db:
            db.collection("api_tests").add({
                "open_food": open_food_response.get("product", {}).get("product_name", "N/A"),
                "usda": usda_response["foods"][0]["description"],
                "spoonacular": spoonacular_response[0]["title"],
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        return jsonify({"message": "All APIs are accessible"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Grocery items
@app.route("/grocery-items", methods=["GET"])
@limiter.limit("100/hour")
def get_grocery_items():
    start_time = time.time()
    try:
        vegetable_types = {
            "tomato": "fruit_vegetable",
            "carrot": "root",
            "potato": "root",
            "beet": "root",
            "radish": "root",
            "spinach": "leafy",
            "lettuce": "leafy",
            "kale": "leafy",
            "cabbage": "leafy",
            "cilantro": "leafy",
            "broccoli": "cruciferous",
            "cauliflower": "cruciferous",
            "brussels sprout": "cruciferous",
            "zucchini": "squash",
            "cucumber": "squash",
            "squash": "squash",
            "eggplant": "fruit_vegetable",
            "pepper": "fruit_vegetable",
            "onion": "bulb",
            "garlic": "bulb",
            "leek": "bulb",
            "asparagus": "stem",
            "celery": "stem",
            "artichoke": "other",
            "mushroom": "other"
        }

        known_english_veggies = {
            "tomato", "carrot", "potato", "beet", "radish", "spinach", "lettuce", "kale", "cabbage",
            "cilantro", "broccoli", "cauliflower", "brussels sprout", "zucchini", "cucumber", "squash",
            "eggplant", "pepper", "bell pepper", "green pepper", "onion", "garlic", "leek", "asparagus",
            "celery", "artichoke", "mushroom"
        }

        def normalize_name(name):
            if not name:
                return ""
            normalized = name.lower()
            normalized = ''.join(c for c in normalized if c.isalnum() or c == ' ')
            normalized = normalized.replace(
                "cherry red green yellow purple organic fresh baby plum grape roma heirloom paste concentrate chopped puree passata boiled raw", ""
            ).strip()
            normalized = normalized.replace("ies", "y").replace("s ", " ")
            if "tomato" in normalized or "passata" in normalized or "pasta" in normalized:
                return "tomato"
            if "potato" in normalized:
                return "potato"
            if "brussels" in normalized:
                return "brussels sprout"
            if "cilantro" in normalized:
                return "cilantro"
            if "pepper" in normalized:
                return "pepper"
            return normalized

        def is_english_name(name):
            if not name:
                return False
            cleaned_name = name.replace("'", "").replace("  ", " ")
            if not all(c.isalpha() or c.isspace() or c == '-' for c in cleaned_name):
                return False
            norm_name = normalize_name(name)
            return any(veggie in norm_name for veggie in known_english_veggies)

        def extract_keywords(name):
            if not name:
                return []
            normalized = name.lower()
            keywords = normalized.split()
            keyword_mappings = {
                "tomato": ["tomato", "tomaten", "passata", "paste", "puree", "tomatoe"],
                "potato": ["potato", "potatoes"],
                "brussels sprout": ["brussels", "brussel", "sprout", "sprouts"],
                "carrot": ["carrot", "carrots", "carrote", "carottes"],
                "beet": ["beet", "beets", "beetroot"],
                "spinach": ["spinach", "spinache"],
                "lettuce": ["lettuce"],
                "kale": ["kale"],
                "cabbage": ["cabbage"],
                "cilantro": ["cilantro", "coriander"],
                "broccoli": ["broccoli"],
                "cauliflower": ["cauliflower"],
                "zucchini": ["zucchini", "courgette", "courgettes"],
                "cucumber": ["cucumber", "cucumbers"],
                "squash": ["squash", "squashes"],
                "eggplant": ["eggplant", "aubergine", "aubergines"],
                "pepper": ["pepper", "peppers", "bell pepper", "green pepper"],
                "onion": ["onion", "onions"],
                "garlic": ["garlic"],
                "leek": ["leek", "leeks"],
                "asparagus": ["asparagus"],
                "celery": ["celery"],
                "artichoke": ["artichoke", "artichokes"],
                "mushroom": ["mushroom", "mushrooms"]
            }
            matched_keywords = []
            for main_key, variants in keyword_mappings.items():
                if any(variant in keywords for variant in variants):
                    matched_keywords.append(main_key)
            return matched_keywords

        def get_veg_type(norm_name):
            for key, vtype in vegetable_types.items():
                if key in norm_name:
                    return vtype
            return "other"

        def get_vegetable_image(vegetable_name):
            try:
                cache_doc = db.collection("image_cache").document(vegetable_name.lower()).get()
                if cache_doc.exists:
                    return cache_doc.to_dict().get("image_url", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300")
                url = f"https://api.unsplash.com/search/photos?query={vegetable_name}&per_page=1"
                headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                data = response.json()
                image_url = data["results"][0]["urls"]["small"] if data["results"] else "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300"
                db.collection("image_cache").document(vegetable_name.lower()).set({
                    "image_url": image_url,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                return image_url
            except Exception as e:
                print(f"Error fetching image for {vegetable_name}: {str(e)}")
                return "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300"

        seen_names = set()
        seen_types = set()
        seen_keywords = set()
        items = []
        filtered_out = []

        try:
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {
                "api_key": USDA_API_KEY,
                "query": "vegetables",
                "pageSize": 30,
                "dataType": "Foundation,SR Legacy,Branded"
            }
            headers = {"User-Agent": "SmartCart - Python - Version 1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            data = {"foods": []}
            filtered_out.append({"name": "N/A", "reason": f"API fetch failed: {str(e)}"})

        all_products = []
        products = data.get("foods", [])
        random.shuffle(products)
        for product in products:
            name = product.get("description", "Unknown Vegetable")
            if not name or not is_english_name(name):
                filtered_out.append({"name": name, "reason": "Non-English name or invalid"})
                continue
            norm_name = normalize_name(name)
            veg_type = get_veg_type(norm_name)
            keywords = extract_keywords(name)
            category = product.get("foodCategory", "Vegetable").lower()
            if "vegetable" not in category.lower():
                filtered_out.append({"name": name, "reason": "Not a vegetable"})
                continue
            all_products.append({
                "name": name,
                "norm_name": norm_name,
                "veg_type": veg_type,
                "keywords": keywords,
                "category": category,
                "tags": ["vegan", "gluten-free", "nut-free", "organic"]
            })

        type_to_product = {}
        for product in all_products:
            veg_type = product["veg_type"]
            if veg_type not in type_to_product:
                type_to_product[veg_type] = []
            type_to_product[veg_type].append(product)

        for veg_type, products in type_to_product.items():
            for product in products:
                name = product["name"]
                norm_name = product["norm_name"]
                keywords = product["keywords"]
                has_overlap = any(keyword in seen_keywords for keyword in keywords)
                if has_overlap:
                    filtered_out.append({"name": name, "reason": "Overlapping keyword"})
                    continue
                if norm_name in seen_names:
                    filtered_out.append({"name": name, "reason": "Duplicate name"})
                    continue
                seen_names.add(norm_name)
                seen_types.add(veg_type)
                seen_keywords.update(keywords)
                price = 1.50
                image_url = get_vegetable_image(norm_name)
                items.append({
                    "name": name,
                    "category": product["category"],
                    "tags": product["tags"],
                    "price": price,
                    "image": image_url,
                    "veg_type": veg_type
                })
                break

        mock_vegetables = [
            {"name": "Fresh Potatoes", "veg_type": "root", "keywords": ["potato"]},
            {"name": "Cilantro Bunch", "veg_type": "leafy", "keywords": ["cilantro"]},
            {"name": "Red Onions", "veg_type": "bulb", "keywords": ["onion"]},
            {"name": "Tomatoes", "veg_type": "fruit_vegetable", "keywords": ["tomato"]},
            {"name": "Green Peppers", "veg_type": "fruit_vegetable", "keywords": ["pepper"]},
            {"name": "Carrots", "veg_type": "root", "keywords": ["carrot"]},
            {"name": "Spinach Leaves", "veg_type": "leafy", "keywords": ["spinach"]},
            {"name": "Broccoli Florets", "veg_type": "cruciferous", "keywords": ["broccoli"]},
            {"name": "Zucchini", "veg_type": "squash", "keywords": ["zucchini"]},
            {"name": "Cauliflower Head", "veg_type": "cruciferous", "keywords": ["cauliflower"]}
        ]

        remaining_slots = 20 - len(items)
        if remaining_slots > 0:
            random.shuffle(mock_vegetables)
            for mock in mock_vegetables:
                if len(items) >= 20:
                    break
                name = mock["name"]
                norm_name = normalize_name(name)
                veg_type = mock["veg_type"]
                keywords = mock["keywords"]
                has_overlap = any(keyword in seen_keywords for keyword in keywords)
                if has_overlap:
                    filtered_out.append({"name": name, "reason": "Overlapping keyword (mock)"})
                    continue
                if norm_name in seen_names:
                    filtered_out.append({"name": name, "reason": "Duplicate name (mock)"})
                    continue
                seen_names.add(norm_name)
                seen_types.add(veg_type)
                seen_keywords.update(keywords)
                image_url = get_vegetable_image(norm_name)
                items.append({
                    "name": name,
                    "category": "vegetable",
                    "tags": ["vegan", "gluten-free", "nut-free"],
                    "price": 1.50,
                    "image": image_url,
                    "veg_type": veg_type
                })

        if not items:
            raise Exception("No valid vegetable items found")

        if db:
            db.collection("api_logs").add({"endpoint": "grocery-items", "status": "success", "time": time.time() - start_time, "filtered_out": filtered_out[:20]})
            db.collection("grocery_cache").document("latest").set({"items": items, "timestamp": firestore.SERVER_TIMESTAMP})
        return jsonify({"items": items}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({"endpoint": "grocery-items", "status": "error", "time": time.time() - start_time, "error": str(e)})
            cached = db.collection("grocery_cache").document("latest").get().to_dict()
            if cached and "items" in cached:
                return jsonify(cached), 200
        return jsonify({"error": str(e)}), 500


@app.route("/daily-offers", methods=["GET"])
@limiter.limit("100/hour")
def get_daily_offers():
    start_time = time.time()
    try:
        mock_vegetables = [
            {"name": "Fresh Potatoes", "veg_type": "root", "keywords": ["potato"]},
            {"name": "Broccoli Florets", "veg_type": "cruciferous", "keywords": ["broccoli"]},
            {"name": "Cilantro Bunch", "veg_type": "leafy", "keywords": ["cilantro"]},
            {"name": "Green Peppers", "veg_type": "fruit_vegetable", "keywords": ["pepper", "green pepper"]},
            {"name": "Carrots", "veg_type": "root", "keywords": ["carrot"]},
            {"name": "Spinach Leaves", "veg_type": "leafy", "keywords": ["spinach"]},
            {"name": "Zucchini", "veg_type": "squash", "keywords": ["zucchini"]},
            {"name": "Red Onions", "veg_type": "bulb", "keywords": ["onion"]},
            {"name": "Cauliflower Head", "veg_type": "cruciferous", "keywords": ["cauliflower"]},
            {"name": "Asparagus Spears", "veg_type": "stem", "keywords": ["asparagus"]}
        ]

        vegetable_types = {
            "tomato": "fruit_vegetable",
            "carrot": "root",
            "potato": "root",
            "beet": "root",
            "radish": "root",
            "spinach": "leafy",
            "lettuce": "leafy",
            "kale": "leafy",
            "cabbage": "leafy",
            "cilantro": "leafy",
            "broccoli": "cruciferous",
            "cauliflower": "cruciferous",
            "brussels sprout": "cruciferous",
            "zucchini": "squash",
            "cucumber": "squash",
            "squash": "squash",
            "eggplant": "fruit_vegetable",
            "pepper": "fruit_vegetable",
            "onion": "bulb",
            "garlic": "bulb",
            "leek": "bulb",
            "asparagus": "stem",
            "celery": "stem",
            "artichoke": "other",
            "mushroom": "other"
        }

        known_english_veggies = {
            "tomato", "carrot", "potato", "beet", "radish", "spinach", "lettuce", "kale", "cabbage",
            "cilantro", "broccoli", "cauliflower", "brussels sprout", "zucchini", "cucumber", "squash",
            "eggplant", "pepper", "bell pepper", "green pepper", "onion", "garlic", "leek", "asparagus",
            "celery", "artichoke", "mushroom"
        }

        def normalize_name(name):
            if not name:
                return ""
            normalized = name.lower()
            normalized = ''.join(c for c in normalized if c.isalnum() or c == ' ')
            normalized = normalized.replace(
                "cherry red green yellow purple organic fresh baby plum grape roma heirloom paste concentrate chopped puree passata", ""
            ).strip()
            normalized = normalized.replace("ies", "y").replace("s ", " ")
            if "tomato" in normalized or "passata" in normalized or "pasta" in normalized:
                return "tomato"
            if "potato" in normalized:
                return "potato"
            if "brussels" in normalized:
                return "brussels sprout"
            if "cilantro" in normalized:
                return "cilantro"
            if "pepper" in normalized:
                return "pepper"
            return normalized

        def is_english_name(name):
            if not name:
                return False
            cleaned_name = name.replace("'", "").replace("  ", " ")
            if not all(c.isalpha() or c.isspace() or c == '-' for c in cleaned_name):
                return False
            norm_name = normalize_name(name)
            return any(veggie in norm_name for veggie in known_english_veggies)

        def extract_keywords(name):
            if not name:
                return []
            normalized = name.lower()
            keywords = normalized.split()
            keyword_mappings = {
                "tomato": ["tomato", "tomaten", "passata", "paste", "puree", "tomatoe"],
                "potato": ["potato", "potatoes"],
                "brussels sprout": ["brussels", "brussel", "sprout", "sprouts"],
                "carrot": ["carrot", "carrots", "carrote", "carottes"],
                "beet": ["beet", "beets", "beetroot"],
                "spinach": ["spinach", "spinache"],
                "lettuce": ["lettuce"],
                "kale": ["kale"],
                "cabbage": ["cabbage"],
                "cilantro": ["cilantro", "coriander"],
                "broccoli": ["broccoli"],
                "cauliflower": ["cauliflower"],
                "zucchini": ["zucchini", "courgette", "courgettes"],
                "cucumber": ["cucumber", "cucumbers"],
                "squash": ["squash", "squashes"],
                "eggplant": ["eggplant", "aubergine", "aubergines"],
                "pepper": ["pepper", "peppers", "bell pepper", "green pepper"],
                "onion": ["onion", "onions"],
                "garlic": ["garlic"],
                "leek": ["leek", "leeks"],
                "asparagus": ["asparagus"],
                "celery": ["celery"],
                "artichoke": ["artichoke", "artichokes"],
                "mushroom": ["mushroom", "mushrooms"]
            }
            matched_keywords = []
            for main_key, variants in keyword_mappings.items():
                if any(variant in keywords for variant in variants):
                    matched_keywords.append(main_key)
            return matched_keywords

        def get_veg_type(norm_name):
            for key, vtype in vegetable_types.items():
                if key in norm_name:
                    return vtype
            return "other"

        seen_names = set()
        seen_types = set()
        seen_keywords = set()
        offers = []
        filtered_out = []

        try:
            url = "https://world.openfoodfacts.org/api/v2/search"
            params = {
                "categories_tags_en": "vegetables",
                "fields": "product_name_en,product_name",
                "lang": "en",
                "page_size": 600,
                "json": "true"
            }
            headers = {"User-Agent": "SmartCart - Python - Version 1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            data = {"products": []}
            filtered_out.append({"name": "N/A", "reason": f"API fetch failed: {str(e)}"})

        all_products = []
        products = data.get("products", [])
        random.shuffle(products)
        for product in products:
            name = product.get("product_name_en") or product.get("product_name")
            if not name:
                filtered_out.append({"name": "None", "reason": "No name"})
                continue
            if not is_english_name(name):
                filtered_out.append({"name": name, "reason": "Non-English name"})
                continue
            norm_name = normalize_name(name)
            veg_type = get_veg_type(norm_name)
            keywords = extract_keywords(name)
            all_products.append({
                "name": name,
                "norm_name": norm_name,
                "veg_type": veg_type,
                "keywords": keywords
            })

        type_to_product = {}
        for product in all_products:
            veg_type = product["veg_type"]
            if veg_type not in type_to_product:
                type_to_product[veg_type] = []
            type_to_product[veg_type].append(product)

        for veg_type, products in type_to_product.items():
            for product in products:
                name = product["name"]
                norm_name = product["norm_name"]
                keywords = product["keywords"]
                has_overlap = any(keyword in seen_keywords for keyword in keywords)
                if has_overlap:
                    filtered_out.append({"name": name, "reason": "Overlapping keyword"})
                    continue
                if norm_name in seen_names:
                    filtered_out.append({"name": name, "reason": "Duplicate name"})
                    continue
                seen_names.add(norm_name)
                seen_types.add(veg_type)
                seen_keywords.update(keywords)
                offers.append({
                    "name": name,
                    "original": round(random.uniform(2, 5), 2),
                    "sale": round(random.uniform(1, 3), 2),
                    "tags": ["vegan", "gluten-free", "nut-free"]
                })
                break

        remaining_slots = 10 - len(offers)
        if remaining_slots > 0:
            random.shuffle(mock_vegetables)
            for mock in mock_vegetables:
                if len(offers) >= 10:
                    break
                name = mock["name"]
                norm_name = normalize_name(name)
                veg_type = mock["veg_type"]
                keywords = mock["keywords"]
                has_overlap = any(keyword in seen_keywords for keyword in keywords)
                if has_overlap:
                    filtered_out.append({"name": name, "reason": "Overlapping keyword (mock)"})
                    continue
                if norm_name in seen_names:
                    filtered_out.append({"name": name, "reason": "Duplicate name (mock)"})
                    continue
                seen_names.add(norm_name)
                seen_types.add(veg_type)
                seen_keywords.update(keywords)
                offers.append({
                    "name": name,
                    "original": round(random.uniform(2, 5), 2),
                    "sale": round(random.uniform(1, 3), 2),
                    "tags": ["vegan", "gluten-free", "nut-free"]
                })

        random.shuffle(offers)

        if not offers:
            raise Exception("No valid vegetable offers found")

        if db:
            db.collection("offers_cache").document("latest").set({"offers": offers, "timestamp": firestore.SERVER_TIMESTAMP})
            db.collection("api_logs").add({
                "endpoint": "daily-offers",
                "status": "success",
                "time": time.time() - start_time,
                "filtered_out": filtered_out[:20]
            })
        return jsonify({"offers": offers}), 200
    except Exception as e:
        if db:
            db.collection("api_logs").add({
                "endpoint": "daily-offers",
                "status": "error",
                "time": time.time() - start_time,
                "error": str(e)
            })
            cached = db.collection("offers_cache").document("latest").get().to_dict()
            if cached and "offers" in cached:
                return jsonify(cached), 200
        return jsonify({"error": str(e)}), 500


@app.route("/meal-recommendations", methods=["POST"])
@firebase_auth
@limiter.limit("10 per minute")
def meal_recommendations():
    data = request.get_json()
    cart_items = data.get("cart_items", [])
    dietary_prefs = data.get("dietary_prefs", {})
    try:
        if not cart_items:
            return jsonify({"meals": []}), 200

        # Step 1: Fetch initial meal suggestions
        query = ",".join(cart_items)
        diet = []
        if dietary_prefs.get("vegan"):
            diet.append("vegan")
        if dietary_prefs.get("glutenFree"):
            diet.append("gluten free")
        if dietary_prefs.get("nutFree"):
            diet.append("peanut free")
        if dietary_prefs.get("dairyFree"):
            diet.append("dairy free")
        if dietary_prefs.get("keto"):
            diet.append("ketogenic")
        if dietary_prefs.get("paleo"):
            diet.append("paleo")
        diet_str = ",".join(diet) if diet else None
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "ingredients": query,
            "number": 5  # Fetch more recipes to account for filtering
        }
        if diet_str:
            params["diet"] = diet_str
        if dietary_prefs.get("lowCarb"):
            params["maxCarbs"] = 20

        response = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params=params
        )
        response.raise_for_status()
        recipes = response.json()

        if not recipes:
            return jsonify({"meals": []}), 200

        # Step 2: Fetch dietary information for each recipe
        meals = []
        for recipe in recipes:
            recipe_id = recipe["id"]
            # Fetch detailed recipe information
            recipe_info_response = requests.get(
                f"https://api.spoonacular.com/recipes/{recipe_id}/information",
                params={"apiKey": SPOONACULAR_API_KEY}
            )
            recipe_info_response.raise_for_status()
            recipe_info = recipe_info_response.json()

            # Extract dietary tags
            tags = []
            if recipe_info.get("vegan"):
                tags.append("vegan")
            if recipe_info.get("glutenFree"):
                tags.append("gluten-free")
            if recipe_info.get("dairyFree"):
                tags.append("dairy-free")
            # Spoonacular uses "veryHealthy" as a proxy for some dietary preferences
            if recipe_info.get("veryHealthy"):
                if dietary_prefs.get("lowCarb") and recipe_info.get("lowCarb", False):
                    tags.append("low-carb")
                if dietary_prefs.get("keto") and recipe_info.get("ketogenic", False):
                    tags.append("keto")
                if dietary_prefs.get("paleo") and recipe_info.get("paleo", False):
                    tags.append("paleo")
            # Note: Spoonacular API does not directly provide nut-free or peanut-free flags
            # We'll assume recipes without peanuts in ingredients are nut-free for simplicity
            ingredients = [ing["name"].lower() for ing in recipe.get("usedIngredients", []) + recipe.get("missedIngredients", [])]
            has_nuts = any("peanut" in ing or "nut" in ing for ing in ingredients)
            if not has_nuts:
                tags.append("nut-free")

            meals.append({
                "meal": recipe["title"],
                "ingredients": [ing["name"] for ing in recipe.get("usedIngredients", [])],
                "tags": tags
            })

        return jsonify({"meals": meals}), 200
    except Exception as e:
        return jsonify({"error": f"Meal recommendations failed: {str(e)}"}), 500


@app.route("/api-logs", methods=["GET"])
@limiter.limit("100/hour")
def get_api_logs():
    if not db:
        return jsonify({"error": "Database unavailable"}), 500
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