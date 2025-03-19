import firebase_admin
from firebase_admin import auth, credentials

# Ensure Firebase is initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

# Prompt user for details
email = input("Enter the email for the new user: ")
password = input("Enter the password for the new user: ")
display_name = input("Enter the display name for the new user: ")

try:
    # Create a user with inputted details
    user = auth.create_user(
        email=email,
        password=password,
        display_name=display_name
    )
    print(f"✅ User created successfully! UID: {user.uid}")
except Exception as e:
    print(f"❌ Error creating user: {e}")
