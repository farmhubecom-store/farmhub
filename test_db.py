#!/usr/bin/env python3
"""Test script to verify database migration"""
from app import db, app, Shop

print("Testing database connection and migration...")

with app.app_context():
    try:
        # Test if we can query the Shop table
        shops_count = db.session.query(db.func.count(Shop.id)).scalar()
        print(f"✓ Successfully connected to database. Found {shops_count} shops.")

        # Test if commission_paid column exists by trying to query it
        shop = Shop.query.first()
        if shop:
            commission_paid = getattr(shop, 'commission_paid', None)
            if commission_paid is not None:
                print("✓ commission_paid column is accessible")
                print(f"✓ Sample shop commission_paid value: {commission_paid}")
            else:
                print("✗ commission_paid column not found")
        else:
            print("No shops found to test column access")

    except Exception as e:
        print(f"✗ Database error: {e}")

print("Test completed.")