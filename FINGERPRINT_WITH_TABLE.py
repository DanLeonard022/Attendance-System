import time
import serial
from pyfingerprint.pyfingerprint import PyFingerprint
from tkinter import *
from tkinter import ttk
from datetime import datetime
import threading
from RPLCD.i2c import CharLCD
from fpdf import FPDF

students = {}
position_to_student_id = {}

try:
    uart = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.1)
except serial.SerialException as e:
    print(f"Error initializing serial connection: {e}")
    exit()

try:
    finger = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
    
    if not finger.verifyPassword():
        raise ValueError("Fingerprint sensor password is incorrect!")

    print("Fingerprint sensor initialized successfully.")

except Exception as e:
    print(f"Failed to initialize the fingerprint sensor: {e}")
    finger = None

lcd = CharLCD('PCF8574', 0x27, port=1, cols=16, rows=2)
lcd.clear()

def display_on_lcd(message):
    """Display a message on the LCD screen."""
    lcd.clear()
    lcd.write_string(message)

def save_student_data():
    """I-save ang student ID at position sa file."""
    with open("students.txt", "w") as file:
        for position, student_id in position_to_student_id.items():
            file.write(f"{position},{student_id}\n")

def load_student_data():
    """I-load ang naka-save na student data mula sa file."""
    global position_to_student_id
    position_to_student_id = {}

    try:
        with open("students.txt", "r") as file:
            for line in file:
                position, student_id = line.strip().split(",")
                position_to_student_id[int(position)] = student_id
        print("Student data loaded successfully.")
    except FileNotFoundError:
        print("No saved student data found.")

def enroll_fingerprint_procedure(finger):
    """Enroll a fingerprint for a student."""
    try:
        print("Place your finger on the scanner...")
        
        while not finger.readImage():
            pass  
        
        finger.convertImage(0x01)
        
        position, accuracy = finger.searchTemplate()
        if position >= 1:
            print("Fingerprint already registered at position", position)
            return -1  # Already exists

        print("Remove finger and place it again...")
        time.sleep(2)

        while not finger.readImage():
            pass  

        finger.convertImage(0x02)
        
        if finger.compareCharacteristics() == 0:
            print("Fingerprints do not match. Try again.")
            return -1

        position = finger.storeTemplate()
        print(f"Fingerprint stored successfully at position {position}")
        return position

    except Exception as e:
        print(f"Error during fingerprint enrollment: {e}")
        return -1


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fingerprint Attendance System")
        self.root.geometry("700x400")

        self.attendance_running = False  
        self.attendance_thread = None  

        load_student_data()  # Load student data kapag nag-start ang program

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

    def enroll_fingerprint(self):
        """Enroll fingerprint and save student ID."""
        student_id = input("Enter Student ID to register fingerprint: ")
        position = enroll_fingerprint_procedure(finger)

        if position != -1:  
            position_to_student_id[position] = student_id  
            save_student_data()  
            print(f"Student ID {student_id} enrolled at position {position}.")
        else:
            print("Fingerprint enrollment failed.")

    def start_attendance(self):
        """Start real-time attendance monitoring in a separate thread."""
        self.attendance_running = True
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=NORMAL)

        self.attendance_thread = threading.Thread(target=self.mark_attendance, daemon=True)
        self.attendance_thread.start()

    def stop_attendance(self):
        """Stop the attendance process."""
        self.attendance_running = False
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)
        print("Attendance marking stopped.")

    def mark_attendance(self):
        """Continuously scan fingerprints without blocking the GUI."""
        while self.attendance_running:
            try:
                if finger.readImage():  
                    finger.convertImage(0x01)
                    position, accuracy = finger.searchTemplate()

                    if position >= 0:
                        student_id = position_to_student_id.get(position, "Unknown")
                        current_time = datetime.now().strftime("%H:%M:%S")

                        display_on_lcd(f"Position {position}")  # ✅ LCD: Position

                        print(f"Attendance marked for Student ID: {student_id} at {current_time}")
                        self.tree.insert("", "end", values=(student_id, current_time))
                        students[student_id] = current_time  

                        time.sleep(1)  
                    else:
                        print("Fingerprint not found.")
                        display_on_lcd("Retry: Place again")

                time.sleep(0.1)  
            except Exception as e:
                print(f"Error during fingerprint scanning: {e}")
                time.sleep(1)

    def generate_report(self):
        """Generate an attendance report as a PDF."""
        if not students:
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
        pdf.ln()

        pdf.set_font("Arial", "", 12)
        for student_id, time_in in students.items():
            pdf.cell(50, 10, str(student_id), border=1)
            pdf.cell(50, 10, time_in, border=1)
            pdf.ln()

        pdf.output("attendance_report.pdf")
        print("Attendance report generated: attendance_report.pdf")


if __name__ == "__main__":
    root = Tk()
    app = AttendanceApp(root)
    root.mainloop()
