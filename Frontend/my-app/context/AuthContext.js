import { createContext, useContext, useState, useEffect } from "react";
import { initializeApp } from "firebase/app";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";

const AuthContext = createContext();

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [idToken, setIdToken] = useState(null);
  const [cart, setCart] = useState([]);
  const [dietaryPrefs, setDietaryPrefs] = useState({
    vegan: false,
    glutenFree: false,
    nutFree: false,
    organic: false,
    nonGMO: false,
    lowCarb: false,
    highFiber: false,
    lowSodium: false,
    dairyFree: false,
    keto: false,
    paleo: false,
  });
  const [loading, setLoading] = useState(true);

  const generateAvatar = (seed) =>
    `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(seed)}`;

  const defaultDietaryPrefs = {
    vegan: false,
    glutenFree: false,
    nutFree: false,
    organic: false,
    nonGMO: false,
    lowCarb: false,
    highFiber: false,
    lowSodium: false,
    dairyFree: false,
    keto: false,
    paleo: false,
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken();
          setIdToken(token);
          let profile = {
            name: firebaseUser.email.split("@")[0],
            avatarUrl: generateAvatar(firebaseUser.uid),
            dietaryPrefs: defaultDietaryPrefs,
          };
          try {
            const profileRes = await fetch(
              `http://localhost:5000/profile/${firebaseUser.uid}`,
              {
                headers: { Authorization: `Bearer ${token}` },
              }
            );
            if (!profileRes.ok) {
              console.error(`Profile fetch failed: ${profileRes.status} ${profileRes.statusText}`);
              throw new Error("Failed to fetch profile");
            }
            profile = await profileRes.json();
          } catch (fetchErr) {
            console.warn(`Using fallback profile: ${fetchErr.message}`);
          }
          setUser({
            userId: firebaseUser.uid,
            name: profile.name || firebaseUser.email.split("@")[0],
            avatarUrl: profile.avatarUrl || generateAvatar(firebaseUser.uid),
            email: firebaseUser.email,
            token,
          });
          setDietaryPrefs(profile.dietaryPrefs || defaultDietaryPrefs);
          try {
            const cartRes = await fetch("http://localhost:5000/cart/get", {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (!cartRes.ok) throw new Error("Failed to fetch cart");
            const cartData = await cartRes.json();
            setCart(cartData.items || []);
          } catch (cartErr) {
            console.warn(`Failed to fetch cart: ${cartErr.message}`);
            setCart([]);
          }
        } catch (err) {
          console.error("Auth error:", err);
          setUser(null);
          setIdToken(null);
          setCart([]);
          setDietaryPrefs(defaultDietaryPrefs);
        }
      } else {
        setUser(null);
        setIdToken(null);
        setCart([]);
        setDietaryPrefs(defaultDietaryPrefs);
      }
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const login = async (email, password) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;
      const token = await firebaseUser.getIdToken();
      setIdToken(token);

     
      try {
        const loginRes = await fetch("http://localhost:5000/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, token }),
        });
        if (!loginRes.ok) {
          console.warn(`Backend login log failed: ${loginRes.status} ${loginRes.statusText}`);
        }
      } catch (err) {
        console.warn(`Backend login log error: ${err.message}`);
      }

      let profile = {
        name: firebaseUser.email.split("@")[0],
        avatarUrl: generateAvatar(firebaseUser.uid),
        dietaryPrefs: defaultDietaryPrefs,
      };
      try {
        const profileRes = await fetch(
          `http://localhost:5000/profile/${firebaseUser.uid}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        if (profileRes.ok) {
          profile = await profileRes.json();
        }
      } catch (err) {
        console.warn(`Login profile fetch failed: ${err.message}`);
      }
      setUser({
        userId: firebaseUser.uid,
        name: profile.name || email.split("@")[0],
        avatarUrl: profile.avatarUrl || generateAvatar(firebaseUser.uid),
        email: firebaseUser.email,
        token,
      });
      setDietaryPrefs(profile.dietaryPrefs || defaultDietaryPrefs);
      try {
        const cartRes = await fetch("http://localhost:5000/cart/get", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (cartRes.ok) {
          const cartData = await cartRes.json();
          setCart(cartData.items || []);
        }
      } catch (err) {
        console.warn(`Login cart fetch failed: ${err.message}`);
      }
    } catch (err) {
      console.error("Login error:", err);
      throw err;
    }
  };

  const signup = async (email, password, name) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;
      const token = await firebaseUser.getIdToken();
      setIdToken(token);
      const avatarUrl = generateAvatar(firebaseUser.uid);
      try {
        const response = await fetch("http://localhost:5000/auth/signup", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ email, name, avatarUrl }),
        });
        if (!response.ok) throw new Error("Signup backend failed");
      } catch (err) {
        console.error(`Signup backend error: ${err.message}`);
      }
      setUser({
        userId: firebaseUser.uid,
        name,
        avatarUrl,
        email,
        token,
      });
      setDietaryPrefs(defaultDietaryPrefs);
      setCart([]);
    } catch (err) {
      console.error("Signup error:", err);
      throw err;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      setIdToken(null);
      setCart([]);
      setDietaryPrefs(defaultDietaryPrefs);
    } catch (err) {
      console.error("Logout error:", err);
      throw err;
    }
  };

  const addToCart = async (item) => {
    if (!user) return false;
    try {
      const response = await fetch("http://localhost:5000/cart/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ item: { ...item, price: Number(item.price) } }),
      });
      if (response.ok) {
        const data = await response.json();
        const cartRes = await fetch("http://localhost:5000/cart/get", {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (cartRes.ok) {
          const cartData = await cartRes.json();
          setCart(cartData.items || []);
        }
        return true;
      }
      return false;
    } catch (err) {
      console.error(`Add to cart error: ${err.message}`);
      return false;
    }
  };

  const removeFromCart = async (itemId) => {
    if (!user) return;
    try {
      const response = await fetch("http://localhost:5000/cart/remove", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ item_id: itemId }),
      });
      if (response.ok) {
        const cartRes = await fetch("http://localhost:5000/cart/get", {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (cartRes.ok) {
          const cartData = await cartRes.json();
          setCart(cartData.items || []);
        }
      }
    } catch (err) {
      console.error(`Remove from cart error: ${err.message}`);
    }
  };

  const updateProfile = async (name, avatarUrl, dietaryPrefs) => {
    if (!user) return false;
    try {
      const response = await fetch("http://localhost:5000/profile/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ name, avatarUrl, dietaryPrefs }),
      });
      if (response.ok) {
        setUser((prev) => ({ ...prev, name, avatarUrl }));
        setDietaryPrefs(dietaryPrefs);
        return true;
      }
      return false;
    } catch (err) {
      console.error(`Update profile error: ${err.message}`);
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        idToken,
        login,
        signup,
        logout,
        cart,
        addToCart,
        removeFromCart,
        dietaryPrefs,
        updateProfile,
        loading,
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}