# frames/account_frame.py
import tkinter as tk
from tkinter import messagebox, simpledialog

class AccountFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="lightgray")
        self.db = db
        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        account_label = tk.Label(self, text="ACCOUNT", font=("Helvetica", 18, "bold"), bg="lightgray")
        account_label.pack(pady=10)

        register_account_button = tk.Button(
            self,
            text="Register Account",
            font=("Arial", 12),
            bg="#4682B4",
            fg="white",
            command=self.show_register_account_form
        )
        register_account_button.pack(pady=10)

        delete_account_button = tk.Button(
            self,
            text="Delete Account",
            font=("Arial", 12),
            bg="#4682B4",
            fg="white",
            command=self.delete_account
        )
        delete_account_button.pack(pady=10)

    def show_register_account_form(self):
        self.clear_frame()

        title_label = tk.Label(self, text="REGISTER YOUR ACCOUNT", font=("Helvetica", 18, "bold"), bg="lightgray")
        title_label.pack(pady=10)

        form_frame = tk.Frame(self, bg="white", bd=2, relief=tk.SUNKEN)
        form_frame.pack(padx=20, pady=20, fill="both", expand=False)

        # Add form fields (first name, last name, email, etc.)
        # Example:
        tk.Label(form_frame, text="First Name:", font=("Arial", 12), bg="white").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_first_name = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.entry_first_name.grid(row=0, column=1, padx=10, pady=10)

        # Add more fields as needed...

        register_btn = tk.Button(
            form_frame,
            text="Register",
            font=("Arial", 12),
            bg="#4682B4",
            fg="white",
            command=self.register_account
        )
        register_btn.grid(row=9, column=1, padx=10, pady=10, sticky="w")

        cancel_btn = tk.Button(
            self,
            text="Cancel",
            font=("Arial", 12),
            bg="gray",
            fg="white",
            command=self.clear_frame
        )
        cancel_btn.pack()

    def register_account(self):
        first_name = self.entry_first_name.get().strip()
        # Add logic to register account in the database
        if not first_name:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        try:
            self.db.cursor.execute(
                "INSERT INTO accounts (first_name) VALUES (?)",
                (first_name,)
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Account registered successfully!")
            self.clear_frame()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register account: {e}")

    def delete_account(self):
        email_to_delete = simpledialog.askstring("Delete Account", "Enter Email of the account to delete:")
        if not email_to_delete:
            return

        self.db.cursor.execute("SELECT * FROM accounts WHERE email = ?", (email_to_delete,))
        account = self.db.cursor.fetchone()

        if account:
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete account with Email: {email_to_delete}?")
            if confirm:
                self.db.cursor.execute("DELETE FROM accounts WHERE email = ?", (email_to_delete,))
                self.db.conn.commit()
                messagebox.showinfo("Deleted", f"Account with email '{email_to_delete}' has been deleted.")
        else:
            messagebox.showerror("Not Found", f"No account found with email '{email_to_delete}'.")

    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()
