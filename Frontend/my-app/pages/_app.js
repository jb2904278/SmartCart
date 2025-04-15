
import { AuthProvider } from "../context/AuthContext";
import Head from "next/head";
import Notification from "../components/Notification";
import { useState } from "react";
import "../styles/globals.css";

export default function App({ Component, pageProps }) {
  const [notification, setNotification] = useState({ message: "", type: "" });

  const showNotification = (message, type) => {
    setNotification({ message, type });
  };

  return (
    <AuthProvider>
      <Head>
        <title>SmartCart</title>
        <link
          href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap"
          rel="stylesheet"
        />
      </Head>
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "" })}
      />
      <Component {...pageProps} showNotification={showNotification} />
    </AuthProvider>
  );
}