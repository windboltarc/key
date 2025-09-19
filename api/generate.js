import { initializeApp } from "firebase/app";
import { getDatabase, ref, set } from "firebase/database";

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.FIREBASE_DB_URL,
  projectId: process.env.FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

export default async function handler(req, res) {
  // Generate random key
  const key = "LUNAR_" + Math.random().toString(36).substring(2, 12);
  const expire = Date.now() + 24 * 60 * 60 * 1000; // 24h

  // Save to Firebase
  await set(ref(db, "keys/" + key), {
    expire: expire,
    used: false
  });

  // Redirect auto → verify page
  res.writeHead(302, {
    Location: `/api/verify?key=${key}`
  });
  res.end();
}
