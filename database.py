# database.py
import sqlite3

class Database:
    def __init__(self):
        self.db_path = 'professor_account.db'  # Updated database name
        print(f"Connecting to database: {self.db_path}")  # Debug print
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def setup_database(self):
        print("Setting up database...")  # Debug print
        try:
            # Create professors table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS professors (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )
            ''')
            
            # Create students table with fingerprint column
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    course TEXT NOT NULL,
                    year_level TEXT NOT NULL,
                    fingerprint TEXT  -- Add fingerprint column
                )
            ''')
            
            # Create professor_students table to link professors and students
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS professor_students (
                    professor_id TEXT,
                    student_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    PRIMARY KEY (professor_id, student_id)
                )
            ''')
            
            self.conn.commit()
            print("Database setup complete.")  # Debug print
        except Exception as e:
            print(f"Error setting up database: {e}")  # Debug print
