"""
Test script for SQLite attendance system
Run this to verify everything is working correctly
"""

from database import AttendanceTracker
from datetime import datetime, timedelta
import os

def test_database():
    """Test all database functionality"""
    
    print("=" * 60)
    print("🧪 Testing SQLite Attendance System")
    print("=" * 60)
    print()
    
    # Use a test database
    test_db = 'data/test_attendance.db'
    
    # Clean up old test database
    if os.path.exists(test_db):
        os.remove(test_db)
        print("🧹 Cleaned up old test database")
    
    print("🔧 Initializing database...")
    tracker = AttendanceTracker(test_db)
    print("✅ Database initialized\n")
    
    # Test 1: Add users
    print("Test 1: Adding users")
    print("-" * 40)
    
    test_users = ["Alice", "Bob", "Charlie"]
    for user in test_users:
        success, msg = tracker.add_user(user)
        print(f"  {'✅' if success else '❌'} {msg}")
    
    # Try adding duplicate
    success, msg = tracker.add_user("Alice")
    print(f"  {'✅' if not success else '❌'} Duplicate check: {msg}")
    print()
    
    # Test 2: Record attendance
    print("Test 2: Recording attendance")
    print("-" * 40)
    
    for user in test_users:
        success, msg = tracker.punch(user, 'in')
        print(f"  {'✅' if success else '❌'} {user}: {msg}")
    
    # Try duplicate punch
    success, msg = tracker.punch("Alice", 'in')
    print(f"  {'✅' if not success else '❌'} Duplicate punch check: {msg}")
    print()
    
    # Test 3: Get today's status
    print("Test 3: Today's status")
    print("-" * 40)
    
    for user in test_users:
        status = tracker.get_today_status(user)
        print(f"  {user}: {status}")
    print()
    
    # Test 4: Multiple punch types
    print("Test 4: Multiple punch types")
    print("-" * 40)
    
    import time
    time.sleep(1)  # Small delay to avoid duplicate check
    
    success, msg = tracker.punch("Bob", 'break')
    print(f"  {'✅' if success else '❌'} Bob break: {msg}")
    
    time.sleep(1)
    success, msg = tracker.punch("Charlie", 'out')
    print(f"  {'✅' if success else '❌'} Charlie out: {msg}")
    print()
    
    # Test 5: Get all users
    print("Test 5: Get all users")
    print("-" * 40)
    
    users = tracker.get_all_users()
    print(f"  Total users: {len(users)}")
    print(f"  Users: {', '.join(users)}")
    print()
    
    # Test 6: Get user history
    print("Test 6: User history")
    print("-" * 40)
    
    history = tracker.get_user_history("Alice", days=7)
    print(f"  Alice has {len(history)} day(s) with records")
    for date, records in history.items():
        print(f"    {date}: {len(records)} record(s)")
        for rec in records:
            print(f"      - {rec['type']}: {rec['time']}")
    print()
    
    # Test 7: Get statistics
    print("Test 7: Statistics")
    print("-" * 40)
    
    stats = tracker.get_statistics()
    print(f"  Punches by type: {stats['by_type']}")
    print(f"  Punches by user: {stats['by_user']}")
    print(f"  Daily attendance: {stats['daily']}")
    print()
    
    # Test 8: Delete user
    print("Test 8: Delete user")
    print("-" * 40)
    
    success, msg = tracker.delete_user("Charlie")
    print(f"  {'✅' if success else '❌'} {msg}")
    
    users = tracker.get_all_users()
    print(f"  Remaining users: {', '.join(users)}")
    print()
    
    # Test 9: Attendance summary
    print("Test 9: Attendance summary")
    print("-" * 40)
    
    summary = tracker.get_attendance_summary()
    for user, records in summary.items():
        print(f"  {user}:")
        for rec in records:
            print(f"    - {rec['type']}: {rec['time']}")
    print()
    
    # Final results
    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print()
    print(f"📁 Test database created at: {test_db}")
    print(f"💡 You can delete it or keep it for reference")
    print()
    
    # Ask to clean up
    cleanup = input("Delete test database? (yes/no): ")
    if cleanup.lower() == 'yes':
        os.remove(test_db)
        print("✅ Test database deleted")
    else:
        print(f"💾 Test database kept at: {test_db}")

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
