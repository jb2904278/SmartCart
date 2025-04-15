import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import Header from "../components/Header";
import Login from "./login";
import CartCard from "../components/CartCard";
import DietarySummary from "../components/DietarySummary";
import styles from "../styles/Products.module.css";
import { filterProducts } from "../utils/filterLogic";

export default function Products({ showNotification }) {
  const { user, addToCart, dietaryPrefs } = useAuth();
  const [products, setProducts] = useState([]);
  const [filters, setFilters] = useState({
    vegan: false,
    glutenFree: false,
    nutFree: false,
    organic: false,
    nonGMO: false,
    lowCarb: false,
    highFiber: false,
    lowSodium: false,
    root: false,
    leafy: false,
    fruitVegetable: false,
    cruciferous: false,
    bulb: false,
    squash: false,
    stem: false,
    other: false,
  });
  const [showLogin, setShowLogin] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchWithRetry = async (url, retries = 7, initialDelay = 1000, timeout = 10000) => {
    let delay = initialDelay;
    for (let i = 0; i < retries; i++) {
      try {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(id);
        if (!response.ok) throw new Error(`HTTP ${response.status} ${response.statusText}`);
        return await response.json();
      } catch (err) {
        if (i < retries - 1) {
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay *= 2;
          if (err.name === "AbortError") {
            console.warn(`Retry ${i + 1} for ${url}: Fetch timed out after ${timeout}ms`);
          } else if (err.message.includes("HTTP")) {
            console.warn(`Retry ${i + 1} for ${url}: ${err.message}`);
          } else {
            console.warn(`Retry ${i + 1} for ${url}: Network error - ${err.message}`);
          }
          continue;
        }
        throw err;
      }
    }
  };

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await fetchWithRetry("http://localhost:5000/grocery-items");
        const vegetables = data.items.map((item, index) => {
          const baseTags = item.tags || ["vegan", "gluten-free", "nut-free"];
          
          // Define additional tags based on product name
          const additionalTags = [];
          
          // Organic: Assume all are organic for simplicity
          additionalTags.push("organic");
          
          // Non-GMO: All except Zucchini
          if (!item.name.toLowerCase().includes("zucchini")) {
            additionalTags.push("non-gmo");
          }
          
          // Low-Carb: Broccoli, Spinach, Cauliflower, Green Peppers, Zucchini
          if (
            item.name.toLowerCase().includes("broccoli") ||
            item.name.toLowerCase().includes("spinach") ||
            item.name.toLowerCase().includes("cauliflower") ||
            item.name.toLowerCase().includes("green peppers") ||
            item.name.toLowerCase().includes("zucchini")
          ) {
            additionalTags.push("low-carb");
          }
          
          // High-Fiber: Broccoli, Cauliflower, Spinach, Carrots
          if (
            item.name.toLowerCase().includes("broccoli") ||
            item.name.toLowerCase().includes("cauliflower") ||
            item.name.toLowerCase().includes("spinach") ||
            item.name.toLowerCase().includes("carrots")
          ) {
            additionalTags.push("high-fiber");
          }

          const product = {
            id: index + 1,
            name: item.name,
            price: item.price,
            tags: [...baseTags, ...additionalTags],
            image: item.image || "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300",
            vegType: item.veg_type || "other",
          };
          console.log(`Product: ${product.name}, Image: ${product.image}, VegType: ${product.vegType}, Tags: ${product.tags.join(", ")}, Price: ${product.price}`);
          return product;
        });
        setProducts(vegetables.slice(0, 20));
      } catch (err) {
        console.error("Error fetching vegetables:", {
          message: err.message,
          name: err.name,
          stack: err.stack,
        });
        showNotification("Failed to load products", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [showNotification]);

  const filteredProducts = filterProducts(products, filters);

  const handleAddToCart = async (product) => {
    if (!user) {
      setShowLogin(true);
    } else {
      const success = await addToCart({ ...product, quantity: 1 });
      if (success) {
        showNotification(`${product.name} added to cart`, "success");
      } else {
        showNotification("Failed to add to cart", "error");
      }
    }
  };

  return (
    <div className={styles.container}>
      <Header />
      <h1 className={styles.title}>Our Vegetables</h1>
      <DietarySummary />

      <div className={styles.filters}>
        <h3 className={styles.filterHeader}>Vegetable Types</h3>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.root}
            onChange={(e) => setFilters({ ...filters, root: e.target.checked })}
          />
          Root (e.g., Potatoes, Carrots)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.leafy}
            onChange={(e) => setFilters({ ...filters, leafy: e.target.checked })}
          />
          Leafy (e.g., Spinach, Cilantro)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.fruitVegetable}
            onChange={(e) => setFilters({ ...filters, fruitVegetable: e.target.checked })}
          />
          Fruit Vegetable (e.g., Tomatoes, Peppers)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.cruciferous}
            onChange={(e) => setFilters({ ...filters, cruciferous: e.target.checked })}
          />
          Cruciferous (e.g., Broccoli, Cauliflower)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.bulb}
            onChange={(e) => setFilters({ ...filters, bulb: e.target.checked })}
          />
          Bulb (e.g., Onions, Garlic)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.squash}
            onChange={(e) => setFilters({ ...filters, squash: e.target.checked })}
          />
          Squash (e.g., Zucchini, Cucumber)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.stem}
            onChange={(e) => setFilters({ ...filters, stem: e.target.checked })}
          />
          Stem (e.g., Asparagus, Celery)
        </label>
        <label className={styles.filterLabel}>
          <input
            type="checkbox"
            checked={filters.other}
            onChange={(e) => setFilters({ ...filters, other: e.target.checked })}
          />
          Other (e.g., Mushrooms, Artichokes)
        </label>
      </div>
      {loading ? (
        <p className={styles.loading}>Loading vegetables...</p>
      ) : filteredProducts.length === 0 ? (
        <p className={styles.loading}>No products match your filters.</p>
      ) : (
        <div className={styles.productGrid}>
          {filteredProducts.map((product) => (
            <div key={product.id} className={styles.productCard}>
              <img
                src={product.image}
                alt={product.name}
                className={styles.productImage}
                onError={(e) => (e.target.src = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300")}
              />
              <h3 className={styles.productName}>{product.name}</h3>
              <p className={styles.productPrice}>${product.price.toFixed(2)}</p>
              <button
                onClick={() => handleAddToCart(product)}
                className={styles.addButton}
              >
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      )}
      <CartCard dietaryFilters={filters} />
      {showLogin && (
        <div className={styles.modalOverlay}>
          <Login
            onClose={() => setShowLogin(false)}
            isModal={true}
            showNotification={showNotification}
          />
        </div>
      )}
    </div>
  );
}