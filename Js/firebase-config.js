export const firebaseConfig = {
  apiKey: "AIzaSyADxJTYYvXCk6AkqTUgOJDHROL1YYUxj7U",
  authDomain: "tokyoweekend.firebaseapp.com",
  projectId: "tokyoweekend",
  appId: "1:597026431047:web:f0b161e9818813ea43d162",
  storageBucket: "tokyoweekend.firebasestorage.app",
  messagingSenderId: "597026431047",
  measurementId: "G-E18MMK79D1"
};

export function isFirebaseConfigured(config) {
  if (!config || typeof config !== "object") {
    return false;
  }

  const requiredKeys = ["apiKey", "authDomain", "projectId", "appId"];
  return requiredKeys.every((key) => {
    const value = String(config[key] || "").trim();
    return value && !value.startsWith("YOUR_");
  });
}
