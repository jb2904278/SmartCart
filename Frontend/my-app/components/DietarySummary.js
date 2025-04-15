import { useAuth } from "../context/AuthContext";
import styles from "./DietarySummary.module.css";

export default function DietarySummary({ cart }) {
  const { dietaryPrefs } = useAuth();

  const generateMealSuggestion = () => {
    if (!cart || cart.length === 0) return "Add items to your cart to get meal suggestions!";
    
    const vegetables = cart.filter(item => item.category === "vegetable");
    const fruits = cart.filter(item => item.category === "fruit");

    let suggestion = "Try making: ";
    if (vegetables.length > 0) {
      suggestion += `${vegetables[0].name} Salad`;
      if (dietaryPrefs.vegan) suggestion += " (Vegan)";
      if (dietaryPrefs.glutenFree) suggestion += " (Gluten-Free)";
      if (dietaryPrefs.nutFree) suggestion += " (Nut-Free)";
    } else if (fruits.length > 0) {
      suggestion += `${fruits[0].name} Smoothie`;
      if (dietaryPrefs.vegan) suggestion += " (Vegan)";
    } else {
      suggestion = "Add some vegetables or fruits for meal ideas!";
    }
    return suggestion;
  };

  return (
    <div className={styles.summary}>
      <h2 className={styles.title}>Dietary Summary</h2>
      <p className={styles.prefs}>
        Preferences: <span>
        {Object.entries(dietaryPrefs)
          .filter(([_, value]) => value)
          .map(([key]) => key.charAt(0).toUpperCase() + key.slice(1))
          .join(", ") || "None"}
        </span>
      </p>
      <p className={styles.suggestion}>{generateMealSuggestion()}</p>
    </div>
  );
}