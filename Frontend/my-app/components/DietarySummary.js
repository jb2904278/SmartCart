import { useAuth } from "../context/AuthContext";
import Link from "next/link";

export default function DietarySummary() {
  const { dietaryPrefs } = useAuth();
  const activePrefs = Object.entries(dietaryPrefs)
    .filter(([_, value]) => value)
    .map(([key]) => key.replace(/([A-Z])/g, " $1").toLowerCase())
    .join(", ") || "None";

  return (
    <div style={{ border: "1px solid #00f", padding: "10px", margin: "10px" }}>
      <h3>Your Preferences: {activePrefs}</h3>
      <Link href="/profile">
        <button>Edit Preferences</button>
      </Link>
    </div>
  );
}
