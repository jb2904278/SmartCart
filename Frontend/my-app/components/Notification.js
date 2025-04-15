import { useState, useEffect } from "react";
import styles from "./Notification.module.css";

export default function Notification({ message, type = "success", onClose }) {
  const [visible, setVisible] = useState(!!message);

  useEffect(() => {
    if (message) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onClose();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);

  if (!visible) return null;

  return (
    <div className={`${styles.notification} ${styles[type]}`}>
      <p>{message}</p>
      <button onClick={() => setVisible(false)} className={styles.close}>
        ×
      </button>
    </div>
  );
}