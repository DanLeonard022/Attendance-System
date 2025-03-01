# app.py
import tkinter as tk
from frames.login_frame import LoginFrame
from frames.register_frame import RegisterFrame
from frames.dashboard_frame import DashboardFrame
from database import Database

class AMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AMS")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(bg="lightgray")

        self.title_label = tk.Label(self, text="ATTENDANCE MANAGEMENT SYSTEM", 
                                    font=("Helvetica", 24, "bold"), 
                                    bg="#4682B4", fg="white", pady=10)
        self.title_label.pack(fill=tk.X)

        self.db = Database()
        self.db.setup_database()
        
        self.register_frame = RegisterFrame(self, self.db)  # Create register_frame first
        self.login_frame = LoginFrame(self, self.db)       # Pass register_frame to LoginFrame
        self.dashboard_frame = DashboardFrame(self, self.db)

        self.show_login_frame()

    def show_login_frame(self):
        self.register_frame.pack_forget()
        self.dashboard_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_register_frame(self):
        self.login_frame.pack_forget()
        self.dashboard_frame.pack_forget()
        self.register_frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        self.dashboard_frame.pack(fill="both", expand=True)
