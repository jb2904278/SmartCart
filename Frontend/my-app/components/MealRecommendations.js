import React, { useState, useCallback, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import styles from "./MealRecommendations.module.css";

export default function MealRecommendations() {
  const { user, cart, dietaryPrefs } = useAuth(); // Changed cartItems to cart
  const [meals, setMeals] = useState([]);
  const [filteredMeals, setFilteredMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRequestTime, setLastRequestTime] = useState(0);

  // Debounce delay to prevent rapid requests (e.g., 1 second between requests)
  const DEBOUNCE_DELAY = 1000;

  const filterMealsByDietaryPrefs = (meals) => {
    if (!dietaryPrefs) return meals;

    const dietaryFilters = {
      vegan: dietaryPrefs.vegan,
      glutenFree: dietaryPrefs.glutenFree,
      nutFree: dietaryPrefs.nutFree,
      lowCarb: dietaryPrefs.lowCarb,
      dairyFree: dietaryPrefs.dairyFree,
      keto: dietaryPrefs.keto,
      paleo: dietaryPrefs.paleo,
    };

    return meals.filter((meal) => {
      return Object.entries(dietaryFilters).every(([key, value]) => {
        if (!value) return true; // If the filter is not active, skip it
        const tagKey = key.toLowerCase().replace("glutenfree", "gluten-free");
        return meal.tags.includes(tagKey);
      });
    });
  };

  const fetchMeals = useCallback(async () => {
    const now = Date.now();
    if (now - lastRequestTime < DEBOUNCE_DELAY) {
      console.log("Request skipped due to debounce");
      return;
    }

    setLoading(true);
    setError(null);
    setLastRequestTime(now);

    try {
      if (!user) {
        throw new Error("Please log in to get meal recommendations");
      }

      const token = user.token || (await user.getIdToken?.());
      if (!token) {
        throw new Error("Authentication token not available");
      }

      const response = await fetch("http://localhost:5000/meal-recommendations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          cart_items: cart.map((item) => item.name), // Use cart instead of cartItems
          dietary_prefs: dietaryPrefs,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        if (response.status === 429) {
          throw new Error("Too many requests. Please wait a minute and try again.");
        }
        throw new Error(
          `Failed to fetch meal recommendations: ${response.status} ${response.statusText} - ${errorText}`
        );
      }

      const data = await response.json();
      const fetchedMeals = data.meals || [];
      setMeals(fetchedMeals);

      // Filter meals based on dietary preferences
      const filtered = filterMealsByDietaryPrefs(fetchedMeals);
      setFilteredMeals(filtered);
    } catch (err) {
      setError(err.message);
      setMeals([]);
      setFilteredMeals([]);
    } finally {
      setLoading(false);
    }
  }, [user, cart, dietaryPrefs, lastRequestTime]); // Update dependency to cart

  useEffect(() => {
    // Since cart is guaranteed to be an array, we can simplify the check
    if (cart.length > 0) {
      fetchMeals();
    } else {
      setMeals([]);
      setFilteredMeals([]);
    }
  }, [cart, fetchMeals]); // Update dependency to cart

  // Re-filter meals whenever dietaryPrefs change
  useEffect(() => {
    const filtered = filterMealsByDietaryPrefs(meals);
    setFilteredMeals(filtered);
  }, [dietaryPrefs, meals]);

  const handleRetry = () => {
    fetchMeals();
  };

  return (
    <div className={styles.mealRecommendations}>
      <h2>Meal Recommendations</h2>
      {loading && <p className={styles.loading}>Loading recommendations...</p>}
      {error && (
        <div className={styles.error}>
          <p>{error}</p>
          {error.includes("Too many requests") ? (
            <p>Please wait a moment before trying again.</p>
          ) : (
            <button onClick={handleRetry} className={styles.retryButton}>
              Retry
            </button>
          )}
        </div>
      )}
      {!loading && !error && filteredMeals.length === 0 && (
        <p>No recommendations available that match your dietary preferences. Try adjusting your preferences or adding different items to your cart.</p>
      )}
      {!loading && !error && filteredMeals.length > 0 && (
        <ul className={styles.mealList}>
          {filteredMeals.map((meal, index) => (
            <li key={index} className={styles.mealItem}>
              <h3>{meal.meal}</h3>
              <p>Ingredients: {meal.ingredients.join(", ")}</p>
              <p>Dietary Tags: {meal.tags.join(", ")}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}