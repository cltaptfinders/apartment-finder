import firebase_admin
from firebase_admin import auth, credentials

# Ensure Firebase is initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")  # Ensure correct path
    firebase_admin.initialize_app(cred)

def set_user_role(email, role):
    """Assign a role to a Firebase user."""
    try:
        user = auth.get_user_by_email(email)
        auth.set_custom_user_claims(user.uid, {"role": role})
        print(f"✅ Role '{role}' assigned to {email}")
    except Exception as e:
        print(f"⚠️ Error assigning role: {e}")

if __name__ == "__main__":
    email = input("Enter user's email: ").strip()
    role = input("Enter role (admin, agent, community_manager): ").strip().lower()

    if role in ["admin", "agent", "community_manager"]:
        set_user_role(email, role)
    else:
        print("⚠️ Invalid role. Use 'admin', 'agent', or 'community_manager'.")
