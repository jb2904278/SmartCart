import { useAuth } from "../context/AuthContext";


export default function Profile() {
  const { user, updateDietaryPrefs, dietaryPrefs } = useAuth();
 

  const handleSave = () => {
    updateDietaryPrefs(prefs);
  };
 

}
