import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [dietaryPrefs, setDietaryPrefs] = useState({ vegan: false, glutenFree: false, nutFree: false });

  const login = (userId, name, avatarUrl) => {
    setUser({ userId, loggedIn: true, name, avatarUrl });
  };

  const logout = () => {
    setUser(null);
    setCart([]);
    setDietaryPrefs({ vegan: false, glutenFree: false, nutFree: false });
  };

  const addToCart = (item) => {
    if (!user) {
      console.log("User not authenticated, showing login modal");
      return false;
    }
    console.log("Adding to cart:", item);
    setCart((prevCart) => {
      const newCart = [...prevCart, item];
      console.log("Updated cart:", newCart);
      return newCart;
    });
    return true;
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, cart, addToCart, dietaryPrefs, setDietaryPrefs }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}