# attendance_list_frame.py
import pandas as pd
import sqlite3
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

DB_NAME = "professor_account.db"  # Ensure this matches the database name

def create_database():
    """Creates a database and student table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            fingerprint TEXT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    

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

        # Update the title label to show section name and subject
        title_text = f"{self.section_name} - {self.subject}" if self.section_name and self.subject else "Attendance List"
        title_label = tk.Label(self, text=title_text, font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        title_label.pack(pady=15, fill="x")

        # Create a frame for the left side buttons (Back button)
        button_frame = tk.Frame(self, bg="lightgray")
        button_frame.place(x=10, y=10)

        # Back button positioned on the left side
        back_button = tk.Button(
            button_frame,
            text="Back",
            font=("Arial", 14),
            bg="#4682B4",
            fg="white",
            width=10,
            command=self.go_back_to_subjects  # Link to the back function
        )
        back_button.pack(side="top", anchor="w", pady=10, ipadx=3)

        # Create a separate frame for the search bar on the right side
        search_frame = tk.Frame(self, bg="lightgray")
        search_frame.place(relx=1.0, x=-285, y=70)  # Aligns it to the right side with an offset

        # Search entry widget
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=20)
        self.search_entry.pack(side="left", padx=5)

        # Search button
        search_button = tk.Button(search_frame, text="Search", command=self.search_student, font=("Arial", 12))
        search_button.pack(side="right", padx=5)

        # Table Frame
        table_frame = tk.Frame(self, bg="lightgray")
        table_frame.pack(fill="both", expand=True)

        columns = ("Student_Number", "Name", "Fingerprint", "April 11", "April 12", "April 13")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Apply Custom Styling
        style = ttk.Style()
        style.theme_use("clam")  # Use "clam" theme for better styling
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white",
                        borderwidth=1,  # Add border
                        relief="solid",  # Solid border style
                        rowheight=25)  # Row height for visibility

        style.configure("Treeview.Heading", 
                        font=("Arial", 12, "bold"),
                        background="#4682B4",
                        foreground="white",
                        borderwidth=1,  # Border for headings
                        relief="solid")

        style.map("Treeview", background=[("selected", "#87CEFA")])  # Highlight selected row

        for col in columns:
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, width=150, anchor="center", stretch=tk.NO)

        v_scrollbar = tk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")

        h_scrollbar = tk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side="bottom", fill="x")

        self.table.pack(fill="both", expand=True)

        bottom_frame = tk.Frame(self, height=130, bg="lightgray")
        bottom_frame.pack(fill="x", side="bottom")

        add_record_btn = tk.Button(bottom_frame, text="Add Record", font=("Arial", 12), bg="#4682B4", fg="white", width=14, command=self.add_records)
        add_record_btn.pack(side="left", padx=20, pady=10)

        delete_btn = tk.Button(bottom_frame, text="Delete", font=("Arial", 12), bg="#4682B4", fg="white",command=self.delete_selected_row, width=14)
        delete_btn.pack(side="left", padx=20, pady=10)

        generateReport_btn = tk.Button(bottom_frame, text="Generate Report", font=("Arial", 12), bg="#4682B4", fg="white", width=14)
        generateReport_btn.pack(side="left", padx=20, pady=10)

        btn_export = tk.Button(bottom_frame, text="Export Students (Excel)",font=("Arial", 12), bg="#4682B4", fg="white", command=self.export_to_excel, width=23)
        btn_export.pack(side="right", padx=10, pady=10)
        
        btn_import = tk.Button(bottom_frame, text="Import Students (Excel)",font=("Arial", 12), bg="#4682B4", fg="white", command=self.import_excel, width=25)
        btn_import.pack(side="right", padx=10, pady=10)

        self.table.bind("<Double-1>", self.on_double_click)

        # Load data AFTER the table is initialized
        self.load_data()

    
    def on_double_click(self, event):
        """Handle double-click event on a cell to make it editable."""
        item = self.table.identify_row(event.y)  # Get the row ID
        column = self.table.identify_column(event.x)  # Get the column ID

        if not item or not column:
            return

        column_id = int(column[1:]) - 1  # Convert from "#1" format to index
        item_values = self.table.item(item, "values")  # Get current row values

        if not item_values or column_id >= len(item_values):
            return

        x, y, width, height = self.table.bbox(item, column_id)  # Get cell position
        entry = tk.Entry(self.table)
        entry.place(x=x, y=y, width=width, height=height)

        entry.insert(0, item_values[column_id])  # Insert current value
        entry.focus()

        def save_edit(event):
            new_value = entry.get()
            updated_values = list(item_values)
            updated_values[column_id] = new_value
            self.table.item(item, values=updated_values)  # Update Treeview

            # Update database
            student_id = updated_values[0]  # Assuming first column is student_number
            column_name = ["student_id", "name", "course", "year_level", "Fingerprint", "late", "absent"][column_id]
            self.update_database(student_id, column_name, new_value)

            entry.destroy()

        entry.bind("<Return>", save_edit)  # Save when pressing Enter
        entry.bind("<FocusOut>", lambda e: entry.destroy())  # Close entry if focus is lost

    def update_database(self, student_id, column, new_value):
        """Updates the database with the new value."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE students SET {column} = ? WHERE student_id = ?", (new_value, student_id))
        conn.commit()
        conn.close()

    def delete_selected_row(self):
        """Deletes an entire student record from the database and table."""
        selected_item = self.table.selection()

        if not selected_item:
            messagebox.showwarning("Warning", "Please select a row to delete!")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if not confirm:
            return

        item_id = selected_item[0]
        student_id = self.table.item(item_id, "values")[0]  

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()
        conn.close()

        self.table.delete(item_id)  
    
    def import_excel(self):
        """Imports students from an Excel file into the database."""
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.csv")])

        if not file_path:
            return

        try:
            df = pd.read_excel(file_path, engine='openpyxl')

            # Required columns from the Excel file
            required_columns = {
                "Student Number": "student_id",
                "Name": "name",
                "Course": "course",
                "Year Level": "year_level"
            }
            
            if not set(required_columns.keys()).issubset(df.columns):
                messagebox.showerror("Error", "Excel file must contain: Student Number, Name, Course, Year Level")
                return

            df = df[list(required_columns.keys())]
            df.rename(columns=required_columns, inplace=True)

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Insert students into the students table with professor_id
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR IGNORE INTO students (student_id, name, course, year_level, professor_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row["student_id"], row["name"], row["course"], row["year_level"], self.current_professor))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Student data imported successfully!")     
            self.load_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data.\n{str(e)}")


    def export_to_excel(self):
        """Exports student records to an Excel file."""
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM students WHERE professor_id = ?", conn, params=(self.current_professor,))
        conn.close()
        
        if df.empty:
            messagebox.showwarning("Warning", "No student records found!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel Files", "*.xlsx")])
        
        if file_path:
            df.to_excel(file_path, index=False, engine='openpyxl')
            messagebox.showinfo("Success", "Student records exported successfully!")

    def search_student(self):
        """Search for a student by name and update the table."""
        search_term = self.search_entry.get().strip().lower()
        if search_term:
            query = '''
                SELECT * FROM students 
                WHERE name LIKE ? 
                AND student_id IN (
                    SELECT student_id FROM professor_students 
                    WHERE professor_id = ?
                )
            '''
            self.load_data(query, (f"%{search_term}%", self.current_professor)) 
        else:
            self.load_data()  
        
    def load_data(self, query=None, params=None):
        """Loads data from the database into the GUI table based on the provided query or all data."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if query:
            cursor.execute(query, params)
        else:
            # Only load students belonging to the current professor through the professor_students table
            cursor.execute('''
                SELECT s.student_id, s.name, s.fingerprint 
                FROM students s
                JOIN professor_students ps ON s.student_id = ps.student_id
                WHERE ps.professor_id = ?
            ''', (self.current_professor,))

        rows = cursor.fetchall()
        conn.close()

        # Clear existing data
        for row in self.table.get_children():
            self.table.delete(row)

        # Insert new data
        for index, row in enumerate(rows):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.table.insert("", "end", values=row, tags=(tag,))

        self.table.tag_configure("evenrow", background="#F0F0F0")
        self.table.tag_configure("oddrow", background="white")
            
    def add_records(self):
        """Open a new window to add a student record."""
        register_window = tk.Toplevel(self)
        register_window.title("AMS")
        register_window.geometry("700x400")

        title_label = tk.Label(register_window, text="REGISTER YOUR ACCOUNT", font=("Helvetica", 18, "bold"), bg="lightgray")
        title_label.pack(pady=10)

        form_frame = tk.Frame(register_window, bg="white", bd=2, relief=tk.SUNKEN)
        form_frame.pack(padx=20, pady=20, fill="both", expand=False)

       
        fields = [
            ("Student Number:", 0), ("Name:", 1),
            ("Course:", 2), ("Year Level:", 3)
        ]

        entries = {}

        
        for text, row in fields:
            tk.Label(form_frame, text=text, font=("Arial", 12), bg="white").grid(row=row, column=0, padx=10, pady=10, sticky="e")
            entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
            entry.grid(row=row, column=1, padx=10, pady=10)
            entries[text] = entry  

        
        fingerprint_label = tk.Label(form_frame, text="Fingerprint Status: Not Scanned", font=("Arial", 10), fg="red", bg="white")
        fingerprint_label.grid(row=8, column=0, columnspan=2, pady=10)

        
        def scan_fingerprint_account():
            fingerprint_label.config(text="Fingerprint Status: Scanning...", fg="blue")
            fingerprint_label.after(2000, lambda: fingerprint_label.config(text="Fingerprint Status: Scanned Successfully", fg="green"))

        
        scan_btn = tk.Button(form_frame, text="Scan Fingerprint", font=("Arial", 12), bg="blue", fg="white", command=scan_fingerprint_account)
        scan_btn.grid(row=9, column=0, padx=10, pady=10, sticky="e")

       
        def register_account_inner():
            values = {key: entry.get().strip() for key, entry in entries.items()}
            fp_status = fingerprint_label.cget("text")

            if not values["Student Number:"] or not values["Name:"] or not values["Fingerprint:"] or not values["April 11:"]:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return

            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()

                
                cursor.execute('''
                    INSERT INTO students (student_id, name, Fingerprint, April 11)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    values["Student Number:"], values["Name:"], values["Fingerprint:"], values["April 11:"], fp_status))

                
                cursor.execute('''
                    INSERT INTO professor_students (professor_id, student_id)
                    VALUES (?, ?)
                ''', (self.current_professor, values["Student Number:"]))

                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Student registered successfully!")
                self.load_data()  
                register_window.destroy()  
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "A student with that ID already exists.")

        
        register_btn = tk.Button(form_frame, text="Register", font=("Arial", 12), bg="#4682B4", fg="white", command=register_account_inner)
        register_btn.grid(row=9, column=1, padx=10, pady=10, sticky="w")
        
    def go_back_to_subjects(self):
        """Navigate back to the subjects_frame in the DashboardFrame"""
        if self.dashboard_frame:
            try:
                # First show the dashboard frame again
                self.dashboard_frame.pack(fill="both", expand=True)
                
                # Then reconstruct the subjects view
                if hasattr(self.dashboard_frame, 'current_course') and hasattr(self.dashboard_frame, 'current_section'):
                    self.dashboard_frame.manage_section(
                        self.dashboard_frame.current_course,
                        self.dashboard_frame.current_section
                    )
                
                self.pack_forget()  # Hide the attendance list frame
            except Exception as e:
                print(f"Navigation error: {e}")
                self.parent.show_dashboard()  # Fallback to main dashboard
        else:
            print("DashboardFrame instance not available")
            self.parent.show_dashboard()  # Fallback to main dashboard


create_database()
