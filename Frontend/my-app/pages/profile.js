import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import Header from "../components/Header";
import styles from "../styles/Profile.module.css";

export default function Profile({ showNotification }) {
  const { user, updateProfile, dietaryPrefs } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatarUrl || "");
  const [prefs, setPrefs] = useState({
    vegan: dietaryPrefs.vegan || false,
    glutenFree: dietaryPrefs.glutenFree || false,
    nutFree: dietaryPrefs.nutFree || false,
    organic: dietaryPrefs.organic || false,
    nonGMO: dietaryPrefs.nonGMO || false,
    lowCarb: dietaryPrefs.lowCarb || false,
    highFiber: dietaryPrefs.highFiber || false,
    lowSodium: dietaryPrefs.lowSodium || false,
    dairyFree: dietaryPrefs.dairyFree || false
  });
  const [error, setError] = useState("");

  const placeholderAvatar = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='50' height='50' viewBox='0 0 24 24' fill='none' stroke='%23555' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E";

  const handleSave = async () => {
    if (!name) {
      setError("Name is required");
      showNotification("Name is required", "error");
      return;
    }
    const validAvatar = avatarUrl.startsWith("https://") ? avatarUrl : user.avatarUrl;
    const success = await updateProfile(name, validAvatar, prefs);
    if (success) {
      showNotification("Profile updated successfully", "success");
      setError("");
    } else {
      showNotification("Failed to update profile", "error");
    }
  };

  return (
    <div className={styles.container}>
      <Header />
      <h1 className={styles.title}>Profile</h1>
      <div className={styles.form}>
        <div className={styles.field}>
          <label htmlFor="name" className={styles.label}>Name:</label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={styles.input}
          />
        </div>
        <div className={styles.field}>
          <label htmlFor="avatarUrl" className={styles.label}>Avatar URL:</label>
          <input
            id="avatarUrl"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            className={styles.input}
            placeholder="Enter a valid HTTPS URL"
          />
          <img
            src={avatarUrl || placeholderAvatar}
            alt={`Avatar for ${name || "user"}`}
            className={styles.avatar}
          />
        </div>
        <div className={styles.field}>
          <h3 className={styles.subtitle}>Dietary Preferences</h3>
          <div className={styles.checkboxContainer}>
            <label htmlFor="vegan" className={styles.checkbox}>
              <input
                id="vegan"
                type="checkbox"
                checked={prefs.vegan}
                onChange={(e) => setPrefs({ ...prefs, vegan: e.target.checked })}
              />
              Vegan
            </label>
            <label htmlFor="glutenFree" className={styles.checkbox}>
              <input
                id="glutenFree"
                type="checkbox"
                checked={prefs.glutenFree}
                onChange={(e) => setPrefs({ ...prefs, glutenFree: e.target.checked })}
              />
              Gluten-Free
            </label>
            <label htmlFor="nutFree" className={styles.checkbox}>
              <input
                id="nutFree"
                type="checkbox"
                checked={prefs.nutFree}
                onChange={(e) => setPrefs({ ...prefs, nutFree: e.target.checked })}
              />
              Nut-Free
            </label>
            <label htmlFor="organic" className={styles.checkbox}>
              <input
                id="organic"
                type="checkbox"
                checked={prefs.organic}
                onChange={(e) => setPrefs({ ...prefs, organic: e.target.checked })}
              />
              Organic
            </label>
            <label htmlFor="nonGMO" className={styles.checkbox}>
              <input
                id="nonGMO"
                type="checkbox"
                checked={prefs.nonGMO}
                onChange={(e) => setPrefs({ ...prefs, nonGMO: e.target.checked })}
              />
              Non-GMO
            </label>
            <label htmlFor="lowCarb" className={styles.checkbox}>
              <input
                id="lowCarb"
                type="checkbox"
                checked={prefs.lowCarb}
                onChange={(e) => setPrefs({ ...prefs, lowCarb: e.target.checked })}
              />
              Low-Carb
            </label>
            <label htmlFor="highFiber" className={styles.checkbox}>
              <input
                id="highFiber"
                type="checkbox"
                checked={prefs.highFiber}
                onChange={(e) => setPrefs({ ...prefs, highFiber: e.target.checked })}
              />
              High-Fiber
            </label>
            <label htmlFor="lowSodium" className={styles.checkbox}>
              <input
                id="lowSodium"
                type="checkbox"
                checked={prefs.lowSodium}
                onChange={(e) => setPrefs({ ...prefs, lowSodium: e.target.checked })}
              />
              Low-Sodium
            </label>
            <label htmlFor="dairyFree" className={styles.checkbox}>
              <input
                id="dairyFree"
                type="checkbox"
                checked={prefs.dairyFree}
                onChange={(e) => setPrefs({ ...prefs, dairyFree: e.target.checked })}
              />
              Dairy-Free
            </label>
            <label htmlFor="keto" className={styles.checkbox}>
              <input
                id="keto"
                type="checkbox"
                checked={prefs.keto}
                onChange={(e) => setPrefs({ ...prefs, keto: e.target.checked })}
              />
              Keto
            </label>
            <label htmlFor="paleo" className={styles.checkbox}>
              <input
                id="paleo"
                type="checkbox"
                checked={prefs.paleo}
                onChange={(e) => setPrefs({ ...prefs, paleo: e.target.checked })}
              />
              Paleo
            </label>
          </div>
        </div>
        {error && <p className={styles.error}>{error}</p>}
        <button onClick={handleSave} className={styles.button}>
          Save
        </button>
      </div>
    </div>
  );
}
