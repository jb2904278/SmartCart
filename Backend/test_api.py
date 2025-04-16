import unittest
import json
from unittest.mock import patch, MagicMock
from app import app

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_test_apis(self):
        response = self.app.get("/test-apis")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "All APIs are accessible")

    def test_grocery_items(self):
        response = self.app.get("/grocery-items")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("items", data)
        self.assertTrue(len(data["items"]) <= 20)
        self.assertTrue(all("price" in item for item in data["items"]))
        self.assertTrue(all("image" in item for item in data["items"]))

    def test_daily_offers(self):
        response = self.app.get("/daily-offers")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("offers", data)
        self.assertTrue(len(data["offers"]) <= 10)
        self.assertTrue(all("sale" in offer and "original" in offer for offer in data["offers"]))

    @patch('app.auth.verify_id_token')
    def test_meal_recommendations(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        response = self.app.post(
            "/meal-recommendations",
            json={"cart_items": ["tomato"], "dietary_prefs": {"vegan": True}},
            headers={"Authorization": "Bearer mock-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("meals", data)
        self.assertTrue(len(data["meals"]) <= 5)

    def test_meal_recommendations_unauthenticated(self):
        response = self.app.post(
            "/meal-recommendations",
            json={"cart_items": ["tomato"], "dietary_prefs": {"vegan": True}}
        )
        self.assertEqual(response.status_code, 401)

    def test_api_logs(self):
        response = self.app.get("/api-logs")
        self.assertEqual(response.status_code, 200)  # Database is available in this test environment
        data = json.loads(response.data)
        self.assertIsInstance(data, list)  # Expecting a list of logs

    @patch('app.auth.verify_id_token')
    def test_signup(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            mock_db_collection.return_value.document.return_value.set.return_value = None
            mock_db_collection.return_value.add.return_value = None
            response = self.app.post(
                "/auth/signup",
                json={"email": "test@example.com", "name": "Test User"},
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "User created")
        self.assertEqual(data["userId"], "test-user")

    @patch('app.auth.verify_id_token')
    @patch('app.auth.get_user_by_email')
    def test_login(self, mock_get_user_by_email, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        mock_get_user_by_email.return_value = type('User', (), {'uid': 'test-user'})()
        with patch('app.db.collection') as mock_db_collection:
            mock_db_collection.return_value.add.return_value = None
            response = self.app.post(
                "/auth/login",
                json={"email": "test@example.com", "token": "mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("uid", data)
        self.assertEqual(data["uid"], "test-user")
        self.assertEqual(data["token"], "mock-token")

    @patch('app.auth.verify_id_token')
    def test_update_profile(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            mock_db_collection.return_value.document.return_value.update.return_value = None
            mock_db_collection.return_value.add.return_value = None
            response = self.app.post(
                "/profile/update",
                json={
                    "name": "Updated User",
                    "avatarUrl": "https://example.com/avatar.png",
                    "dietaryPrefs": {"vegan": True}
                },
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Profile updated")

    @patch('app.auth.verify_id_token')
    def test_get_profile(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user", "email": "test@example.com"}
        with patch('app.db.collection') as mock_db_collection:
            mock_doc = MagicMock()
            mock_doc.exists = False  # Simulate profile not found, should return fallback
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db_collection.return_value.add.return_value = None
            response = self.app.get(
                "/profile/test-user",
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("email", data)
        self.assertIn("dietaryPrefs", data)

    @patch('app.auth.verify_id_token')
    def test_profile_logs(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            mock_doc = MagicMock()
            mock_doc.exists = False  # Simulate profile not found, should return empty logs
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db_collection.return_value.add.return_value = None
            response = self.app.get(
                "/profile-logs",
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("logs", data)
        self.assertEqual(data["logs"], {})  # Expecting empty logs since profile not found

    @patch('app.auth.verify_id_token')
    def test_add_to_cart(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            # Mock the Firestore document retrieval
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"cart": []}
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            # Mock the Firestore update and logging
            mock_db_collection.return_value.document.return_value.update.return_value = None
            mock_db_collection.return_value.add.return_value = None
            response = self.app.post(
                "/cart/add",
                json={"item": {"name": "Tomato", "price": 1.50}},
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Item added")

    def test_add_to_cart_unauthenticated(self):
        response = self.app.post(
            "/cart/add",
            json={"item": {"name": "Tomato", "price": 1.50}}
        )
        self.assertEqual(response.status_code, 401)

    @patch('app.auth.verify_id_token')
    def test_get_cart(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"cart": []}
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db_collection.return_value.add.return_value = None
            response = self.app.get(
                "/cart/get",
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("items", data)

    @patch('app.auth.verify_id_token')
    def test_cart_summary(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"cart": []}
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db_collection.return_value.add.return_value = None
            response = self.app.get(
                "/cart/summary",
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("totalItems", data)
        self.assertIn("totalPrice", data)
        self.assertIn("items", data)

    def test_cart_summary_unauthenticated(self):
        response = self.app.get("/cart/summary")
        self.assertEqual(response.status_code, 401)

    @patch('app.auth.verify_id_token')
    def test_remove_from_cart(self, mock_verify_id_token):
        mock_verify_id_token.return_value = {"uid": "test-user"}
        with patch('app.db.collection') as mock_db_collection:
            # Mock the Firestore document retrieval
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"cart": [{"id": "1", "name": "Tomato", "price": 1.50, "quantity": 1}]}
            mock_db_collection.return_value.document.return_value.get.return_value = mock_doc
            # Mock the Firestore update and logging
            mock_db_collection.return_value.document.return_value.update.return_value = None
            mock_db_collection.return_value.add.return_value = None
            response = self.app.post(
                "/cart/remove",
                json={"item_id": "1"},
                headers={"Authorization": "Bearer mock-token"}
            )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Item removed")

if __name__ == "__main__":
    unittest.main()