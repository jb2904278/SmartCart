import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/router";
import Link from "next/link";
import { getAuth, sendPasswordResetEmail } from "firebase/auth";
import styles from "../styles/Login.module.css";

export default function Login({ onClose, isModal = false, showNotification }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  const auth = getAuth();

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleLogin = async (e) => {
    e.preventDefault(); 
    setError("");
    setLoading(true);


    if (!email) {
      setError("Email is required.");
      setLoading(false);
      showNotification("Email is required", "error");
      return;
    }
    if (!validateEmail(email)) {
      setError("Please enter a valid email address.");
      setLoading(false);
      showNotification("Invalid email address", "error");
      return;
    }
    if (!password) {
      setError("Password is required.");
      setLoading(false);
      showNotification("Password is required", "error");
      return;
    }

    try {
      await login(email, password);
      showNotification("Logged in successfully", "success");
      if (isModal) onClose();
      else router.push("/products");
    } catch (err) {
      console.error("Login error:", err);
      if (err.code === "auth/invalid-email") {
        setError("Please enter a valid email address.");
        showNotification("Invalid email address", "error");
      } else if (err.code === "auth/user-not-found") {
        setError("No account exists with this email. Please sign up.");
        showNotification("No account exists with this email", "error");
      } else if (err.code === "auth/wrong-password") {
        setError("Incorrect password. Please try again or reset your password.");
        showNotification("Incorrect password", "error");
      } else if (err.code === "auth/too-many-requests") {
        setError("Too many attempts. Please try again later or reset your password.");
        showNotification("Too many attempts", "error");
      } else {
        setError("Login failed. Please check your email and password.");
        showNotification("Login failed", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    if (!email) {
      setError("Please enter your email address to reset your password.");
      showNotification("Email is required for password reset", "error");
      return;
    }
    if (!validateEmail(email)) {
      setError("Please enter a valid email address to reset your password.");
      showNotification("Invalid email address", "error");
      return;
    }
    setResetLoading(true);
    setError("");
    try {
      await sendPasswordResetEmail(auth, email);
      showNotification("Password reset email sent! Check your inbox.", "success");
    } catch (err) {
      console.error("Password reset error:", err);
      if (err.code === "auth/invalid-email") {
        setError("Please enter a valid email address to reset your password.");
        showNotification("Invalid email address", "error");
      } else if (err.code === "auth/user-not-found") {
        setError("No account exists with this email. Please sign up.");
        showNotification("No account exists with this email", "error");
      } else {
        setError("Failed to send password reset email. Please try again.");
        showNotification("Failed to send password reset email", "error");
      }
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className={`${styles.container} ${isModal ? styles.modal : ""}`}>
      <h1 className={styles.title}>Login</h1>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className={styles.input}
          required
          aria-label="Email address"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className={styles.input}
          required
          aria-label="Password"
        />
        {error && <p className={styles.error}>{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className={styles.button}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
      <p className={styles.linkText}>
        <span
          onClick={handlePasswordReset}
          className={styles.link}
          style={{ cursor: resetLoading ? "not-allowed" : "pointer" }}
        >
          {resetLoading ? "Sending reset email..." : "Forgot Password?"}
        </span>
      </p>
      <p className={styles.linkText}>
        Don’t have an account?{" "}
        <Link href="/signup" className={styles.link}>
          Sign Up
        </Link>
      </p>
      {isModal && (
        <button
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Close login modal"
        >
          ✕
        </button>
      )}
    </div>
  );
}