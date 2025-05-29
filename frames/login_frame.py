# frames/login_frame.py
import tkinter as tk
import bcrypt
from tkinter import messagebox
from widgets.password_toggle import PasswordToggle

class LoginFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="#E7E7E7")
        self.db = db
        self.parent = parent

        mid_frame = tk.Frame(self, bg="lightgray", width=500, height=500, relief=tk.SUNKEN, bd=2)
        mid_frame.pack(fill=None, expand=False, padx=50, pady=130)
        mid_frame.pack_propagate(False)

        login_label = tk.Label(mid_frame, text="LOG IN", font=("Helvetica", 25, "bold"), bg="lightgray")
        login_label.pack(pady=20)

        username_label_log = tk.Label(mid_frame, text="Username:", font=("Arial", 14), bg="lightgray")
        username_label_log.pack(pady=5)
        self.username_entry_log = tk.Entry(mid_frame, font=("Arial", 12), width=42, bd=2)
        self.username_entry_log.pack(pady=10, ipady=7)

        password_label_log = tk.Label(mid_frame, text="Password:", font=("Arial", 14), bg="lightgray")
        password_label_log.pack(pady=5)
        self.password_entry_log = tk.Entry(mid_frame, font=("Arial", 14), width=39, show="*", bd=2)
        self.password_entry_log.pack(pady=7, ipady=7)

        self.password_toggle = PasswordToggle(mid_frame, self.password_entry_log)

        login_button = tk.Button(mid_frame, text="Login", font=("Arial", 14), bg="#4682B4", fg="white", command=self.login_professor)
        login_button.pack(pady=14, ipadx=16,ipady=4)

        create_account_button = tk.Button(
            mid_frame,
            text="Create Account",
            font=("Arial", 14),
            bg="#4682B4",
            fg="white",
            command=self.parent.show_register_frame
        )
        create_account_button.pack(pady=14, ipadx=16, ipady=4)

    def login_professor(self):
        username = self.username_entry_log.get().strip()
        password = self.password_entry_log.get().strip()

        if not username or not password:
            messagebox.showerror("Input Error", "Please fill in both fields.")
            return

        self.db.cursor.execute("SELECT * FROM professors WHERE username = ?", (username,))
        professor = self.db.cursor.fetchone()

        if professor and bcrypt.checkpw(password.encode('utf-8'), professor[1]):
            messagebox.showinfo("Success", "Login successful!")
            self.parent.current_professor = username
            print(f"Logged in as: {self.parent.current_professor}")
            self.parent.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

