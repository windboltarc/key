import { initializeApp } from "firebase/app";
import { getFirestore, doc, setDoc, serverTimestamp } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_PROJECT_ID + ".firebaseapp.com",
  projectId: process.env.FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export default async function handler(req, res) {
  const key = "Lunar_" + Math.random().toString(36).substring(2, 15);

  await setDoc(doc(db, "keys", key), {
    createdAt: serverTimestamp(),
    used: false,
    expiresAt: Date.now() + 24 * 60 * 60 * 1000 // 24h
  });

  res.setHeader("Content-Type", "text/html");
  res.status(200).send(`
    <html>
      <head><title>Lunar Key</title></head>
      <body style="font-family:sans-serif; text-align:center; margin-top:100px;">
        <h1>Your Lunar Key</h1>
        <p style="font-size:20px; color:#0f0;">${key}</p>
        <p>Expires in 24h – One-time use only.</p>
      </body>
    </html>
  `);
}
