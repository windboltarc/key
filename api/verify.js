import { initializeApp, cert } from "firebase-admin/app";
import { getFirestore, Timestamp } from "firebase-admin/firestore";

const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);

// Init Firebase Admin
initializeApp({ credential: cert(serviceAccount) });
const db = getFirestore();

export default async function handler(req, res) {
  if(req.method !== "POST") return res.status(405).json({ status:"error", message:"Method not allowed" });
  
  try{
    const { key } = req.body;
    if(!key || !/^Lunar_[A-Z0-9]{20}$/.test(key)) return res.status(400).json({ status:"error", message:"Invalid key format" });

    const docRef = db.collection("keys").doc(key);
    const docSnap = await docRef.get();

    if(!docSnap.exists) return res.json({ status:"success", isValid:false });

    const data = docSnap.data();
    const now = Timestamp.now();

    // Check 24h expiration
    if(data.used || (now.toMillis() - data.createdAt.toMillis()) > 24*60*60*1000){
      return res.json({ status:"success", isValid:false });
    }

    // Mark as used
    await docRef.update({ used:true });

    return res.json({ status:"success", isValid:true });
  }catch(e){
    console.error(e);
    return res.status(500).json({ status:"error", message:e.message });
  }
}
