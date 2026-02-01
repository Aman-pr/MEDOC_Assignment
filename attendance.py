import json
import os
from datetime import datetime

class AttendanceTracker:
    """Simple attendance tracking"""
    
    def __init__(self, data_file='data/attendance/records.json'):
        self.data_file = data_file
        self.records = self.load()
    
    def load(self):
        """load attendance records"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self):
        """save attendance records"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.records, f, indent=2)
    
    def punch(self, name, punch_type):
        """record punch in/out"""
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        
        if name not in self.records:
            self.records[name] = {}
        
        if date not in self.records[name]:
            self.records[name][date] = []
        
        # check if already punched same type recently
        if len(self.records[name][date]) > 0:
            last = self.records[name][date][-1]
            if last['type'] == punch_type:
                return False, f"Already punched {punch_type} at {last['time']}"
        
        record = {
            'type': punch_type,
            'time': time
        }
        
        self.records[name][date].append(record)
        self.save()
        
        return True, f"Punched {punch_type} successfully at {time}"
    
    def get_today_status(self, name):
        """get today's status for a user"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if name not in self.records or today not in self.records[name]:
            return "Not punched in"
        
        records = self.records[name][today]
        if len(records) == 0:
            return "Not punched in"
        
        last = records[-1]
        return f"Punched {last['type'].upper()} at {last['time']}"
    
    def get_user_history(self, name, days=7):
        """get recent attendance for a user"""
        if name not in self.records:
            return {}
        
        # get last N days
        all_dates = sorted(self.records[name].keys(), reverse=True)
        recent = {date: self.records[name][date] for date in all_dates[:days]}
        
        return recent