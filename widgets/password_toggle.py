# widgets/password_toggle.py
import tkinter as tk

class PasswordToggle:
    def __init__(self, parent, password_entry, confirm_password_entry=None):
        self.password_entry = password_entry
        self.confirm_password_entry = confirm_password_entry
        self.password_checkbox_var = tk.BooleanVar()

        self.password_checkbox = tk.Checkbutton(
            parent,
            text="Show Password",
            variable=self.password_checkbox_var,
            command=self.toggle_password,
            bg="lightgray"
        )
        self.password_checkbox.pack(pady=5)  # The Checkbutton is packed here

    def toggle_password(self):
        if self.password_checkbox_var.get():
            self.password_entry.config(show="")
            if self.confirm_password_entry:
                self.confirm_password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
            if self.confirm_password_entry:
                self.confirm_password_entry.config(show="*")