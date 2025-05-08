# database.py
import sqlite3

class Database:
    def __init__(self):
        self.db_path = 'professor_account.db'
        print(f"Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        print("Setting up database...")
        try:
        
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS professors (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )
            ''')
            
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    professor_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username)
                )
            ''')
            
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    professor_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (course_name) REFERENCES courses(name)
                )
            ''')
            
            # Check if year_level column exists, if not add it
            self.cursor.execute("PRAGMA table_info(sections)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'year_level' not in columns:
                self.cursor.execute("ALTER TABLE sections ADD COLUMN year_level TEXT NOT NULL DEFAULT '1ST YEAR'")
            
            # Create subjects table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    professor_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (course_name, section_name) REFERENCES sections(course_name, name)
                )
            ''')
            
            # Create students table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    fingerprint BLOB
                )
                ''')
            
            # Create professor_students table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS professor_students (
                    professor_id TEXT,
                    student_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    PRIMARY KEY (professor_id, student_id)
                )
            ''')
            
            # Create attendance records table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    subject_id INTEGER,
                    date TEXT,
                    status TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id TEXT,
                    course_name TEXT,
                    section_name TEXT,
                    subject_name TEXT,
                    day TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    room TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (course_name, section_name) REFERENCES sections(course_name, name)
                )
            ''')
            
            self.conn.commit()
            print("Database setup complete.")
        except Exception as e:
            print(f"Error setting up database: {e}")
            self.conn.rollback()
