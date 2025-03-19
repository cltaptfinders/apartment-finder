import firebase_admin
from firebase_admin import credentials, firestore, auth

# Load the Firebase credentials
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore database
db = firestore.client()