import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import Header from "../components/Header";
import Login from "./login";
import styles from "../styles/Products.module.css";

const DUMMY_PRODUCTS = [
  { name: "Tomato", tags: ["vegan", "gluten-free"], price: 1.00 },
  { name: "Apple", tags: ["vegan", "gluten-free", "nut-free"], price: 0.75 },
  { name: "Bread", tags: ["vegan"], price: 2.00 },
  { name: "Chicken", tags: [], price: 5.00 },
  { name: "Pasta", tags: ["gluten-free"], price: 3.00 }
];

export default function Products() {
  const { user, addToCart } = useAuth();
  const [filters, setFilters] = useState({ vegan: false, glutenFree: false, nutFree: false });
  const [showLogin, setShowLogin] = useState(false);

  const filteredProducts = DUMMY_PRODUCTS.filter((product) =>
    Object.entries(filters).every(([key, value]) =>
      !value || product.tags.includes(key.toLowerCase().replace("glutenfree", "gluten-free"))
    )
  );

  const handleAddToCart = (product) => {
    console.log("Attempting to add:", product);
    const added = addToCart(product);
    if (!added) {
      setShowLogin(true);
    }
  };

  return (
    <div className={styles.container}>
      <Header />
      <h1 className={styles.title}>Our Products</h1>
      <div className={styles.filters}>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.vegan}
            onChange={(e) => setFilters({ ...filters, vegan: e.target.checked })}
          />
          Vegan
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.glutenFree}
            onChange={(e) => setFilters({ ...filters, glutenFree: e.target.checked })}
          />
          Gluten-Free
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.nutFree}
            onChange={(e) => setFilters({ ...filters, nutFree: e.target.checked })}
          />
          Nut-Free
        </label>
      </div>
      <div className={styles.productGrid}>
        {filteredProducts.map((product, index) => (
          <div key={index} className={styles.productCard}>
            <h3 className={styles.productName}>{product.name}</h3>
            <p className={styles.productPrice}>${product.price}</p>
            <button onClick={() => handleAddToCart(product)} className={styles.addButton}>
              Add to Cart
            </button>
          </div>
        ))}
      </div>
      {showLogin && (
        <div className={styles.modalOverlay}>
          <Login onClose={() => setShowLogin(false)} isModal={true} />
        </div>
      )}
    </div>
  );
}
