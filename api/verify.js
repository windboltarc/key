import { initializeApp } from "firebase/app";
import { getDatabase, ref, get, update } from "firebase/database";

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.FIREBASE_DB_URL,
  projectId: process.env.FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

export default async function handler(req, res) {
  const { key } = req.method === "POST" ? req.body : req.query;

  if (!key) {
    return res.status(400).json({ valid: false, error: "No key provided" });
  }

  const snapshot = await get(ref(db, "keys/" + key));
  if (!snapshot.exists()) {
    return res.json({ valid: false, error: "Key not found" });
  }

  const data = snapshot.val();

  if (data.used) {
    return res.json({ valid: false, error: "Key already used" });
  }

  if (Date.now() > data.expire) {
    return res.json({ valid: false, error: "Key expired" });
  }

  // Nếu gọi bằng GET (truy cập web) thì chỉ show key
  if (req.method === "GET") {
    return res.send(`
      <html>
        <head><title>Lunar Key</title></head>
        <body style="font-family: sans-serif; background:#111; color:#0f0; text-align:center; padding:40px;">
          <h1>Your Lunar Key</h1>
          <p style="font-size:20px; color:#0ff;">${key}</p>
          <p>Valid for 24 hours</p>
        </body>
      </html>
    `);
  }

  // Nếu POST từ C# → mark as used
  await update(ref(db, "keys/" + key), { used: true });

  return res.json({ valid: true });
}
