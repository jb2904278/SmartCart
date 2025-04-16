import { useAuth } from "../context/AuthContext";
import Link from "next/link";
import styles from "./Header.module.css";
import { memo } from "react";

function Header() {
  const { user, logout } = useAuth();

  // Placeholder SVG for avatar if DiceBear fails
  const placeholderAvatar = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='%23555' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E";

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.logo}>
        SmartCart
      </Link>
      <nav className={styles.nav}>
        <Link href="/products" className={`${styles.link} ${styles.productsButton}`}>
          Products
        </Link>
        {user ? (
          <>
            <Link href="/profile" className={styles.link}>
              Profile
            </Link>
            <div className={styles.userInfo}>
              <img
                src={user.avatarUrl || placeholderAvatar}
                alt={`Avatar of ${user.name}`}
                title={`Avatar of ${user.name}`} // Added for accessibility
                className={styles.avatar}
              />
              <span className={styles.welcome}>Welcome, {user.name}</span>
            </div>
            <button onClick={logout} className={styles.button}>
              Logout
            </button>
          </>
        ) : (
          <Link href="/login" className={styles.button}>
            Login
          </Link>
        )}
      </nav>
    </header>
  );
}

export default memo(Header);