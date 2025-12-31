"""Database initialization and migration script."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import init_db, drop_db
from src.database.models import User
from src.api.middleware.jwt_auth import hash_password
from src.database.config import SessionLocal
import uuid

def seed_demo_user():
    """Create demo user for testing."""
    db = SessionLocal()
    
    # Check if demo user exists
    demo = db.query(User).filter(User.username == "demo_user").first()
    if demo:
        print("ℹ️  Demo user already exists")
        return
    
    demo_user = User(
        id=str(uuid.uuid4()),
        username="demo_user",
        email="demo@example.com",
        hashed_password=hash_password("demo_password_123"),
        is_active=True
    )
    
    db.add(demo_user)
    db.commit()
    print("✅ Demo user created")
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--drop", action="store_true", help="Drop all tables (WARNING)")
    parser.add_argument("--seed", action="store_true", help="Seed demo data")
    parser.add_argument("--all", action="store_true", help="Init + seed")
    
    args = parser.parse_args()
    
    if args.drop:
        confirm = input("⚠️  This will delete all data. Type 'yes' to confirm: ")
        if confirm == "yes":
            drop_db()
        else:
            print("Cancelled")
    
    if args.init or args.all:
        init_db()
    
    if args.seed or args.all:
        seed_demo_user()
    
    if not any([args.init, args.drop, args.seed, args.all]):
        print("Usage: python scripts/init_db.py --init --seed")
