# firebase_sync.py
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import threading
import time
import json
from datetime import datetime

class FirebaseSync:
    def __init__(self, db_path='professor_account.db'):
        self.db_path = db_path
        self.connected = False
        self.sync_interval = 60  # seconds between sync attempts
        self.firebase_app = None
        self.init_firebase()
        
    def init_firebase(self):
        if firebase_admin._apps:  # Already initialized
            self.firebase_app = firebase_admin.get_app()
            self.connected = True
            return
            
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
            self.firebase_app = firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ams-project-b6b30-default-rtdb.firebaseio.com/'
            })
            self.connected = True
            print("Firebase connection established")
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.connected = False
    
    def start_sync(self):
        """Start background sync thread"""
        sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        sync_thread.start()
    
    def _sync_loop(self):
        """Continuous sync loop"""
        while True:
            if not self.connected:
                try:
                    self.init_firebase()
                except Exception as e:
                    print(f"Reconnection failed: {e}")
                    time.sleep(self.sync_interval)
                    continue
            
            try:
                self.sync_all_tables()
            except Exception as e:
                print(f"Sync error: {e}")
                self.connected = False
            time.sleep(self.sync_interval)
    
    def sync_all_tables(self):
        """Sync all relevant tables"""
        if not self.connected:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Sync professors table (excluding password field)
            self._sync_table(cursor, 'professors', 'professors', exclude_fields=['password'])
            
            # Sync students table (excluding binary fingerprint data)
            self._sync_table(cursor, 'students', 'students', exclude_fields=['fingerprint'])
            
            # Sync courses table
            self._sync_table(cursor, 'courses', 'courses')
            
            # Sync sections table
            self._sync_table(cursor, 'sections', 'sections')
            
            # Sync subjects table
            self._sync_table(cursor, 'subjects', 'subjects')
            
            # Sync attendance - only sync unsynced records
            self._sync_attendance(cursor)
            
            print("Sync completed at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        finally:
            conn.close()
    
    def _sync_table(self, cursor, table_name, firebase_path, exclude_fields=None):
        """Sync a single table"""
        if exclude_fields is None:
            exclude_fields = []
            
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Filter out excluded columns
        select_columns = [col for col in columns if col not in exclude_fields]
        
        # Build the SELECT query properly
        if not select_columns:
            print(f"No columns to sync for {table_name} after exclusions")
            return
            
        # Properly format the column names in the SELECT statement
        quoted_columns = [f'"{col}"' for col in select_columns]
        select_query = f"SELECT {', '.join(quoted_columns)} FROM \"{table_name}\""
        
        try:
            cursor.execute(select_query)
            rows = cursor.fetchall()
            
            # Convert rows to dicts with only selected columns
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(select_columns):
                    value = row[i]
                    if value is None:
                        continue
                    if isinstance(value, (bytes, bytearray)):
                        continue  # Skip binary data
                    row_dict[col] = str(value) if not isinstance(value, (str, int, float, bool)) else value
                data.append(row_dict)
            
            # Push to Firebase
            ref = db.reference(firebase_path)
            ref.set(data)
            print(f"Successfully synced {len(data)} records from {table_name}")
        except Exception as e:
            print(f"Error syncing table {table_name}: {e}")
            raise
    
    def _sync_attendance(self, cursor):
        """Sync attendance records that haven't been synced yet"""
        # Get unsynced records
        cursor.execute("""
            SELECT a.id, a.student_id, a.time_in, a.status, 
                   a.course_name, a.section_name, a.subject_name,
                   s.name as student_name 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.synced = 0
        """)
        
        # Get column names from description
        columns = [col[0] for col in cursor.description]
        
        # Prepare data for Firebase
        unsynced_data = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            # Convert datetime string to timestamp if needed
            if 'time_in' in row_dict:
                row_dict['timestamp'] = row_dict['time_in']
            unsynced_data.append(row_dict)
        
        if unsynced_data:
            # Push to Firebase
            ref = db.reference('attendance')
            for record in unsynced_data:
                try:
                    new_ref = ref.push()
                    new_ref.set(record)
                    
                    # Mark as synced in SQLite
                    cursor.execute("""
                        UPDATE attendance 
                        SET synced = 1 
                        WHERE id = ?
                    """, (record['id'],))
                    cursor.connection.commit()
                except Exception as e:
                    print(f"Failed to sync attendance record {record['id']}: {e}")
                    cursor.connection.rollback()
    
    def check_connection(self):
        """Check if Firebase connection is active"""
        return self.connected
