import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/router";
import styles from "../styles/Signup.module.css";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const router = useRouter();

  const handleSignup = () => {
    if (email && password.length >= 6) {
      login("user123", "New User", "https://default-avatar.com");
      router.push("/products");
    } else {
      setError("Enter a valid email and password (min 6 chars)");
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Sign Up</h1>
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
      <button onClick={handleSignup} className={styles.button}>Sign Up</button>
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
