import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

load_dotenv(dotenv_path=backend_dir / ".env")

from pymongo import MongoClient
from app.extensions import password_manager
from app.models.user import User

def seed_admin(email="admin@example.com", username="admin", password="AdminPassword123!", full_name="System Administrator"):
    """Seeds an initial administrator account if one does not already exist."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("DB_NAME", "banking_dev")

    client = MongoClient(mongo_uri)
    db = client[db_name]

    existing = db.users.find_one({"$or": [{"email": email}, {"username": username}]})
    if existing:
        print(f"[INFO] Admin user '{username}' or email '{email}' already exists. No changes made.")
        return

    admin_doc = User.create_document(
        email=email,
        username=username,
        plain_password=password,
        full_name=full_name,
        role="admin"
    )

    db.users.insert_one(admin_doc)
    print(f"[SUCCESS] Admin account created successfully!")
    print(f"  User ID : {admin_doc['user_id']}")
    print(f"  Username: {admin_doc['username']}")
    print(f"  Email   : {admin_doc['email']}")
    print(f"  Role    : {admin_doc['role']}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    username = sys.argv[2] if len(sys.argv) > 2 else "admin"
    password = sys.argv[3] if len(sys.argv) > 3 else "AdminPassword123!"
    full_name = sys.argv[4] if len(sys.argv) > 4 else "System Administrator"

    seed_admin(email, username, password, full_name)
