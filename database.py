import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

class Database:
    """SQLite database for attendance system"""
    
    def __init__(self, db_path='data/attendance.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Attendance records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    punch_type TEXT NOT NULL,
                    punch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    CHECK (punch_type IN ('in', 'out', 'break', 'lunch'))
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_user_date 
                ON attendance(user_id, date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_date 
                ON attendance(date)
            ''')


class AttendanceTracker:
    """Attendance tracking with SQLite backend"""
    
    def __init__(self, db_path='data/attendance.db'):
        self.db = Database(db_path)
    
    def add_user(self, name):
        """Add a new user to the database"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (name) VALUES (?)', (name,))
                return True, f"User {name} added successfully"
        except sqlite3.IntegrityError:
            return False, f"User {name} already exists"
        except Exception as e:
            return False, f"Error adding user: {str(e)}"
    
    def get_user_id(self, name):
        """Get user ID by name"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE name = ?', (name,))
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def punch(self, name, punch_type):
        """Record punch in/out"""
        # Ensure user exists
        user_id = self.get_user_id(name)
        if not user_id:
            success, msg = self.add_user(name)
            if not success:
                return False, msg
            user_id = self.get_user_id(name)
        
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        
        # Check if already punched same type recently (within last 5 minutes)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT punch_type, punch_time 
                FROM attendance 
                WHERE user_id = ? AND date = ?
                ORDER BY punch_time DESC 
                LIMIT 1
            ''', (user_id, date))
            
            last_record = cursor.fetchone()
            
            if last_record and last_record['punch_type'] == punch_type:
                last_time = datetime.strptime(last_record['punch_time'], '%Y-%m-%d %H:%M:%S')
                if (now - last_time).seconds < 300:  # 5 minutes
                    return False, f"Already punched {punch_type} at {last_time.strftime('%H:%M:%S')}"
            
            # Insert new record
            cursor.execute('''
                INSERT INTO attendance (user_id, punch_type, punch_time, date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, punch_type, now.strftime('%Y-%m-%d %H:%M:%S'), date))
            
            return True, f"Punched {punch_type} successfully at {time}"
    
    def get_today_status(self, name):
        """Get today's status for a user"""
        user_id = self.get_user_id(name)
        if not user_id:
            return "Not registered"
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT punch_type, punch_time 
                FROM attendance 
                WHERE user_id = ? AND date = ?
                ORDER BY punch_time DESC 
                LIMIT 1
            ''', (user_id, today))
            
            record = cursor.fetchone()
            
            if not record:
                return "Not punched in"
            
            time = datetime.strptime(record['punch_time'], '%Y-%m-%d %H:%M:%S')
            return f"Punched {record['punch_type'].upper()} at {time.strftime('%H:%M:%S')}"
    
    def get_user_history(self, name, days=7):
        """Get recent attendance for a user"""
        user_id = self.get_user_id(name)
        if not user_id:
            return {}
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, punch_type, punch_time
                FROM attendance
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC, punch_time DESC
            ''', (user_id, start_date))
            
            records = cursor.fetchall()
            
            # Group by date
            history = {}
            for record in records:
                date = record['date']
                if date not in history:
                    history[date] = []
                
                time = datetime.strptime(record['punch_time'], '%Y-%m-%d %H:%M:%S')
                history[date].append({
                    'type': record['punch_type'],
                    'time': time.strftime('%H:%M:%S')
                })
            
            return history
    
    def get_all_users(self):
        """Get all registered users"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM users ORDER BY name')
            return [row['name'] for row in cursor.fetchall()]
    
    def get_attendance_summary(self, date=None):
        """Get attendance summary for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.name, a.punch_type, a.punch_time
                FROM users u
                LEFT JOIN attendance a ON u.id = a.user_id AND a.date = ?
                ORDER BY u.name, a.punch_time
            ''', (date,))
            
            records = cursor.fetchall()
            
            # Group by user
            summary = {}
            for record in records:
                name = record['name']
                if name not in summary:
                    summary[name] = []
                
                if record['punch_time']:
                    time = datetime.strptime(record['punch_time'], '%Y-%m-%d %H:%M:%S')
                    summary[name].append({
                        'type': record['punch_type'],
                        'time': time.strftime('%H:%M:%S')
                    })
            
            return summary
    
    def delete_user(self, name):
        """Delete a user and their attendance records"""
        user_id = self.get_user_id(name)
        if not user_id:
            return False, "User not found"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete attendance records first (foreign key constraint)
                cursor.execute('DELETE FROM attendance WHERE user_id = ?', (user_id,))
                
                # Delete user
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                
                return True, f"User {name} and all records deleted"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
    
    def get_statistics(self, start_date=None, end_date=None):
        """Get attendance statistics"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total punches by type
            cursor.execute('''
                SELECT punch_type, COUNT(*) as count
                FROM attendance
                WHERE date BETWEEN ? AND ?
                GROUP BY punch_type
            ''', (start_date, end_date))
            
            type_stats = {row['punch_type']: row['count'] for row in cursor.fetchall()}
            
            # Punches by user
            cursor.execute('''
                SELECT u.name, COUNT(a.id) as punch_count
                FROM users u
                LEFT JOIN attendance a ON u.id = a.user_id 
                    AND a.date BETWEEN ? AND ?
                GROUP BY u.name
                ORDER BY punch_count DESC
            ''', (start_date, end_date))
            
            user_stats = {row['name']: row['punch_count'] for row in cursor.fetchall()}
            
            # Daily attendance count
            cursor.execute('''
                SELECT date, COUNT(DISTINCT user_id) as users_present
                FROM attendance
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date DESC
            ''', (start_date, end_date))
            
            daily_stats = {row['date']: row['users_present'] for row in cursor.fetchall()}
            
            return {
                'by_type': type_stats,
                'by_user': user_stats,
                'daily': daily_stats
            }
