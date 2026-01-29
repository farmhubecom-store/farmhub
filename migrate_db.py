#!/usr/bin/env python3
"""
Manual database migration script for Render deployment
Run this script on Render to add the commission_paid column to the Shop table
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import db, auto_migrate_database

if __name__ == "__main__":
    print("Running manual database migration for Render...")

    # Import the app context
    from app import app

    with app.app_context():
        success = auto_migrate_database()

    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)