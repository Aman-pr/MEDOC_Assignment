"""
Migration script to convert JSON attendance data to SQLite database
Run this once to migrate your existing data
"""

import json
import os
from database import Database, AttendanceTracker
from datetime import datetime

def migrate_json_to_sqlite():
    """Migrate attendance data from JSON to SQLite"""
    
    json_file = 'data/attendance/records.json'
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print("❌ No JSON file found. Nothing to migrate.")
        return
    
    # Load JSON data
    print("📂 Loading JSON data...")
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    print(f"✅ Found {len(json_data)} users in JSON")
    
    # Initialize SQLite database
    print("🔧 Initializing SQLite database...")
    tracker = AttendanceTracker()
    
    total_records = 0
    
    # Migrate each user
    for username, dates in json_data.items():
        print(f"\n👤 Migrating user: {username}")
        
        # Add user to database
        success, msg = tracker.add_user(username)
        if not success and "already exists" not in msg:
            print(f"  ⚠️ Warning: {msg}")
        else:
            print(f"  ✓ User added")
        
        user_id = tracker.get_user_id(username)
        
        # Migrate attendance records
        for date, records in dates.items():
            for record in records:
                # Insert directly into database
                punch_type = record['type']
                time_str = record['time']
                
                # Combine date and time
                datetime_str = f"{date} {time_str}"
                
                with tracker.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO attendance (user_id, punch_type, punch_time, date)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, punch_type, datetime_str, date))
                
                total_records += 1
        
        print(f"  ✓ Migrated {sum(len(records) for records in dates.values())} records")
    
    print(f"\n✅ Migration complete!")
    print(f"📊 Summary:")
    print(f"  - Users migrated: {len(json_data)}")
    print(f"  - Total records: {total_records}")
    print(f"\n💾 Data saved to: data/attendance.db")
    print(f"\n⚠️ IMPORTANT: Backup your JSON file before deleting it!")
    print(f"   Location: {json_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 JSON to SQLite Migration Tool")
    print("=" * 60)
    print()
    
    confirm = input("⚠️ This will create a new SQLite database. Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        migrate_json_to_sqlite()
        print("\n" + "=" * 60)
        print("✅ Migration finished!")
        print("=" * 60)
    else:
        print("\n❌ Migration cancelled.")
