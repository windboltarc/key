import { initializeApp } from "firebase/app";
import { getFirestore, doc, getDoc, updateDoc } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_PROJECT_ID + ".firebaseapp.com",
  projectId: process.env.FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const { key } = req.body;
  if (!key) return res.status(400).json({ error: "Missing key" });

  const ref = doc(db, "keys", key);
  const snap = await getDoc(ref);

  if (!snap.exists()) return res.json({ valid: false, reason: "Key not found" });

  const data = snap.data();
  if (data.used) return res.json({ valid: false, reason: "Key already used" });
  if (Date.now() > data.expiresAt) return res.json({ valid: false, reason: "Key expired" });

  await updateDoc(ref, { used: true });

  return res.json({ valid: true });
}
