import Header from "../components/Header";
import CartCard from "../components/CartCard";
import DailyOffers from "../components/DailyOffers";
import { useRouter } from "next/router";
import styles from "../styles/Home.module.css";

export default function Home() {
  const router = useRouter();

  return (
    <div className={styles.container}>
      <Header />
      <div className={styles.hero}>
        <h1 className={styles.title}>Welcome to SmartCart</h1>
        <p className={styles.subtitle}>Discover premium groceries with style.</p>
        <button onClick={() => router.push("/products")} className={styles.button}>
          Browse Products
        </button>
      </div>
      <DailyOffers />
      <CartCard /> {/* Shows cart and meal recommendations for logged-in users */}
    </div>
  );
}
