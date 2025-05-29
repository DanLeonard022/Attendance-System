import time
import serial
import RPi.GPIO as GPIO
import threading
from pyfingerprint.pyfingerprint import PyFingerprint
from datetime import datetime
from RPLCD.i2c import CharLCD
from fpdf import FPDF
import sqlite3
from tkinter import DISABLED, NORMAL
from firebase_sync import FirebaseSync
from email_handler import EmailHandler

# Setup GPIO pins for feedback (LEDs and buzzer)
GREEN_LED = 27  
RED_LED = 17    
BUZZER_PIN = 18 

GPIO.setwarnings(False)  # Disable warnings
GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Initialize LCD
lcd = CharLCD('PCF8574', 0x27, port=1, cols=16, rows=2)
lcd.clear()
lcd.write_string("System Ready")

class AttendanceApp:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.attendance_running = False
        self.students = {}
        self.position_to_student_id = {}
        self.present_threshold = 10  # minutes (considered present if within 10 mins)
        self.late_threshold = 15
        self.current_course = None
        self.current_section = None
        self.current_subject = None

        # Initialize DB connection
        self.db_conn = sqlite3.connect('professor_account.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()

        # Initialize Firebase sync
        self.firebase_sync = FirebaseSync()
        self.firebase_sync.start_sync()
        
        self.email_handler = EmailHandler(
            sender_email="bio.hunters10@gmail.com",
            sender_password="ljab fqkc ptdf qwzk"
        )

        # Create or recreate tables
        self._create_tables()

        # Load student list
        self._load_students()

        # Initialize fingerprint sensor
        try:
            self.finger = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
            if not self.finger.verifyPassword():
                raise ValueError('The given fingerprint sensor password is wrong!')
        except Exception as e:
            print(f'Fingerprint sensor initialization failed: {str(e)}')
            self.finger = None


    def verify_database_schema(self):
        """Verify all required tables and columns exist"""
        try:
            # Check attendance table
            self.cursor.execute("PRAGMA table_info(attendance)")
            attendance_cols = {col[1] for col in self.cursor.fetchall()}
            required = {'student_id', 'time_in', 'status', 'synced'}
            if not required.issubset(attendance_cols):
                return False
                
            # Check students table
            self.cursor.execute("PRAGMA table_info(students)")
            student_cols = {col[1] for col in self.cursor.fetchall()}
            required = {'student_id', 'name', 'fingerprint_position'}
            return required.issubset(student_cols)
            
        except sqlite3.Error:
            return False
    def _create_tables(self):
        """Create or update database tables with all required columns"""
        try:
            # Enable foreign key support
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create students table first since attendance references it
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    fingerprint_position INTEGER
                )
            ''')
            
            # Check if columns exist, if not add them
            self.cursor.execute("PRAGMA table_info(students)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'email' not in columns:
                self.cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
            if 'fingerprint_position' not in columns:
                self.cursor.execute("ALTER TABLE students ADD COLUMN fingerprint_position INTEGER")
            
            # Now create attendance table with foreign key
            self.cursor.execute("DROP TABLE IF EXISTS attendance")
            self.cursor.execute('''
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    time_in TEXT NOT NULL,
                    status TEXT DEFAULT 'Present',
                    synced INTEGER DEFAULT 0,
                    course_name TEXT,
                    section_name TEXT,
                    subject_name TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
                )
            ''')
            
            self.db_conn.commit()
            print("Database setup complete.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            if hasattr(self, 'db_conn'):
                self.db_conn.rollback()

        
    def _load_students(self):
        """Load students from database into memory."""
        try:
            # First check if the fingerprint_position column exists
            self.cursor.execute("PRAGMA table_info(students)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'fingerprint_position' in columns:
                self.cursor.execute("SELECT student_id, name, fingerprint_position FROM students")
                for student_id, name, position in self.cursor.fetchall():
                    self.students[student_id] = name
                    if position is not None:  # Only add if position exists
                        self.position_to_student_id[position] = student_id
            else:
                # Fallback if column doesn't exist
                self.cursor.execute("SELECT student_id, name FROM students")
                for student_id, name in self.cursor.fetchall():
                    self.students[student_id] = name
        except sqlite3.Error as e:
            print(f"Error loading students: {e}")
    
    def start_attendance(self):
        """Start attendance monitoring."""
        if not self.finger:
            lcd.clear()
            lcd.write_string("Sensor Not Ready")
            return False
            
        self.attendance_running = True
        self.attendance_start_time = datetime.now()
        
        # Update UI if parent frame is available
        if hasattr(self.parent_frame, 'start_button'):
            self.parent_frame.start_button.config(state=DISABLED)
        if hasattr(self.parent_frame, 'stop_button'):
            self.parent_frame.stop_button.config(state=NORMAL)
        
        lcd.clear()
        lcd.write_string("Scan Fingerprint")
        
        # Start attendance thread
        self.attendance_thread = threading.Thread(target=self._monitor_attendance, daemon=True)
        self.attendance_thread.start()
        return True
    
    def stop_attendance(self):
        """Stop attendance process."""
        self.attendance_running = False
        if hasattr(self.parent_frame, 'start_button'):
            self.parent_frame.start_button.config(state=NORMAL)
        if hasattr(self.parent_frame, 'stop_button'):
            self.parent_frame.stop_button.config(state=DISABLED)
        
        lcd.clear()
        lcd.write_string("Attendance Stopped")
        time.sleep(1)
        lcd.clear()
        lcd.write_string("System Ready")
    
    def _monitor_attendance(self):
        """Continuously monitor for fingerprint scans."""
        while self.attendance_running:
            try:
                if self.finger.readImage():
                    self.finger.convertImage(0x01)
                    position, accuracy = self.finger.searchTemplate()
                    
                    if position >= 0:
                        student_id = self.position_to_student_id.get(position, "Unknown")
                        self._process_attendance(student_id)
                    else:
                        self._show_error("Finger not found")
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Scan error: {e}")
                self._show_error("Scan Error")
                time.sleep(1)
    
    def _process_attendance(self, student_id):
        """Process a successful fingerprint scan with status calculation"""
        current_time = datetime.now()
        time_in_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate minutes late
        minutes_late = (current_time - self.attendance_start_time).total_seconds() / 60
        
        # Determine status
        if minutes_late <= self.present_threshold:
            status = "Present"
        elif minutes_late <= self.late_threshold:
            status = "Late"
        else:
            status = "Absent"
        
        # Get student info
        self.cursor.execute("SELECT name, email FROM students WHERE student_id = ?", (student_id,))
        student_data = self.cursor.fetchone()
        
        if not student_data:
            self._show_error("Student not found")
            return
            
        student_name, student_email = student_data[0], student_data[1]

        # Visual and audio feedback
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        
        # Display on LCD
        lcd.clear()
        lcd.write_string(f"ID: {student_id}")
        lcd.crlf()
        lcd.write_string(f"Status: {status}")
        
        # Save to database
        self._save_attendance(student_id, time_in_str, status)
        
        # Send email notification
        if student_email:
            try:
                subject = f"Attendance Recorded - {status}"
                body = f"""Your attendance has been recorded:

Student ID: {student_id}
Name: {student_name}
Time In: {time_in_str}
Status: {status}

Thank you!"""
                
                email_thread = threading.Thread(
                    target=self.email_handler.send_email_reminder,
                    args=(student_email, subject, body),
                    daemon=True
                )
                email_thread.start()
            except Exception as e:
                print(f"Error sending email: {e}")

        time.sleep(1)
        GPIO.output(GREEN_LED, GPIO.LOW)
    
    def _show_error(self, message):
        """Show error feedback."""
        GPIO.output(RED_LED, GPIO.HIGH)
        lcd.clear()
        lcd.write_string(message)
        time.sleep(1)
        GPIO.output(RED_LED, GPIO.LOW)
        lcd.clear()
        lcd.write_string("Scan Fingerprint")
    
    def _save_attendance(self, student_id, time_in, status):
        """Save attendance record to database."""
        try:
            # First verify the student exists
            self.cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
            if not self.cursor.fetchone():
                print(f"Student {student_id} not found in database")
                self._show_error("Student not found")
                return

            self.cursor.execute(
                """INSERT INTO attendance 
                (student_id, time_in, status, synced, 
                 course_name, section_name, subject_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (student_id, time_in, status, 0,
                 self.current_course, self.current_section, self.current_subject)
            )
            self.db_conn.commit()
            
            # Update UI if available
            if hasattr(self.parent_frame, 'attendance_tree'):
                self.parent_frame.attendance_tree.insert(
                    "", "end", 
                    values=(student_id, self.students.get(student_id, "Unknown"), time_in,
                           self.current_course, self.current_section, self.current_subject))
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self._show_error("DB Error")
    
    def enroll_fingerprint(self, student_id, name, email=None):
        """Enroll a new fingerprint for a student (universal registration)"""
        if not self.finger:
            return False, "Fingerprint sensor not available"
        
        try:
            # Check if student already exists in the system
            self.cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
            student_exists = self.cursor.fetchone()
            
            lcd.clear()
            lcd.write_string("Place finger")
            
            # Wait for finger to be placed
            while not self.finger.readImage():
                pass
            
            self.finger.convertImage(0x01)
            
            # Check if finger already exists
            position, accuracy = self.finger.searchTemplate()
            if position >= 0:
                return False, "Fingerprint already registered"
            
            lcd.clear()
            lcd.write_string("Remove finger")
            time.sleep(2)
            
            lcd.clear()
            lcd.write_string("Place again")
            
            # Get second image
            while not self.finger.readImage():
                pass
            
            self.finger.convertImage(0x02)
            
            # Verify both images match
            if self.finger.compareCharacteristics() == 0:
                return False, "Fingerprints don't match"
            
            # Store template
            position = self.finger.storeTemplate()
            
            # Save to database
            try:
                if not student_exists:
                    # Add new student if doesn't exist
                    self.cursor.execute(
                        "INSERT INTO students (student_id, name, email, fingerprint_position) VALUES (?, ?, ?, ?)",
                        (student_id, name, email, position)
                    )
                else:
                    # Update existing student's fingerprint
                    self.cursor.execute(
                        "UPDATE students SET fingerprint_position = ? WHERE student_id = ?",
                        (position, student_id)
                    )
                
                # Link student to current professor
                if hasattr(self.parent_frame, 'current_professor'):
                    professor_id = self.parent_frame.current_professor
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO professor_students (professor_id, student_id) VALUES (?, ?)",
                        (professor_id, student_id)
                    )
                
                self.db_conn.commit()
                
                # Update in-memory records
                self.students[student_id] = name
                self.position_to_student_id[position] = student_id
                
                return True, f"Enrollment successful (Position: {position})"
            except sqlite3.Error as e:
                return False, f"Database error: {e}"
                
        except Exception as e:
            return False, f"Enrollment error: {e}"
        finally:
            lcd.clear()
            lcd.write_string("System Ready")
    
    def generate_report(self, filename="attendance_report.pdf"):
        """Generate PDF attendance report."""
        try:
            self.cursor.execute("SELECT student_id, time_in, status FROM attendance")
            records = self.cursor.fetchall()
            
            if not records:
                return False, "No attendance records found"
            
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Attendance Report", ln=True, align='C')
            pdf.ln(10)
            
            # Header
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, "Student ID", border=1)
            pdf.cell(70, 10, "Time In", border=1)
            pdf.cell(50, 10, "Status", border=1)
            pdf.ln()
            
            # Data
            pdf.set_font("Arial", "", 10)
            for student_id, time_in, status in records:
                pdf.cell(50, 10, str(student_id), border=1)
                pdf.cell(70, 10, time_in, border=1)
                pdf.cell(50, 10, status, border=1)
                pdf.ln()
            
            pdf.output(filename)
            return True, f"Report generated: {filename}"
            
        except Exception as e:
            return False, f"Report generation error: {e}"
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
        GPIO.cleanup()
        lcd.clear()
        lcd.close()
