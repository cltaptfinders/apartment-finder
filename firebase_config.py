import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

# ✅ Use Environment Variable for Firebase Credentials
cred = credentials.Certificate(os.getenv("FIREBASE_KEY_PATH", "firebase-key.json"))
firebase_admin.initialize_app(cred)

# Initialize Firestore database
db = firestore.client()