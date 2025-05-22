# firebase_sync.py
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import threading
import time
import json
from datetime import datetime
import requests

class FirebaseSync:
    def __init__(self, db_path='professor_account.db'):
        self.db_path = db_path
        self.connected = False
        self.sync_interval = 60  # seconds between sync attempts
        self.firebase_app = None
        self.offline_queue = []
        self.init_firebase()
        
    def init_firebase(self):
        if firebase_admin._apps:  # Already initialized
            self.firebase_app = firebase_admin.get_app()
            self.connected = True
            return
            
        try:
            # First check internet connection
            if not self.check_internet_connection():
                self.connected = False
                print("No internet connection - working in offline mode")
                return
                
            cred = credentials.Certificate("serviceAccountKey.json")
            self.firebase_app = firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://ams-project-b6b30-default-rtdb.firebaseio.com/'
            })
            self.connected = True
            print("Firebase connection established")
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.connected = False
    
    def check_internet_connection(self, url="http://www.google.com", timeout=5):
        """Check if there's an internet connection"""
        try:
            requests.get(url, timeout=timeout)
            return True
        except requests.ConnectionError:
            return False
    
    def start_sync(self):
        """Start background sync thread"""
        sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        sync_thread.start()
    
    def _sync_loop(self):
        """Continuous sync loop with offline handling"""
        while True:
            if not self.connected:
                try:
                    # Try to reconnect
                    self.init_firebase()
                    if self.connected:
                        # Connection restored, process offline queue
                        self._process_offline_queue()
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
    
    def _process_offline_queue(self):
        """Process any data collected while offline"""
        while self.offline_queue:
            try:
                table_name, data = self.offline_queue.pop(0)
                self._sync_table_data(table_name, data)
            except Exception as e:
                print(f"Failed to sync queued data: {e}")
                # Put it back in the queue to try again later
                self.offline_queue.insert(0, (table_name, data))
                break
    
    def sync_all_tables(self):
        """Sync all relevant tables with offline handling"""
        if not self.connected:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            self._sync_table(cursor, 'attendance', 'attendance')
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
        except Exception as e:
            print(f"Sync error: {e}")
            if not self.connected:
                # If we lost connection during sync, queue the data
                self._queue_offline_data(cursor)
        finally:
            conn.close()
    
    def _queue_offline_data(self, cursor):
        """Queue data for sync when connection is restored"""
        # Get all unsynced attendance records
        cursor.execute("""
            SELECT a.id, a.student_id, a.time_in, a.status, 
                   a.course_name, a.section_name, a.subject_name,
                   s.name as student_name 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.synced = 0
        """)
        
        columns = [col[0] for col in cursor.description]
        unsynced_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if unsynced_data:
            self.offline_queue.append(('attendance', unsynced_data))
            print(f"Queued {len(unsynced_data)} attendance records for offline sync")
    
    def _sync_table(self, cursor, table_name, firebase_path, exclude_fields=None):
        """Sync a single table with offline handling"""
        if exclude_fields is None:
            exclude_fields = []
            
        try:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Filter out excluded columns
            select_columns = [col for col in columns if col not in exclude_fields]
            
            if not select_columns:
                print(f"No columns to sync for {table_name} after exclusions")
                return
                
            # Properly format the column names in the SELECT statement
            quoted_columns = [f'"{col}"' for col in select_columns]
            select_query = f"SELECT {', '.join(quoted_columns)} FROM \"{table_name}\""
            
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
            
            if not self.connected:
                self.offline_queue.append((table_name, data))
                print(f"Queued {len(data)} records from {table_name} for offline sync")
                return
                
            # Push to Firebase
            self._sync_table_data(table_name, data, firebase_path)
            
        except Exception as e:
            print(f"Error syncing table {table_name}: {e}")
            raise
    
    def _sync_table_data(self, table_name, data, firebase_path=None):
        """Actually sync data to Firebase"""
        if not firebase_path:
            firebase_path = table_name
            
        ref = db.reference(firebase_path)
        ref.set(data)
        print(f"Successfully synced {len(data)} records from {table_name}")
    
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
            if not self.connected:
                self.offline_queue.append(('attendance', unsynced_data))
                print(f"Queued {len(unsynced_data)} attendance records for offline sync")
                return
                
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
                    if not self.connected:
                        self.offline_queue.append(('attendance', [record]))
                        break
    
    def check_connection(self):
        """Check if Firebase connection is active"""
        return self.connected and self.check_internet_connection()
