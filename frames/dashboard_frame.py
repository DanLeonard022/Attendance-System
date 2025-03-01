# frames/dashboard_frame.py (updated)
import tkinter as tk
import sqlite3
from tkinter import messagebox, simpledialog, ttk
import datetime
from email_handler import EmailHandler

class DashboardFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg="white")
        self.db = db
        self.parent = parent

        # Initialize EmailHandler
        self.email_handler = EmailHandler(
            sender_email="bio.hunters10@gmail.com",  # Replace with your Gmail address
            sender_password="ljab fqkc ptdf qwzk"   # Replace with your Gmail app password
        )

        self.left_frame = tk.Frame(self, bg="lightgray", width=200, relief=tk.SUNKEN, bd=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.left_frame.pack_propagate(False)
        self.left_frame.config(height=600)

        menu_label = tk.Label(self.left_frame, text="MENU", font=("Helvetica", 18, "bold"), bg="lightgray")
        menu_label.pack(pady=10)

        menu_buttons_frame = tk.Frame(self.left_frame, bg="lightgray")
        menu_buttons_frame.place(relx=0.5, rely=0.5, anchor="center")

        dashboard_button = tk.Button(menu_buttons_frame, text="DASHBOARD", font=("Arial", 12), bg="white", command=self.show_dashboard_screen)
        dashboard_button.pack(fill="x", pady=10)

        records_button = tk.Button(menu_buttons_frame, text="VIEW/ADD RECORDS", font=("Arial", 12), bg="white", command=self.show_records_screen)
        records_button.pack(fill="x", pady=10)

        schedule_button = tk.Button(menu_buttons_frame, text="SCHEDULE", font=("Arial", 12), bg="white", command=self.show_schedule_screen)
        schedule_button.pack(fill="x", pady=10)

        account_button = tk.Button(menu_buttons_frame, text="ACCOUNT", font=("Arial", 12), bg="white", command=self.show_account_screen)
        account_button.pack(fill="x", pady=10)

        logout_button = tk.Button(menu_buttons_frame, text="LOG OUT", font=("Arial", 12), bg="white", command=self.parent.show_login_frame)
        logout_button.pack(fill="x", pady=10)

        self.right_frame = tk.Frame(self, bg="lightgray", width=600, relief=tk.SUNKEN, bd=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.show_dashboard_screen();

    def show_dashboard_screen(self):
        self.clear_right_frame()
        dashboard_label = tk.Label(self.right_frame, text="DASHBOARD", font=("Helvetica", 18, "bold"), bg="#4682B4", fg="white")
        dashboard_label.pack(pady=10)
        first_text_label = tk.Label(self.right_frame, text="Welcome to the Dashboard!", font=("Helvetica", 20), bg="lightgray", wraplength=400)
        first_text_label.pack(anchor="center", padx=10, pady=10)

    def show_records_screen(self):
        self.right_frame.unbind_all("<MouseWheel>")
        self.clear_right_frame()

        records_label = tk.Label(self.right_frame, text="VIEW/ADD RECORDS", 
                                font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        records_label.pack(pady=10)
        second_text_label = tk.Label(self.right_frame, text="COURSES",
                                    font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        second_text_label.pack(anchor="center", pady=15)

        course_frame = tk.Frame(self.right_frame, bg="lightgray", width=700, height=400, relief=tk.SUNKEN, bd=2)
        course_frame.pack(fill=None, expand=False, padx=50, pady=5)
        course_frame.pack_propagate(False)
        
        courses = [
            "BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY",
            "BACHELOR OF SCIENCE IN COMPUTER SCIENCE",
            "BACHELOR OF SCIENCE IN INFORMATION SYSTEM",
        ]

        for course in courses:
            tk.Button(course_frame, text=course, 
                    font=("Arial", 14), bg="#4682B4", fg="white", width=54, height=3,
                    command=lambda c=course: self.yearlevel_and_section_frame(c)
                    ).pack(pady=20)


    def yearlevel_and_section_frame(self, course_name):
        self.clear_right_frame()
        self.right_frame.pack_propagate(False)

        yearlevel_label = tk.Label(self.right_frame, text=f"VIEW/ADD RECORDS - \n{course_name}", 
                                font=("Helvetica", 18, "bold"), bg="#4682B4", fg="white")
        yearlevel_label.pack(pady=10)

        container = tk.Frame(self.right_frame, bg="lightgray")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        right_scrollbar = tk.Scrollbar(container, orient="vertical")
        right_scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(container, bg="lightgray", width=800, height=460, yscrollcommand=right_scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.config(command=canvas.yview)

        scroll_frame = tk.Frame(canvas, bg="lightgray")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", on_frame_configure)

        def on_mouse_wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        def on_mouse_wheel(event):
            if canvas.winfo_exists():  # Check if canvas still exists
                canvas.yview_scroll(-1 * (event.delta // 120), "units")

        
        bottom_frame = tk.Frame(self.right_frame, height=60, bg="lightgray")
        bottom_frame.pack(fill="x", side="bottom")

        back1_button = tk.Button(bottom_frame, text="Back", font=("Arial", 14), bg="#4682B4", fg="white", width=10,
                                 command=self.show_records_screen)
        back1_button.pack(side="left", padx=30, pady=5)


        if course_name == "BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY":
            section_names = {1: ["LFCA111M010", "LFCA322M011"], 2: ["LFCA211M025", "LFCA211A005"], 
                            3: ["LFCA311M045", "LFCA311M046"], 4: ["LFCA411M055", "LFCA411M056"]}
        elif course_name == "BACHELOR OF SCIENCE IN COMPUTER SCIENCE":
            section_names = {1: ["CS101", "CS102"], 2: ["CS201", "CS202"], 3: ["CS301", "CS302"], 4: ["CS401", "CS402"]}
        elif course_name == "BACHELOR OF SCIENCE IN INFORMATION SYSTEM":
            section_names = {1: ["IS101", "IS102"], 2: ["IS201", "IS102"], 3: ["IS301", "IS102"], 4: ["IS401", "IS102"]}

        for year in range(1, 5):
            year_frame = tk.Frame(scroll_frame, bg="lightgray", width=700, height=230, relief=tk.SUNKEN, bd=2)
            year_frame.pack(fill=None, padx=10, pady=10)
            year_frame.pack_propagate(False)  
            
            year_label_text = f"{year}ST YEAR" if year == 1 else f"{year}ND YEAR" if year == 2 else f"{year}RD YEAR" if year == 3 else f"{year}TH YEAR"
            year_label = tk.Label(year_frame, text=year_label_text, font=("Helvetica", 15, "bold"), fg="white", bg="gray")
            year_label.pack(anchor="w", padx=5, pady=10)

            for section in section_names.get(year, []):
                section_button = tk.Button(year_frame, text=section, font=("Arial", 14), bg="#4682B4", fg="white", width=21,
                                        command=lambda sec=section: self.subjects_frame(sec, course_name))  
                section_button.pack(pady=5, ipadx=200, ipady=5)

            add_section_button = tk.Button(year_frame, text="Add Section", font=("Arial", 14), bg="green", fg="white", width=21)
            add_section_button.config(command=lambda yf=year_frame, ab=add_section_button: self.add_section(yf, ab))
            add_section_button.pack(pady=5, ipadx=200, ipady=5)


    def add_section(self, year_frame, add_button):
        
        entry_frame = tk.Frame(year_frame, bg="lightgray")
        entry_frame.pack(pady=5)
        section_entry = tk.Entry(entry_frame, font=("Arial", 14), width=25, bd=2, bg="white")
        section_entry.pack(side="left", padx=5)
        confirm_button = tk.Button(entry_frame, text="Confirm", font=("Arial", 12), bg="#4682B4", fg="white",
                                command=lambda: self.confirm_add_section(year_frame, entry_frame, section_entry.get(), add_button))
        confirm_button.pack(side="left", padx=5)

    def confirm_add_section(self, year_frame, entry_frame, new_section, add_button):
        if new_section:
            add_button.pack_forget()
            section_button = tk.Button(year_frame, text=new_section, font=("Arial", 14), bg="#4682B4", fg="white")
            section_button.pack(pady=5, ipadx=200, ipady=5)
            add_button.pack(pady=5, ipadx=190, ipady=5)
        entry_frame.destroy()

    def subjects_frame(self, section_names, course_name):
        self.right_frame.unbind_all("<MouseWheel>")
        self.clear_right_frame()

        subjects_label = tk.Label(self.right_frame, text="SUBJECTS", font=("Helvetica", 18, "bold"), bg="#4682B4", fg="white", width=13)
        subjects_label.place(x=30, y=30, anchor="nw")
        
        section_name_label = tk.Label(self.right_frame, text=section_names, font=("Helvetica", 18, "bold"), bg="#4682B4", fg="white", width=31)
        section_name_label.place(relx=1.0, x=-40, y=30, anchor="ne")
        
        sublist_frame = tk.Frame(self.right_frame, bg="lightgray", width=700, height=350, relief=tk.SUNKEN, bd=2)
        sublist_frame.place(relx=0.5, rely=0.5, anchor="center")
        sublist_frame.pack_propagate(False)


        subjects = [
            ("CAPSTONE 1", "BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY"),
            ("CISCO 02", "BACHELOR OF SCIENCE IN COMPUTER SCIENCE"),
            ("INFORMATION ASSURANCE AND SECURITY", "BACHELOR OF SCIENCE IN INFORMATION SYSTEM"),
            ("INTEGRATIVE PROGRAMMING AND TECHNOLOGIES", "BACHELOR OF SCIENCE IN INFORMATION SYSTEM"),
        ]

        for subject, program in subjects:
            tk.Button(sublist_frame, text=subject, 
                    font=("Arial", 14), bg="#4682B4", fg="white", width=54, 
                    command=lambda p=program: self.yearlevel_and_section_frame(p)
            ).pack(pady=15, ipady=7)

        back_button = tk.Button(self.right_frame, text="Back", font=("Arial", 14), bg="#4682B4", fg="white", width=10,
                                command=lambda: self.yearlevel_and_section_frame(course_name))
        back_button.place(x=20, rely=1.0, y=-50, anchor="sw")


    def show_schedule_screen(self):
        self.right_frame.unbind_all("<MouseWheel>")
        self.clear_right_frame()
        schedule_label = tk.Label(self.right_frame, text="SCHEDULE", font=("Helvetica", 18, "bold"), bg="lightgray")
        schedule_label.pack(pady=10)
        third_text_label = tk.Label(self.right_frame, text="", font=("Helvetica", 20), bg="lightgray", wraplength=400)
        third_text_label.pack(anchor="center", padx=10, pady=10)
        reminder_button = tk.Button(self.right_frame, text="Schedule Class Reminder", font=("Arial", 12), bg="#4682B4", fg="white", command=self.schedule_email_reminder)
        reminder_button.pack(pady=10, ipadx=10, ipady=5)

    def send_email_reminder(self, recipient, subject, body):
        success = self.email_handler.send_email_reminder(recipient, subject, body)
        if success:
            messagebox.showinfo("Success", f"Email sent to {recipient}")
        else:
            messagebox.showerror("Error", "Failed to send email.")

    def send_bulk_email_reminder(self, recipients, subject, body):
        success = self.email_handler.send_bulk_email_reminder(recipients, subject, body)
        if success:
            messagebox.showinfo("Success", f"Emails sent to {len(recipients)} recipients.")
        else:
            messagebox.showerror("Error", "Failed to send bulk emails.")
            
    def schedule_email_reminder(self):
        reminder_window = tk.Toplevel(self)
        reminder_window.title("Schedule Class Reminder Email")
        reminder_window.geometry("500x600")

        # Recipient Emails
        tk.Label(reminder_window, text="Recipient Email(s):", font=("Arial", 10)).pack(pady=5)
        tk.Label(reminder_window, text="(Enter emails separated by commas or newlines.\nLeave empty for all students)", font=("Arial", 8)).pack()
        text_emails = tk.Text(reminder_window, width=40, height=2)
        text_emails.pack(pady=5)

        # Date Selection
        tk.Label(reminder_window, text="Date:").pack(pady=5)

        # Frame for Date Comboboxes
        date_frame = tk.Frame(reminder_window)
        date_frame.pack(pady=5)

        # Day Combobox
        days = [str(day).zfill(2) for day in range(1, 32)]  # Days 01 to 31
        day_combobox = ttk.Combobox(date_frame, width=5, values=days)
        day_combobox.set(datetime.datetime.now().strftime("%d"))  # Set current day
        day_combobox.pack(side="left", padx=5)

        # Month Combobox
        months = [datetime.date(2023, month, 1).strftime("%B") for month in range(1, 13)]  # January to December
        month_combobox = ttk.Combobox(date_frame, width=10, values=months)
        month_combobox.set(datetime.datetime.now().strftime("%B"))  # Set current month
        month_combobox.pack(side="left", padx=5)

        # Year Combobox
        current_year = datetime.datetime.now().year
        years = [str(year) for year in range(current_year, current_year + 5)]  # Current year + next 4 years
        year_combobox = ttk.Combobox(date_frame, width=5, values=years)
        year_combobox.set(str(current_year))  # Set current year
        year_combobox.pack(side="left", padx=5)

        # Time Selection
        tk.Label(reminder_window, text="Time (HH:MM):").pack(pady=5)

        # Frame for Time Comboboxes
        time_frame = tk.Frame(reminder_window)
        time_frame.pack(pady=5)

        # Hour Combobox
        hours = [str(hour).zfill(2) for hour in range(0, 24)]  # Hours 00 to 23
        hour_combobox = ttk.Combobox(time_frame, width=5, values=hours)
        hour_combobox.set(datetime.datetime.now().strftime("%H"))  # Set current hour
        hour_combobox.pack(side="left", padx=5)

        # Minute Combobox
        minutes = [str(minute).zfill(2) for minute in range(0, 60, 5)]  # Minutes 00 to 55 (increments of 5)
        minute_combobox = ttk.Combobox(time_frame, width=5, values=minutes)
        minute_combobox.set(datetime.datetime.now().strftime("%M"))  # Set current minute
        minute_combobox.pack(side="left", padx=5)

        # Subject
        tk.Label(reminder_window, text="Subject:").pack(pady=5)
        entry_subject = tk.Entry(reminder_window, width=40)
        entry_subject.insert(0, "Class Reminder")
        entry_subject.pack(pady=5)

        # Message
        tk.Label(reminder_window, text="Message:").pack(pady=5)
        text_message = tk.Text(reminder_window, width=40, height=5)
        text_message.insert("1.0", "This is a reminder that you have a class to attend.")
        text_message.pack(pady=5)

        def schedule_action():
            emails_input = text_emails.get("1.0", tk.END).strip()
            recipients = []
            if emails_input:
                for line in emails_input.splitlines():
                    for email in line.split(','):
                        email = email.strip()
                        if email:
                            recipients.append(email)

            # Get selected date and time from comboboxes
            day = day_combobox.get().strip()
            month = month_combobox.get().strip()
            year = year_combobox.get().strip()
            hour = hour_combobox.get().strip()
            minute = minute_combobox.get().strip()

            # Combine date and time into a single string
            date_str = f"{year}-{datetime.datetime.strptime(month, '%B').month:02d}-{day}"
            time_str = f"{hour}:{minute}"

            subject = entry_subject.get().strip()
            body = text_message.get("1.0", tk.END).strip()

            if not day or not month or not year or not hour or not minute:
                messagebox.showerror("Input Error", "Please fill in the date and time.")
                return

            try:
                scheduled_dt = datetime.datetime.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Format Error", "Invalid date or time.")
                return

            now = datetime.datetime.now()
            delay_ms = int((scheduled_dt - now).total_seconds() * 1000)
            if delay_ms < 0:
                messagebox.showerror("Input Error", "The scheduled time is in the past.")
                return

            if recipients:
                if len(recipients) == 1:
                    self.after(delay_ms, lambda: self.send_email_reminder(recipients[0], subject, body))
                else:
                    self.after(delay_ms, lambda: self.send_bulk_email_reminder(recipients, subject, body))
                messagebox.showinfo("Scheduled", f"Email reminder scheduled for {scheduled_dt.strftime('%Y-%m-%d %H:%M')} to {len(recipients)} recipient(s).")
            else:
                self.db.cursor.execute("SELECT email FROM accounts")
                all_recipients = [row[0] for row in self.db.cursor.fetchall()]
                if not all_recipients:
                    messagebox.showerror("Error", "No student emails found in the database.")
                    return
                self.after(delay_ms, lambda: self.send_bulk_email_reminder(all_recipients, subject, body))
                messagebox.showinfo("Scheduled", f"Bulk email reminder scheduled for {scheduled_dt.strftime('%Y-%m-%d %H:%M')} for {len(all_recipients)} recipients.")
            reminder_window.destroy()

        # Schedule Button
        btn_schedule = tk.Button(reminder_window, text="Schedule Reminder", font=("Arial", 12), bg="#4682B4", fg="white", command=schedule_action)
        btn_schedule.pack(pady=10)

    def show_account_screen(self):
        self.right_frame.unbind_all("<MouseWheel>")
        self.clear_right_frame()
        account_label = tk.Label(self.right_frame, text="ACCOUNT", font=("Helvetica", 18, "bold"), bg="lightgray")
        account_label.pack(pady=10)
        register_account_button = tk.Button(self.right_frame, text="Register Account", font=("Arial", 12), bg="#4682B4", fg="white", command=self.show_register_account_form)
        register_account_button.pack(pady=10)
        delete_account_button = tk.Button(self.right_frame, text="Delete Account", font=("Arial", 12), bg="#4682B4", fg="white", command=self.delete_account)
        delete_account_button.pack(pady=10)
    
    def show_register_account_form(self):
        self.clear_right_frame()
        title_label = tk.Label(self.right_frame, text="REGISTER YOUR ACCOUNT", font=("Helvetica", 18, "bold"), bg="lightgray")
        title_label.pack(pady=10)

        form_frame = tk.Frame(self.right_frame, bg="white", bd=2, relief=tk.SUNKEN)
        form_frame.pack(padx=20, pady=20, fill="both", expand=False)

        # First Name
        tk.Label(form_frame, text="First Name:", font=("Arial", 12), bg="white")\
            .grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_first_name = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_first_name.grid(row=0, column=1, padx=10, pady=10)

        # Middle Name
        tk.Label(form_frame, text="Middle Name (Optional):", font=("Arial", 12), bg="white")\
            .grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_middle_name = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_middle_name.grid(row=1, column=1, padx=10, pady=10)

        # Last Name
        tk.Label(form_frame, text="Last Name:", font=("Arial", 12), bg="white")\
            .grid(row=2, column=0, padx=10, pady=10, sticky="e")
        entry_last_name = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_last_name.grid(row=2, column=1, padx=10, pady=10)

        # Suffix
        tk.Label(form_frame, text="Suffix:", font=("Arial", 12), bg="white")\
            .grid(row=3, column=0, padx=10, pady=10, sticky="e")
        entry_suffix = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_suffix.grid(row=3, column=1, padx=10, pady=10)

        # Age
        tk.Label(form_frame, text="Age:", font=("Arial", 12), bg="white")\
            .grid(row=4, column=0, padx=10, pady=10, sticky="e")
        entry_age = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_age.grid(row=4, column=1, padx=10, pady=10)

        # Birthdate
        tk.Label(form_frame, text="Birthdate:", font=("Arial", 12), bg="white")\
            .grid(row=5, column=0, padx=10, pady=10, sticky="e")
        entry_birthdate = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_birthdate.grid(row=5, column=1, padx=10, pady=10)

        # Email
        tk.Label(form_frame, text="Email:", font=("Arial", 12), bg="white")\
            .grid(row=6, column=0, padx=10, pady=10, sticky="e")
        entry_email = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_email.grid(row=6, column=1, padx=10, pady=10)

        # Cell Number
        tk.Label(form_frame, text="Cell Number:", font=("Arial", 12), bg="white")\
            .grid(row=7, column=0, padx=10, pady=10, sticky="e")
        entry_cell = tk.Entry(form_frame, font=("Arial", 12), width=25)
        entry_cell.grid(row=7, column=1, padx=10, pady=10)

        # Fingerprint
        fingerprint_label = tk.Label(form_frame, text="Fingerprint Status: Not Scanned", 
                                     font=("Arial", 10), fg="red", bg="white")
        fingerprint_label.grid(row=8, column=0, columnspan=2, pady=10)

        def scan_fingerprint_account():
            fingerprint_label.config(text="Fingerprint Status: Scanning...", fg="blue")
            fingerprint_label.after(2000, lambda: fingerprint_label.config(text="Fingerprint Status: Scanned Successfully", fg="green"))

        scan_btn = tk.Button(form_frame, text="Scan Fingerprint", font=("Arial", 12), bg="blue", fg="white", 
                             command=scan_fingerprint_account)
        scan_btn.grid(row=9, column=0, padx=10, pady=10, sticky="e")

        def register_account_inner():
            first_name = entry_first_name.get().strip()
            middle_name = entry_middle_name.get().strip()
            last_name = entry_last_name.get().strip()
            suffix = entry_suffix.get().strip()
            age = entry_age.get().strip()
            birthdate = entry_birthdate.get().strip()
            email = entry_email.get().strip()
            cell = entry_cell.get().strip()
            fp_status = fingerprint_label.cget("text")

            if not first_name or not last_name or not email:
                messagebox.showerror("Input Error", "Please fill at least First Name, Last Name, and Email.")
                return

            try:
                self.db.cursor.execute('''
                    INSERT INTO accounts (first_name, middle_name, last_name, suffix, age, birthdate, email, cell_number, fingerprint_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (first_name, middle_name, last_name, suffix, age, birthdate, email, cell, fp_status))
                self.db.conn.commit()
                messagebox.showinfo("Success", "Account registered successfully!")

                entry_first_name.delete(0, tk.END)
                entry_middle_name.delete(0, tk.END)
                entry_last_name.delete(0, tk.END)
                entry_suffix.delete(0, tk.END)
                entry_age.delete(0, tk.END)
                entry_birthdate.delete(0, tk.END)
                entry_email.delete(0, tk.END)
                entry_cell.delete(0, tk.END)
                fingerprint_label.config(text="Fingerprint Status: Not Scanned", fg="red")

                self.show_account_screen()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "An account with that Email already exists.")

        register_btn = tk.Button(form_frame, text="Register", font=("Arial", 12), bg="#4682B4", fg="white",
                                 command=register_account_inner)
        register_btn.grid(row=9, column=1, padx=10, pady=10, sticky="w")

        cancel_btn = tk.Button(self.right_frame, text="Cancel", font=("Arial", 12), bg="gray", fg="white",
                               command=self.show_account_screen)
        cancel_btn.pack()

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

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()