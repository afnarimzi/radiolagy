#!/usr/bin/env python3
"""
Setup database for Radiology AI system - Simplified for radiology agent
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.init_db import init_database, test_database_connection

def main():
    """Main setup function"""
    print("🏥 Radiology AI Database Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found. Creating default .env file...")
        with open(env_file, "w") as f:
            f.write("# Database configuration\n")
            f.write("DATABASE_URL=sqlite:///./radiology_ai.db\n")
            f.write("\n# Add other environment variables as needed\n")
        print("✅ Default .env file created")
    
    # Initialize database
    print("\n📊 Setting up database...")
    try:
        engine, SessionLocal = init_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False
    
    # Test database connection
    print("\n🧪 Testing database connection...")
    if test_database_connection():
        print("✅ Database test passed!")
    else:
        print("❌ Database test failed!")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYou can now:")
    print("1. Run the radiology agent: python main.py")
    print("2. View reports: python view_reports.py")
    print("3. Check database: sqlite3 radiology_ai.db (if using SQLite)")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)