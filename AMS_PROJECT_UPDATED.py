

import time
import serial
import RPi.GPIO as GPIO
from pyfingerprint.pyfingerprint import PyFingerprint
from tkinter import *
from tkinter import ttk
from datetime import datetime
import threading
from RPLCD.i2c import CharLCD
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import requests

# Setup GPIO pins for feedback (LEDs and buzzer)
GREEN_LED = 27  
RED_LED = 17    
BUZZER_PIN = 18 

GPIO.setwarnings(False)  # ✅ Disable warnings
GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# SQLite Database setup
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    time_in TEXT,
    status TEXT,
    synced INTEGER DEFAULT 0
)''')



# Serial Connection Setup
try:
    uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
except serial.SerialException as e:
    print(f"Error initializing serial connection: {e}")
    exit()

# Fingerprint Sensor Initialization
try:
    finger = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
    if not finger.verifyPassword():
        raise ValueError("Fingerprint sensor password is incorrect!")
    print("Fingerprint sensor initialized successfully.")
except Exception as e:
    print(f"Failed to initialize the fingerprint sensor: {e}")
    finger = None

# LCD Setup
lcd = CharLCD('PCF8574', 0x27, port=1, cols=16, rows=2)
lcd.clear()


# Functions for LED and Buzzer
def buzzer():
    """Activate the buzzer for 0.5 seconds."""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def led_feedback(matched):
    """Turn ON Green LED for success, Red LED for failure."""
    if matched:
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(RED_LED, GPIO.LOW)
    else:
        GPIO.output(RED_LED, GPIO.HIGH)
        GPIO.output(GREEN_LED, GPIO.LOW)

    buzzer()  # Buzzer on both success and failure
    time.sleep(1)  # Keep LED on for 1 sec
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)

# Attendance System
students = {}
position_to_student_id = {}

def save_student_data():
    """Save enrolled student data."""
    with open("enrolled_students.txt", "w") as file:
        for position, student_id in position_to_student_id.items():
            file.write(f"{position},{student_id}\n")

def load_student_data():
    """Load saved student data."""
    global position_to_student_id
    position_to_student_id = {}
    try:
        with open("enrolled_students.txt", "r") as file:
            for line in file:
                position, student_id = line.strip().split(",")
                position_to_student_id[int(position)] = student_id
        print("Student data loaded successfully.")
    except FileNotFoundError:
        print("No saved student data found.")


def enroll_fingerprint_procedure(finger):
    """Enroll a fingerprint for a student by capturing multiple parts of the fingerprint."""
    try:
        print("Place your finger on the scanner...")

        # Set up a loop for multiple attempts
        for attempt in range(3):  # 3 attempts to scan the fingerprint
            print(f"Attempt {attempt + 1} of 3: Place your finger on the scanner")
            
            # Read the fingerprint image
            while not finger.readImage():
                pass  # Wait until the image is read

            # Convert the image to a template (for capturing different parts of the fingerprint)
            finger.convertImage(0x01)  # Store template for this part

            # Optionally, you can show a visual feedback on the screen for the user
            print("Fingerprint image captured successfully.")
            
            # Wait a bit and prompt user to lift finger and place it again
            print("Remove your finger, then place it again for next scan...")
            time.sleep(2)  # Wait for 2 seconds before the next attempt

        # After all attempts, store the final template in the device memory
        print("All scans complete. Storing fingerprint data...")
        position = finger.storeTemplate()  # Store the final template after multiple scans
        print(f"Fingerprint stored at position {position}")
        
        return position

    except Exception as e:
        print(f"Error during fingerprint enrollment: {e}")
        return -1



def check_internet():
    """Check if device is connected to the internet."""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def save_to_sqlite(student_id, time_in_str, status, synced=True):
    """Save attendance record to SQLite database (add synced flag)."""
    try:
        conn = sqlite3.connect('attendance.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO attendance (student_id, time_in, status, synced) VALUES (?, ?, ?, ?)", 
                       (student_id, time_in_str, status, synced))
        conn.commit()
        print(f"Attendance for {student_id} saved to SQLite.")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")




def reset_synced_flag_for_deleted_data():
    """Reset the synced flag to 0 if data is deleted from Firebase."""
    try:
        # Update records where synced is 1 (means data was previously synced but deleted from Firebase)
        conn = sqlite3.connect('attendance.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("UPDATE attendance SET synced = 0 WHERE synced = 1")
        conn.commit()
        conn.close()
        print("Synced flag reset for deleted data.")
    except sqlite3.Error as e:
        print(f"SQLite error during reset: {e}")



def auto_sync_unsynced_data():
    """Auto-sync unsynced records to Firebase once internet is available."""
    while True:
        if check_internet():
            print("Internet connection detected. Attempting to sync unsynced data to Firebase...")
            conn = sqlite3.connect('attendance.db', check_same_thread=False)
            cursor = conn.cursor()

            # Fetch unsynced records from SQLite in batches
            cursor.execute("SELECT id, student_id, time_in FROM attendance WHERE synced = 0 LIMIT 50")
            unsynced_records = cursor.fetchall()

            if not unsynced_records:
                print("No unsynced data found.")
            else:
                # Batch process syncing the records to Firebase
                batch_data = {}
                for record in unsynced_records:
                    record_id, student_id, time_in = record
                    today = datetime.now().strftime('%Y-%m-%d')

                    if today not in batch_data:
                        batch_data[today] = {}

                    batch_data[today][student_id] = {
                        'timeIn': time_in
                    }

                # Sync to Firebase in a batch
                for date, students_data in batch_data.items():
                    ref = db.reference(f'attendance/{date}')
                    for student_id, data in students_data.items():
                        ref.child(student_id).set(data)
                        print(f"Synced attendance for {student_id} at {data['timeIn']}.")

                # Mark as synced in SQLite after batch processing
                cursor.executemany(
                    "UPDATE attendance SET synced = 1 WHERE id = ?",
                    [(record[0],) for record in unsynced_records]
                )
                conn.commit()
                print("Batch sync completed. Updated synced flag for records in SQLite.")
            
            conn.close()
        else:
            print("No internet connection. Trying again in 10 seconds...")

        time.sleep(10)  # Wait before trying again



# Run auto-sync function in a separate thread
def start_auto_sync_thread():
    auto_sync_thread = threading.Thread(target=auto_sync_unsynced_data, daemon=True)
    auto_sync_thread.start()



def check_saved_data():
    """Check if data is saved correctly in SQLite."""
    try:
        cursor.execute("SELECT * FROM attendance")
        records = cursor.fetchall()

        if records:
            print("Saved attendance records:")
            for record in records:
                print(f"Student ID: {record[0]}, Time In: {record[1]}")
        else:
            print("No records found in the SQLite database.")
    except sqlite3.Error as e:
        print(f"Error checking data in SQLite: {e}")



# Attendance GUI
class AttendanceApp:
    def __init__(self, root):
        self.attendance_start_time = None
        # Firebase Setup
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://ams-project-b6b30-default-rtdb.firebaseio.com/'
        })
        self.root = root
        self.root.title("Fingerprint Attendance System")
        self.root.geometry("700x400")

        self.attendance_running = False  
        self.attendance_thread = None  

        load_student_data()  

        self.enroll_button = Button(self.root, text="Enroll Fingerprint", command=self.enroll_fingerprint)
        self.enroll_button.pack(pady=10)

        self.start_button = Button(self.root, text="Start Attendance", command=self.start_attendance)
        self.start_button.pack(pady=10)

        self.stop_button = Button(self.root, text="Stop Attendance", command=self.stop_attendance, state=DISABLED)
        self.stop_button.pack(pady=10)
        
        self.report_button = Button(self.root, text="Report Attendance", command=self.generate_report)
        self.report_button.pack(pady=10)

        self.tree = ttk.Treeview(self.root, columns=("Student ID", "Time In"), show="headings")
        self.tree.heading("Student ID", text="Student ID")
        self.tree.heading("Time In", text="Time In")
        self.tree.pack(pady=10, fill="both", expand=True)

    def get_student_id_popup(self):
        """Show popup to enter Student ID and return the value."""
        self.student_id_value = None

        def on_submit():
            self.student_id_value = student_id_entry.get()
            popup.destroy()

        popup = Toplevel(self.root)
        popup.title("Enter Student ID")
        popup.geometry("300x100")
        popup.resizable(False, False)

        Label(popup, text="Enter Student ID:").pack(pady=5)
        student_id_entry = Entry(popup)
        student_id_entry.pack(pady=5)
        Button(popup, text="Submit", command=on_submit).pack(pady=5)

        popup.grab_set()
        self.root.wait_window(popup)
        return self.student_id_value

    def enroll_fingerprint(self):
        
        student_id = self.get_student_id_popup() 
        position = enroll_fingerprint_procedure(finger)

        if position != -1:
            position_to_student_id[position] = student_id
            save_student_data()
            print(f"Student ID {student_id} enrolled at position {position}.")
            led_feedback(True)
        else:
            print("Fingerprint enrollment failed.")
            led_feedback(False)

    def start_attendance(self):
        """Start attendance monitoring."""
        self.attendance_running = True
        self.attendance_start_time = datetime.now()  # ✅ Mark start time
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=NORMAL)

        self.attendance_thread = threading.Thread(target=self.mark_attendance, daemon=True)
        self.attendance_thread.start()


    def stop_attendance(self):
        """Stop attendance process."""
        self.attendance_running = False
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)
        print("Attendance marking stopped.")

    def mark_attendance(self):
        """Scan fingerprints for attendance with time-based rules."""
        while self.attendance_running:
            try:
                if not finger.readImage():
                    continue

                finger.convertImage(0x01)
                result = finger.searchTemplate()

                position_number = result[0]

                if position_number == -1:
                    lcd.clear()
                    lcd.write_string("Finger not found")
                    led_feedback(False)
                    continue

                student_id = position_to_student_id.get(position_number)

                if not student_id:
                    lcd.clear()
                    lcd.write_string("ID not found")
                    led_feedback(False)
                    continue

                current_time = datetime.now()
                time_diff = (current_time - self.attendance_start_time).total_seconds()

                if time_diff <= 10:
                    status = "Present"
                elif time_diff <= 15:
                    status = "Late"
                else:
                    lcd.clear()
                    lcd.write_string("Marked Absent")
                    print(f"{student_id} tried after 5 mins. Marked absent.")
                    led_feedback(False)
                    continue

                time_in_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                lcd.clear()
                lcd.write_string(f"{status}: {student_id}")
                print(f"{student_id} marked {status} at {time_in_str}")

                self.tree.insert("", END, values=(student_id, time_in_str, status))
                led_feedback(True)

                # Save attendance record with status to SQLite
                save_to_sqlite(student_id, time_in_str, status, synced=False)

            except Exception as e:
                print(f"Error during attendance marking: {e}")



    def generate_report(self):
        """Generate an attendance report as a PDF."""
        # Instead of checking 'students', directly check if attendance records exist in the database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, time_in, status FROM attendance")
        records = cursor.fetchall()

        if not records:
            print("No attendance records to generate report.")
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Attendance Report", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, "Student ID", border=1)
        pdf.cell(50, 10, "Time In", border=1)
        pdf.cell(50, 10, "Status", border=1)  # Added status column
        pdf.ln()

        pdf.set_font("Arial", "", 12)

        for student_id, time_in, status in records:
            # Ensure that status is not None and assign a default value if necessary
            if status is None:
                status = "Unknown"  # Default value in case status is None

            pdf.cell(50, 10, str(student_id), border=1)
            pdf.cell(50, 10, time_in, border=1)
            pdf.cell(50, 10, status, border=1)  # Add status to report
            pdf.ln()

        # Save PDF
        pdf.output("attendance_report.pdf")
        print("Attendance report generated successfully.")
        conn.close()


if __name__ == "__main__":
    start_auto_sync_thread() 
    root = Tk()
    app = AttendanceApp(root)
    root.mainloop()
