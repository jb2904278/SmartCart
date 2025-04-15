import { useState, useEffect } from "react";
import styles from "./DailyOffers.module.css";

export default function DailyOffers({ showNotification }) {
  const [offers, setOffers] = useState([]);
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
    const fetchOffers = async () => {
      try {
        const data = await fetchWithRetry("http://localhost:5000/daily-offers");
        // Failsafe deduplication
        const seenNames = new Set();
        const uniqueOffers = data.offers.filter(offer => {
          const normName = offer.name.toLowerCase().replace(/s$/, "");
          if (seenNames.has(normName)) return false;
          seenNames.add(normName);
          return true;
        });
        setOffers(uniqueOffers);
      } catch (err) {
        console.error("Error fetching vegetable offers:", {
          message: err.message,
          name: err.name,
          stack: err.stack
        });
        showNotification("Unable to load vegetable offers. Please try again later.", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchOffers();
  }, [showNotification]);

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Daily Vegetable Deals</h1>
      {loading ? (
        <p className={styles.loading}>Loading vegetable offers...</p>
      ) : offers.length > 0 ? (
        <div className={styles.offerGrid}>
          {offers.map((offer, index) => (
            <div key={index} className={styles.offerCard}>
              <h3 className={styles.offerName}>{offer.name}</h3>
              <p className={styles.originalPrice}>
                Original: ${offer.original.toFixed(2)}
              </p>
              <p className={styles.discountedPrice}>
                Now: ${offer.sale.toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.empty}>No vegetable offers available.</p>
      )}
    </div>
  );
}