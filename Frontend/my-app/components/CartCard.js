import { useAuth } from "../context/AuthContext";
import styles from "./CartCard.module.css";
import MealRecommendations from "./MealRecommendations";

export default function CartCard({ dietaryFilters }) {
  const { user, cart, removeFromCart } = useAuth();

  if (!user) {
    return <p className={styles.loginPrompt}>Login to View Cart</p>;
  }

  const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
  const totalPrice = cart.reduce((sum, item) => sum + (item.price * (item.quantity || 1)), 0);

  console.log("Rendering CartCard with cart:", cart);

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Shopping Cart</h3>
      {cart.length ? (
        cart.map((item) => (
          <div key={item.id} className={styles.item}>
            <span>
              {item.name} - ${Number(item.price).toFixed(2)} x {item.quantity || 1}
            </span>
            <button
              onClick={() => removeFromCart(item.id)}
              className={styles.removeButton}
            >
              Remove
            </button>
          </div>
        ))
      ) : (
        <p className={styles.empty}>Cart is empty</p>
      )}
      {cart.length > 0 && (
        <>
          <div className={styles.summary}>
            <p>Total Items: {totalItems}</p>
            <p>Total Price: ${totalPrice.toFixed(2)}</p>
          </div>
          <div className={styles.mealRecommendations}>
            <MealRecommendations cartItems={cart} dietaryFilters={dietaryFilters} />
          </div>
        </>
      )}
    </div>
  );
}