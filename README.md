# Face Attendance System – SQLite Edition

## Overview
This is an upgraded version of the Face Attendance System that replaces JSON-based storage with an SQLite database. The migration improves data integrity, query performance, scalability, and long-term maintainability while keeping the face recognition pipeline unchanged.

---

## What’s New

### SQLite Database Enhancements
- Relational schema with proper foreign key constraints
- Faster data access using indexed queries
- Improved data integrity through transactions and constraints
- Support for advanced analytical queries and reporting
- Safe concurrent read/write access
- Simplified backup using a single database file

### Application Features
- Statistics dashboard for attendance analytics
- Date-range filtering for historical records
- User management with cascading record deletion
- Multiple punch types (IN, OUT, BREAK, LUNCH)
- Visual analytics using bar and line charts
- Faster data retrieval and processing

---

## Project Structure
├── app_sqlite.py # Streamlit application using SQLite
├── database.py # SQLite database logic and attendance tracker
├── face_system.py # Face recognition module (unchanged)
├── migrate_to_sqlite.py # Migration script (JSON → SQLite)
├── requirements.txt # Python dependencies
└── data/
├── attendance.db # SQLite database (auto-generated)
└── faces/ # Stored face encodings


---

## Getting Started

### Option 1: Fresh Installation
Use this option if starting without existing data.

```bash
pip install -r requirements.txt
streamlit run app_sqlite.py
```

Option 2: Migrate from JSON

Use this option if you already have attendance data stored in JSON.
```bash
pip install -r requirements.txt
python migrate_to_sqlite.py
cp data/attendance/records.json data/attendance/records.json.backup
streamlit run app_sqlite.py
```
## Application Usage

### 1. Mark Attendance
- Capture image via camera
- Face recognition identifies the user
- Select punch type:
  - IN
  - OUT
  - BREAK
  - LUNCH
- View real-time attendance status

---

### 2. Register New User
- Enter user name
- Capture 10–15 facial samples
- Train the face recognition model
- Persist user data in the database

---

### 3. View Attendance Records
- View records for a specific user or all users
- Filter records by date range
- Export functionality (planned)

---

### 4. Statistics & Analytics
- View attendance trends over time
- Analyze punch-type distribution
- Daily attendance summaries
- Detailed statistical breakdowns

---

### 5. System Settings
- Delete users and their related attendance records
- View database status
- Administrative tools (planned)

---

## Troubleshooting

### Database Locked Error
- Ensure no other processes are accessing the database
- Use context-managed database connections

---

### Migration Failure
- Validate JSON file structure
- Ensure correct directory permissions
- Confirm required paths exist

---

### Performance Issues
- Indexes are created automatically
- Large datasets may require additional query optimization
