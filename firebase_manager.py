import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import os
import json

class FirebaseManager:
    """Firebase integration for user management and data sync"""
    
    def __init__(self, credentials_path='firebase-credentials.json'):
        """Initialize Firebase"""
        self.credentials_path = credentials_path
        self.db = None
        self.bucket = None
        self.initialized = False
        
        self.init_firebase()
    
    def init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                if os.path.exists(self.credentials_path):
                    cred = credentials.Certificate(self.credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': 'attendance-system-839ae'  
                    })
                    self.db = firestore.client()
                    self.bucket = storage.bucket()
                    self.initialized = True
                    return True, "Firebase initialized successfully"
                else:
                    return False, f"Credentials file not found: {self.credentials_path}"
            else:
                self.db = firestore.client()
                self.bucket = storage.bucket()
                self.initialized = True
                return True, "Firebase already initialized"
        except Exception as e:
            return False, f"Firebase initialization error: {str(e)}"
    
    def add_user(self, name, email=None, department=None):
        """Add user to Firebase"""
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            user_data = {
                'name': name,
                'email': email or '',
                'department': department or '',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            
            # Add to Firestore
            doc_ref = self.db.collection('users').document(name)
            doc_ref.set(user_data)
            
            return True, f"User {name} added to Firebase"
        except Exception as e:
            return False, f"Error adding user to Firebase: {str(e)}"
    
    def get_user(self, name):
        """Get user from Firebase"""
        if not self.initialized:
            return None
        
        try:
            doc_ref = self.db.collection('users').document(name)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
    
    def update_user(self, name, updates):
        """Update user information"""
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection('users').document(name)
            doc_ref.update(updates)
            
            return True, f"User {name} updated"
        except Exception as e:
            return False, f"Error updating user: {str(e)}"
    
    def delete_user(self, name):
        """Delete user from Firebase"""
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            doc_ref = self.db.collection('users').document(name)
            doc_ref.delete()
            
            return True, f"User {name} deleted from Firebase"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
    
    def get_all_users(self):
        """Get all users from Firebase"""
        if not self.initialized:
            return []
        
        try:
            users_ref = self.db.collection('users')
            docs = users_ref.stream()
            
            users = []
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                users.append(user_data)
            
            return users
        except Exception as e:
            print(f"Error getting users: {str(e)}")
            return []
    
    def log_attendance(self, name, punch_type, timestamp=None):
        """Log attendance to Firebase"""
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            attendance_data = {
                'user_name': name,
                'punch_type': punch_type,
                'timestamp': timestamp,
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S')
            }
            
            # Add to Firestore
            self.db.collection('attendance').add(attendance_data)
            
            return True, "Attendance logged to Firebase"
        except Exception as e:
            return False, f"Error logging attendance: {str(e)}"
    
    def get_user_attendance(self, name, days=7):
        """Get user attendance from Firebase"""
        if not self.initialized:
            return []
        
        try:
            from datetime import timedelta
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            attendance_ref = self.db.collection('attendance')
            query = attendance_ref.where('user_name', '==', name).where('date', '>=', start_date)
            docs = query.stream()
            
            records = []
            for doc in docs:
                records.append(doc.to_dict())
            
            return records
        except Exception as e:
            print(f"Error getting attendance: {str(e)}")
            return []
    
    def sync_local_to_firebase(self, local_tracker):
        """Sync local SQLite data to Firebase"""
        if not self.initialized:
            return False, "Firebase not initialized"
        
        try:
            # Sync users
            local_users = local_tracker.get_all_users()
            synced_users = 0
            
            for user in local_users:
                self.add_user(user)
                synced_users += 1
            
            return True, f"Synced {synced_users} users to Firebase"
        except Exception as e:
            return False, f"Sync error: {str(e)}"
    
    def is_initialized(self):
        """Check if Firebase is initialized"""
        return self.initialized


class HybridStorage:
    """Use both SQLite (local) and Firebase (cloud) storage"""
    
    def __init__(self, local_tracker, firebase_manager):
        self.local = local_tracker
        self.firebase = firebase_manager
    
    def add_user(self, name, email=None, department=None):
        """Add user to both local and Firebase"""
        # Add to local SQLite
        local_success, local_msg = self.local.add_user(name)
        
        # Try to add to Firebase
        if self.firebase.is_initialized():
            firebase_success, firebase_msg = self.firebase.add_user(name, email, department)
            
            if local_success:
                return True, f"{local_msg} | Firebase: {firebase_msg}"
            else:
                return False, local_msg
        else:
            return local_success, local_msg
    
    def punch(self, name, punch_type):
        """Record punch in both local and Firebase"""
        # Record in local SQLite
        local_success, local_msg = self.local.punch(name, punch_type)
        
        # Try to sync to Firebase
        if local_success and self.firebase.is_initialized():
            self.firebase.log_attendance(name, punch_type)
        
        return local_success, local_msg
    
    def delete_user(self, name):
        """Delete user from both local and Firebase"""
        # Delete from local
        local_success, local_msg = self.local.delete_user(name)
        
        # Try to delete from Firebase
        if self.firebase.is_initialized():
            firebase_success, firebase_msg = self.firebase.delete_user(name)
            
            if local_success:
                return True, f"{local_msg} | Firebase: {firebase_msg}"
            else:
                return False, local_msg
        else:
            return local_success, local_msg
    
    def get_all_users(self):
        """Get users from local storage"""
        return self.local.get_all_users()
    
    def get_today_status(self, name):
        """Get today's status from local storage"""
        return self.local.get_today_status(name)
    
    def get_user_history(self, name, days=7):
        """Get user history from local storage"""
        return self.local.get_user_history(name, days)
    
    def get_statistics(self, start_date=None, end_date=None):
        """Get statistics from local storage"""
        return self.local.get_statistics(start_date, end_date)
    
    def get_attendance_summary(self, date=None):
        """Get attendance summary from local storage"""
        return self.local.get_attendance_summary(date)
