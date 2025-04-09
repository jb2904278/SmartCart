import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/router";
import Link from "next/link";
import styles from "../styles/Login.module.css";

export default function Login({ onClose, isModal = false }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = () => {
    if (email === "test@example.com" && password === "password123") {
      login("user123", "John Doe", "https://dummyavatar.com/john.jpg");
      if (isModal) onClose();
      else router.push("/products");
    } else {
      setError("Invalid credentials");
    }
  };

  return (
    <div className={`${styles.container} ${isModal ? styles.modal : ''}`}>
      <h1 className={styles.title}>Login</h1>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        className={styles.input}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        className={styles.input}
      />
      <button onClick={handleLogin} className={styles.button}>Login</button>
      {error && <p className={styles.error}>{error}</p>}
      <p className={styles.linkText}>
        Dont have an account? <Link href="/signup" className={styles.link}>Sign Up</Link>
      </p>
      {isModal && <button onClick={onClose} className={styles.closeButton}>Close</button>}
    </div>
  );
}
