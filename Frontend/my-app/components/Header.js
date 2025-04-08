import { useAuth } from "../context/AuthContext";
import Link from "next/link";
import styles from "./Header.module.css";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className={styles.header}>
      <Link href="/products" className={styles.logo}>Grocery Elegance</Link>
      <nav className={styles.nav}>
        {user ? (
          <>
            <span className={styles.welcome}>Welcome, {user.name}</span>
            <button onClick={logout} className={styles.button}>Logout</button>
          </>
        ) : (
          <Link href="/login" className={styles.button}>Login</Link>
        )}
      </nav>
    </header>
  );
}