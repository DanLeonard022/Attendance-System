# attendance_list_frame.py
import pandas as pd
import sqlite3
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
from fpdf import FPDF

DB_NAME = "professor_account.db"

class Attendance_List(tk.Frame):
    def __init__(self, parent, db, section_name=None, subject=None, course_name=None, dashboard_frame=None):
        super().__init__(parent, bg="lightgray")
        self.db = db
        self.parent = parent
        self.section_name = section_name
        self.subject = subject
        self.course_name = course_name
        self.dashboard_frame = dashboard_frame
        self.current_professor = self.parent.current_professor

        # Initialize database
        self.initialize_database()

        # Title
        title_text = f"{self.section_name} - {self.subject}" if self.section_name and self.subject else "Attendance List"
        title_label = tk.Label(self, text=title_text, font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        title_label.pack(pady=15, fill="x")

        # Back button
        button_frame = tk.Frame(self, bg="lightgray")
        button_frame.place(x=10, y=10)
        back_button = tk.Button(
            button_frame,
            text="Back",
            font=("Arial", 14),
            bg="#4682B4",
            fg="white",
            width=10,
            command=self.go_back_to_subjects
        )
        back_button.pack(side="top", anchor="w", pady=10, ipadx=3)

        # Report type selection
        report_frame = tk.Frame(self, bg="lightgray")
        report_frame.pack(fill="x", padx=10, pady=5)
        
        self.report_type = tk.StringVar(value="daily")
        tk.Radiobutton(report_frame, text="Daily", variable=self.report_type, 
                      value="daily", command=self.load_data).pack(side="left", padx=5)
        tk.Radiobutton(report_frame, text="Weekly", variable=self.report_type, 
                      value="weekly", command=self.load_data).pack(side="left", padx=5)
        tk.Radiobutton(report_frame, text="Monthly", variable=self.report_type, 
                      value="monthly", command=self.load_data).pack(side="left", padx=5)

        # Date selection
        date_frame = tk.Frame(self, bg="lightgray")
        date_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(date_frame, text="Date:").pack(side="left")
        self.date_entry = DateEntry(date_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2)
        self.date_entry.pack(side="left", padx=5)
        self.date_entry.bind("<<DateEntrySelected>>", lambda e: self.load_data())

        # Search frame
        search_frame = tk.Frame(self, bg="lightgray")
        search_frame.place(relx=1.0, x=-285, y=70)

        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=20)
        self.search_entry.pack(side="left", padx=5)

        search_button = tk.Button(search_frame, text="Search", command=self.search_student, font=("Arial", 12))
        search_button.pack(side="right", padx=5)

        # Table Frame
        table_frame = tk.Frame(self, bg="lightgray")
        table_frame.pack(fill="both", expand=True)

        columns = ("Student ID", "Name", "Status", "Time In", "Date")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white",
                        borderwidth=1,
                        relief="solid",
                        rowheight=25)

        style.configure("Treeview.Heading", 
                        font=("Arial", 12, "bold"),
                        background="#4682B4",
                        foreground="white",
                        borderwidth=1,
                        relief="solid")

        style.map("Treeview", background=[("selected", "#87CEFA")])

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")

        # Scrollbars
        v_scrollbar = tk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")

        h_scrollbar = tk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side="bottom", fill="x")

        self.table.pack(fill="both", expand=True)

        # Bottom buttons
        bottom_frame = tk.Frame(self, height=130, bg="lightgray")
        bottom_frame.pack(fill="x", side="bottom")

        add_record_btn = tk.Button(bottom_frame, text="Add Record", font=("Arial", 12), bg="#4682B4", fg="white", width=14, command=self.add_records)
        add_record_btn.pack(side="left", padx=20, pady=10)

        delete_btn = tk.Button(bottom_frame, text="Delete", font=("Arial", 12), bg="#4682B4", fg="white", command=self.delete_selected_row, width=14)
        delete_btn.pack(side="left", padx=20, pady=10)

        generateReport_btn = tk.Button(bottom_frame, text="Generate Report", font=("Arial", 12), bg="#4682B4", fg="white", width=14, command=self.generate_report)
        generateReport_btn.pack(side="left", padx=20, pady=10)

        btn_export = tk.Button(bottom_frame, text="Export Students (Excel)", font=("Arial", 12), bg="#4682B4", fg="white", command=self.export_to_excel, width=23)
        btn_export.pack(side="right", padx=10, pady=10)
        
        btn_import = tk.Button(bottom_frame, text="Import Students (Excel)", font=("Arial", 12), bg="#4682B4", fg="white", command=self.import_excel, width=25)
        btn_import.pack(side="right", padx=10, pady=10)

        self.table.bind("<Double-1>", self.on_double_click)

        # Load initial data
        self.load_data()

    def initialize_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Create students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    fingerprint_position INTEGER,
                    year_level TEXT,
                    course TEXT
                )
            """)
            
            # Create attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    time_in TEXT NOT NULL,
                    status TEXT DEFAULT 'Present',
                    synced INTEGER DEFAULT 0,
                    course_name TEXT,
                    section_name TEXT,
                    subject_name TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id)
                )
            """)
            
            # Create professor_students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS professor_students (
                    professor_id TEXT,
                    student_id TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors(username),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    PRIMARY KEY (professor_id, student_id)
                )
            """)
            
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
        finally:
            if conn:
                conn.close()

    def load_data(self):
        """Load attendance data based on report type and date"""
        report_type = self.report_type.get()
        selected_date = self.date_entry.get_date()
        
        # Clear existing data
        for row in self.table.get_children():
            self.table.delete(row)
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            if report_type == "daily":
                date_str = selected_date.strftime("%Y-%m-%d")
                query = """
                    SELECT a.student_id, s.name, a.status, a.time_in, date(a.time_in)
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE date(a.time_in) = ?
                    AND a.section_name = ? AND a.subject_name = ? AND a.course_name = ?
                    ORDER BY a.time_in
                """
                params = (date_str, self.section_name, self.subject, self.course_name)
                
            elif report_type == "weekly":
                start_date = selected_date - datetime.timedelta(days=selected_date.weekday())
                end_date = start_date + datetime.timedelta(days=6)
                query = """
                    SELECT a.student_id, s.name, a.status, a.time_in, date(a.time_in)
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE date(a.time_in) BETWEEN ? AND ?
                    AND a.section_name = ? AND a.subject_name = ? AND a.course_name = ?
                    ORDER BY a.time_in
                """
                params = (start_date.strftime("%Y-%m-%d"), 
                         end_date.strftime("%Y-%m-%d"),
                         self.section_name, self.subject, self.course_name)
                
            else:  # monthly
                year = selected_date.year
                month = selected_date.month
                query = """
                    SELECT a.student_id, s.name, a.status, a.time_in, date(a.time_in)
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE strftime('%Y', a.time_in) = ? 
                    AND strftime('%m', a.time_in) = ?
                    AND a.section_name = ? AND a.subject_name = ? AND a.course_name = ?
                    ORDER BY a.time_in
                """
                params = (str(year), f"{month:02d}", 
                         self.section_name, self.subject, self.course_name)
                
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Insert data into table
            for row in rows:
                self.table.insert("", "end", values=row)
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load attendance: {str(e)}")
        finally:
            conn.close()

    def generate_report(self):
        """Generate PDF report of attendance"""
        report_type = self.report_type.get()
        selected_date = self.date_entry.get_date()
        filename = f"attendance_report_{report_type}_{selected_date.strftime('%Y%m%d')}.pdf"
        
        # Get data from table
        data = []
        for item in self.table.get_children():
            data.append(self.table.item(item)['values'])
            
        if not data:
            messagebox.showwarning("Warning", "No attendance data to generate report")
            return
            
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.cell(200, 10, txt=f"Attendance Report - {report_type.capitalize()}", 
                ln=1, align='C')
        pdf.cell(200, 10, txt=f"Date: {selected_date.strftime('%Y-%m-%d')}", 
                ln=1, align='C')
        pdf.cell(200, 10, txt=f"Section: {self.section_name} | Subject: {self.subject}", 
                ln=1, align='C')
        pdf.ln(10)
        
        # Table header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 10, "Student ID", 1)
        pdf.cell(60, 10, "Name", 1)
        pdf.cell(40, 10, "Status", 1)
        pdf.cell(50, 10, "Time In", 1)
        pdf.ln()
        
        # Table rows
        pdf.set_font("Arial", size=10)
        for row in data:
            # Convert all values to strings to avoid the AttributeError
            row = [str(item) if item is not None else "" for item in row]
            pdf.cell(40, 10, row[0], 1)
            pdf.cell(60, 10, row[1], 1)
            pdf.cell(40, 10, row[2], 1)
            pdf.cell(50, 10, row[3], 1)
            pdf.ln()
            
        # Save file
        try:
            pdf.output(filename)
            messagebox.showinfo("Success", f"Report generated as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def on_double_click(self, event):
        """Handle double-click event on a cell to make it editable."""
        item = self.table.identify_row(event.y)
        column = self.table.identify_column(event.x)

        if not item or not column:
            return

        column_id = int(column[1:]) - 1
        item_values = self.table.item(item, "values")

        if not item_values or column_id >= len(item_values):
            return

        x, y, width, height = self.table.bbox(item, column_id)
        entry = tk.Entry(self.table)
        entry.place(x=x, y=y, width=width, height=height)

        entry.insert(0, item_values[column_id])

        def save_edit(event):
            new_value = entry.get()
            updated_values = list(item_values)
            updated_values[column_id] = new_value
            self.table.item(item, values=updated_values)

            # Update database
            student_id = updated_values[0]
            column_name = ["student_id", "name", "status", "time_in", "date"][column_id]
            self.update_database(student_id, column_name, new_value)

            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def update_database(self, student_id, column, new_value):
        """Update database with edited value"""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE attendance SET {column} = ? WHERE student_id = ?", (new_value, student_id))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_selected_row(self):
        """Delete selected attendance record"""
        selected_item = self.table.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a record to delete")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if not confirm:
            return

        item_id = selected_item[0]
        student_id = self.table.item(item_id, "values")[0]
        time_in = self.table.item(item_id, "values")[3]

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance WHERE student_id = ? AND time_in = ?", (student_id, time_in))
            conn.commit()
            self.table.delete(item_id)
            messagebox.showinfo("Success", "Record deleted successfully")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def export_to_excel(self):
        """Export attendance data to Excel"""
        try:
            conn = sqlite3.connect(DB_NAME)
            query = """
                SELECT a.student_id, s.name, a.status, a.time_in, a.section_name, a.subject_name
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.section_name = ? AND a.subject_name = ?
            """
            df = pd.read_sql_query(query, conn, params=(self.section_name, self.subject))
            
            if df.empty:
                messagebox.showwarning("Warning", "No attendance records to export")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                title="Save Attendance Report"
            )
            
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Attendance data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
        finally:
            if conn:
                conn.close()

    def import_excel(self):
        """Import student data from Excel with enrollment"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx;*.xls")],
            title="Select Excel File"
        )
        
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            required_columns = ["student_id", "name", "email", "year_level", "course"]
            
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error", "Excel file must contain: student_id, name, email, year_level, course")
                return

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            for _, row in df.iterrows():
                # Insert student
                cursor.execute("""
                    INSERT OR REPLACE INTO students (student_id, name, email, year_level, course)
                    VALUES (?, ?, ?, ?, ?)
                """, (row["student_id"], row["name"], row["email"], row["year_level"], row["course"]))

                # Link student to professor and enroll in current section/subject
                cursor.execute("""
                    INSERT OR IGNORE INTO professor_students (professor_id, student_id)
                    VALUES (?, ?)
                """, (self.current_professor, row["student_id"]))
                
                # Enroll student in this course/section/subject
                cursor.execute("""
                    INSERT OR REPLACE INTO enrollments 
                    (student_id, course_name, section_name, subject_name)
                    VALUES (?, ?, ?, ?)
                """, (row["student_id"], self.course_name, self.section_name, self.subject))

            conn.commit()
            messagebox.showinfo("Success", "Student data imported and enrolled successfully")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")
        finally:
            if conn:
                conn.close()

    def search_student(self):
        """Search for student in attendance records"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.load_data()
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            query = """
                SELECT a.student_id, s.name, a.status, a.time_in, date(a.time_in)
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE (a.student_id LIKE ? OR s.name LIKE ?)
                AND a.section_name = ? AND a.subject_name = ?
                ORDER BY a.time_in
            """
            params = (f"%{search_term}%", f"%{search_term}%", self.section_name, self.subject)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Clear and update table
            for row in self.table.get_children():
                self.table.delete(row)
                
            for row in rows:
                self.table.insert("", "end", values=row)
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Search failed: {str(e)}")
        finally:
            if conn:
                conn.close()

    def add_records(self):
        """Add new attendance record"""
        add_window = tk.Toplevel(self)
        add_window.title("Add Attendance Record")
        add_window.geometry("400x300")

        tk.Label(add_window, text="Student ID:", font=("Arial", 12)).pack(pady=5)
        student_id_entry = tk.Entry(add_window, font=("Arial", 12))
        student_id_entry.pack(pady=5)

        tk.Label(add_window, text="Status:", font=("Arial", 12)).pack(pady=5)
        status_var = tk.StringVar(value="Present")
        status_menu = tk.OptionMenu(add_window, status_var, "Present", "Late", "Absent")
        status_menu.pack(pady=5)

        def save_record():
            student_id = student_id_entry.get().strip()
            status = status_var.get()
            
            if not student_id:
                messagebox.showwarning("Warning", "Student ID is required")
                return

            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                # Check if student exists
                cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
                if not cursor.fetchone():
                    messagebox.showerror("Error", "Student ID not found")
                    return

                # Insert attendance record
                time_in = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO attendance (student_id, time_in, status, section_name, subject_name, course_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, time_in, status, self.section_name, self.subject, self.course_name))
                
                conn.commit()
                messagebox.showinfo("Success", "Attendance record added")
                add_window.destroy()
                self.load_data()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to add record: {str(e)}")
            finally:
                if conn:
                    conn.close()

        save_btn = tk.Button(add_window, text="Save", command=save_record, font=("Arial", 12), bg="#4682B4", fg="white")
        save_btn.pack(pady=10)

    def go_back_to_subjects(self):
        """Return to subjects view"""
        if self.dashboard_frame:
            self.dashboard_frame.pack(fill="both", expand=True)
            if hasattr(self.dashboard_frame, 'current_course') and hasattr(self.dashboard_frame, 'current_section'):
                self.dashboard_frame.manage_section(
                    self.dashboard_frame.current_course,
                    self.dashboard_frame.current_section
                )
            self.pack_forget()
        else:
            self.parent.show_dashboard()
