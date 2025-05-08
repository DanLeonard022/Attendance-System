# frames/register_frame.py
import tkinter as tk
import sqlite3
from tkinter import messagebox
from widgets.password_toggle import PasswordToggle
from widgets.fingerprint_scanner import FingerprintScanner
import bcrypt

class RegisterFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="#E7E7E7")
        self.db = db
        self.parent = parent

        mid_frame_register = tk.Frame(self, bg="lightgray", width=450, height=500, relief=tk.SUNKEN, bd=2)
        mid_frame_register.pack(fill=None, expand=False, padx=50, pady=50)
        mid_frame_register.pack_propagate(False)

        register_label = tk.Label(mid_frame_register, text="SIGN UP", font=("Helvetica", 20, "bold"), bg="lightgray")
        register_label.pack(pady=10)

        username_label_reg = tk.Label(mid_frame_register, text="Username:", font=("Arial", 12), bg="lightgray")
        username_label_reg.pack(pady=3)
        self.username_entry_reg = tk.Entry(mid_frame_register, font=("Arial", 12), width=30, bd=2)
        self.username_entry_reg.pack(pady=5, ipady=5)

        password_label_reg = tk.Label(mid_frame_register, text="Password:", font=("Arial", 12), bg="lightgray")
        password_label_reg.pack(pady=3)
        self.password_entry_reg = tk.Entry(mid_frame_register, font=("Arial", 12), width=30, show="*", bd=2)
        self.password_entry_reg.pack(pady=3, ipady=5)

        confirm_password_entry_reg_label = tk.Label(mid_frame_register, text="Confirm Password:", font=("Arial", 12), bg="lightgray")
        confirm_password_entry_reg_label.pack(pady=3)
        self.confirm_password_entry_reg = tk.Entry(mid_frame_register, font=("Arial", 12), width=30, show="*", bd=2)
        self.confirm_password_entry_reg.pack(pady=5, ipady=5)

        self.password_toggle = PasswordToggle(mid_frame_register, self.password_entry_reg, self.confirm_password_entry_reg)

        self.fingerprint_scanner = FingerprintScanner(mid_frame_register)

        register_button = tk.Button(mid_frame_register, text="Register", font=("Arial", 12), bg="#4682B4", fg="white", command=self.register_professor)
        register_button.pack(pady=10)

        back_to_login_button = tk.Button(mid_frame_register, text="Back to Login", font=("Arial", 12), bg="#4682B4", fg="white", command=self.parent.show_login_frame)
        back_to_login_button.pack(pady=10)

    def register_professor(self):
        username = self.username_entry_reg.get().strip()
        password = self.password_entry_reg.get().strip()
        confirm_password = self.confirm_password_entry_reg.get().strip()

        if not username or not password:
            messagebox.showerror("Input Error", "Please fill in both fields.")
            return

        if password != confirm_password:
            messagebox.showerror("Password Error", "Passwords do not match.")
            return

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            self.db.cursor.execute("INSERT INTO professors (username, password) VALUES (?, ?)", (username, hashed_password))
            self.db.conn.commit()
            messagebox.showinfo("Success", "Professor registered successfully!")
            self.parent.show_login_frame()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
