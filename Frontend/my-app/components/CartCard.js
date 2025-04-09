import { useAuth } from "../context/AuthContext";
import styles from "./CartCard.module.css";
import MealRecommendations from "./MealRecommendations";

export default function CartCard() {
  const { user, cart } = useAuth();

  if (!user) {
    return <p className={styles.loginPrompt}>Login to View Cart</p>;
  }

  const totalItems = cart.length;
  const totalPrice = cart.reduce((sum, item) => sum + (item.price || 1.00), 0);

  console.log("Rendering CartCard with cart:", cart); // Debug log

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Shopping Cart</h3>
      {cart.length ? (
        cart.map((item, index) => (
          <div key={index} className={styles.item}>
            {item.name} - ${item.price || 1.00}
          </div>
        ))
      ) : (
        <p className={styles.empty}>Cart is empty</p>
      )}
      <div className={styles.summary}>
        <p>Total Items: {totalItems}</p>
        <p>Total Price: ${totalPrice.toFixed(2)}</p>
      </div>
      {cart.length > 0 && <MealRecommendations cartItems={cart} />}
    </div>
  );
}
