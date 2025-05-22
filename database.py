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
                
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    professor_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (course_name) REFERENCES courses(name),
                    FOREIGN KEY (section_name) REFERENCES sections(name)
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    time_in TEXT NOT NULL,
                    status TEXT DEFAULT 'Present',
                    synced INTEGER DEFAULT 0,
                    course_name TEXT,
                    section_name TEXT,
                    subject_name TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id)
                )
            ''')
            
            # Updated schema for students table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    fingerprint_position INTEGER
                )
            ''')

            # Check if year_level column exists, if not add it
            self.cursor.execute("PRAGMA table_info(students)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'year_level' not in columns:
                self.cursor.execute("ALTER TABLE students ADD COLUMN year_level TEXT")
            
            if 'email' not in columns:
                self.cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
            
            if 'fingerprint_position' not in columns:
                self.cursor.execute("ALTER TABLE students ADD COLUMN fingerprint_position INTEGER")
            
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_id TEXT,
                course_name TEXT,
                section_name TEXT,
                subject_name TEXT,
                day TEXT CHECK(day IN ('MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY')),
                start_time TEXT,
                end_time TEXT,
                room TEXT,
                FOREIGN KEY (professor_id) REFERENCES professors(username),
                FOREIGN KEY (course_name) REFERENCES courses(name),
                FOREIGN KEY (section_name) REFERENCES sections(name),
                FOREIGN KEY (subject_name) REFERENCES subjects(name)
            )
        ''')
            
            # New enrollment table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS enrollments (
                    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    course_name TEXT,
                    section_name TEXT,
                    subject_name TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    UNIQUE(student_id, course_name, section_name, subject_name)
                )
            ''')
            
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
            print("Database setup complete.")
        except Exception as e:
            print(f"Error setting up database: {e}")
            self.conn.rollback()

    def print_table_structure(self):
        """Print the structure of the attendance table."""
        self.cursor.execute("PRAGMA table_info(attendance)")
        columns = self.cursor.fetchall()
        print("Attendance Table Structure:")
        for column in columns:
            print(column)
