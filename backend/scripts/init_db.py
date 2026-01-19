#!/usr/bin/env python3
"""
Initialize database - create tables and seed initial data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.database import init_db, get_db, crud

def main():
    """Initialize database"""
    print("🗄️  Initializing database...")
    
    try:
        # Create all tables
        init_db()
        print("✅ Database tables created")
        
        # Create default user
        print("Creating default user...")
        db = next(get_db())
        user = crud.get_or_create_user(
            db,
            user_id="u_dev",
            timezone="America/Los_Angeles"
        )
        print(f"✅ User created: {user.id}")
        
        print("")
        print("🎉 Database initialization complete!")
        print("")
        print("Next steps:")
        print("  1. Start the API: uvicorn apps.api.main:app --reload")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Try: curl http://localhost:8000/api/brief/latest")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
