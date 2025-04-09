import { useState, useEffect } from "react";
import styles from "./MealRecommendations.module.css";

export default function MealRecommendations({ cartItems }) {
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMeals = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("http://localhost:5000/meal-recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cart_items: cartItems.map(item => item.name) })
        });
        if (!response.ok) throw new Error("Failed to fetch meal recommendations");
        const data = await response.json();
        console.log("Meal data:", data); // Debug log
        setMeals(data.meals || []);
      } catch (error) {
        console.error("Error fetching meal recommendations:", error);
        setError(error.message);
        setMeals([]);
      }
      setLoading(false);
    };

    if (cartItems.length > 0) {
      fetchMeals();
    } else {
      setMeals([]);
    }
  }, [cartItems]);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Meal Suggestions</h3>
      {loading ? (
        <p className={styles.loading}>Loading recipes...</p>
      ) : error ? (
        <p className={styles.error}>{error}</p>
      ) : meals.length > 0 ? (
        meals.map((meal, index) => (
          <div key={index} className={styles.meal}>
            <h4>{meal.meal}</h4>
            <p>Ingredients: {meal.ingredients.join(", ")}</p>
          </div>
        ))
      ) : (
        <p className={styles.empty}>Add items to see meal suggestions.</p>
      )}
    </div>
  );
}
