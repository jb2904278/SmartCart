import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/router";
import Link from "next/link";
import styles from "../styles/Signup.module.css";

export default function Signup({ showNotification }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(""); 
  const { signup } = useAuth();
  const router = useRouter();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(""); 
    try {
      await signup(email, password, name);
      showNotification("Signup successful! Welcome to SmartCart.", "success");
      router.push("/products");
    } catch (error) {
      console.error("Signup failed:", error);
      if (error.code === "auth/email-already-in-use") {
        setError("This email is already in use. Please use a different email or log in.");
        showNotification("This email is already in use. Please use a different email or log in.", "error");
      } else if (error.code === "auth/invalid-email") {
        setError("Invalid email address. Please enter a valid email.");
        showNotification("Invalid email address", "error");
      } else if (error.code === "auth/weak-password") {
        setError("Password is too weak. It should be at least 6 characters long.");
        showNotification("Password is too weak", "error");
      } else {
        setError("Signup failed. Please try again.");
        showNotification("Signup failed. Please try again.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Sign Up</h1>
      <form onSubmit={handleSignup}>
        <div className={styles.inputGroup}>
          <label>Email:</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className={styles.input}
            required
          />
        </div>
        <div className={styles.inputGroup}>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            className={styles.input}
            required
          />
        </div>
        <div className={styles.inputGroup}>
          <label>Name:</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            className={styles.input}
            required
          />
        </div>
        {error && <p className={styles.error}>{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className={styles.button}
        >
          {loading ? "Signing up..." : "Sign Up"}
        </button>
      </form>
      <p className={styles.linkText}>
        Already have an account?{" "}
        <Link href="/login" className={styles.link}>
          Log in here
        </Link>
      </p>
    </div>
  );
}