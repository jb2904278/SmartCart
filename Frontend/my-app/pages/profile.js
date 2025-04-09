
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import Header from "../components/Header";

export default function Profile() {
  const { user, updateDietaryPrefs, dietaryPrefs } = useAuth();
  const [name, setName] = useState(user?.name || "John Doe");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatarUrl || "https://dummyavatar.com/john.jpg");
  const [prefs, setPrefs] = useState(dietaryPrefs);

  const handleSave = () => {
    updateDietaryPrefs(prefs);
  };
 

  return (
    <div>
      <Header />
      <h1>Profile</h1>
      <div>
        <label>Name:</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <label>Avatar URL:</label>
        <input value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} />
        <img src={avatarUrl} alt="Avatar" style={{ width: "50px", margin: "10px" }} />
      </div>
      <div>
        <h3>Dietary Preferences</h3>
        <label>
          <input
            type="checkbox"
            checked={prefs.vegan}
            onChange={(e) => setPrefs({ ...prefs, vegan: e.target.checked })}
          />
          Vegan
        </label>
        <label>
          <input
            type="checkbox"
            checked={prefs.glutenFree}
            onChange={(e) => setPrefs({ ...prefs, glutenFree: e.target.checked })}
          />
          Gluten-Free
        </label>
        <label>
          <input
            type="checkbox"
            checked={prefs.nutFree}
            onChange={(e) => setPrefs({ ...prefs, nutFree: e.target.checked })}
          />
          Nut-Free
        </label>
      </div>
      <button onClick={handleSave}>Save</button>
    </div>
  );
}
