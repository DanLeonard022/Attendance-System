# database.py
import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('professor_student.db')
        self.cursor = self.conn.cursor()

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS students (
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            suffix TEXT,
            student_number TEXT PRIMARY KEY,
            course TEXT,
            section TEXT,
            year_level TEXT
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS professors (
            username TEXT PRIMARY KEY,
            password TEXT
        )''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                suffix TEXT,
                age TEXT,
                birthdate TEXT,
                email TEXT UNIQUE,
                cell_number TEXT,
                fingerprint_status TEXT
            )
        ''')
        self.conn.commit()