# app.py
import tkinter as tk
from frames.login_frame import LoginFrame
from frames.register_frame import RegisterFrame
from frames.dashboard_frame import DashboardFrame
from frames.attendance_list_frame import Attendance_List
from database import Database

class AMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AMS")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(bg="lightgray")

        self.current_professor = None  # Track the current logged-in professor

        self.title_label = tk.Label(self, text="ATTENDANCE MANAGEMENT SYSTEM", 
                                    font=("Helvetica", 24, "bold"), 
                                    bg="#4682B4", fg="white", pady=10)
        self.title_label.pack(fill=tk.X)

        self.db = Database()
        self.db.setup_database()

        # Initialize frames
        self.register_frame = RegisterFrame(self, self.db)  
        self.login_frame = LoginFrame(self, self.db)
        self.dashboard_frame = None  # Initialize as None, will be created dynamically
        
        self.show_login_frame()


    def show_login_frame(self):
        self.register_frame.pack_forget()
        if self.dashboard_frame:
            self.dashboard_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_register_frame(self):
        self.login_frame.pack_forget()
        if self.dashboard_frame:
            self.dashboard_frame.pack_forget()
        self.register_frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        
        # Create DashboardFrame dynamically with current_professor
        self.dashboard_frame = DashboardFrame(self, self.db, self.current_professor)
        self.dashboard_frame.pack(fill="both", expand=True)
    
    def show_attendanceList(self, section_name=None, subject=None, course_name=None):
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        if self.dashboard_frame:
            self.dashboard_frame.pack_forget()

        # Debug print to confirm DashboardFrame instance
        print(f"DashboardFrame instance: {self.dashboard_frame}")

        # Create Attendance_List frame dynamically with section_name, subject, and course_name
        attendance_frame = Attendance_List(self, self.db, section_name, subject, course_name, self.dashboard_frame)
        attendance_frame.pack(fill="both", expand=True)
