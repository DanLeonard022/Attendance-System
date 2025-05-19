
# frames/dashboard_frame.py
import tkinter as tk
import sqlite3
from tkinter import messagebox, simpledialog, ttk
import datetime
from email_handler import EmailHandler
from attendance import AttendanceApp

class DashboardFrame(tk.Frame):
    def __init__(self, parent, db, current_professor):
        super().__init__(parent, bg="white")
        self.db = db
        self.parent = parent
        self.current_professor = current_professor
        self.current_course = None  # Track current course
        self.current_section = None
        self.current_subject = None
        self.attendance_app = None 
        
        # Initialize EmailHandler with secure credentials
        self.email_handler = EmailHandler(
            sender_email="bio.hunters10@gmail.com",
            sender_password="ljab fqkc ptdf qwzk"
        )

        # Left frame with menu buttons
        self.left_frame = tk.Frame(self, bg="#2c3e50", width=200, relief=tk.SUNKEN, bd=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.left_frame.pack_propagate(False)
        self.left_frame.config(height=600)

        menu_label = tk.Label(self.left_frame, text="MENU", font=("Helvetica", 18, "bold"), 
                            bg="#2c3e50", fg="white")
        menu_label.pack(pady=20)

        menu_buttons_frame = tk.Frame(self.left_frame, bg="#2c3e50")
        menu_buttons_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Menu buttons with consistent styling
        button_style = {"font": ("Arial", 12), "bg": "#3498db", "fg": "white", 
                       "activebackground": "#2980b9", "width": 18, "bd": 0}
        
        dashboard_button = tk.Button(menu_buttons_frame, text="ATTENDANCE LOG", 
                                  command=self.show_dashboard_screen, **button_style)
        dashboard_button.pack(pady=10, ipady=5)

        records_button = tk.Button(menu_buttons_frame, text="VIEW/ADD RECORDS", 
                                 command=self.show_records_screen, **button_style)
        records_button.pack(pady=10, ipady=5)

        schedule_button = tk.Button(menu_buttons_frame, text="SCHEDULE", 
                                  command=self.show_schedule_screen, **button_style)
        schedule_button.pack(pady=10, ipady=5)

        account_button = tk.Button(menu_buttons_frame, text="ACCOUNT", 
                                 command=self.show_account_screen, **button_style)
        account_button.pack(pady=10, ipady=5)

        logout_button = tk.Button(menu_buttons_frame, text="LOG OUT", 
                                command=self.parent.show_login_frame, 
                                bg="#e74c3c", fg="white", activebackground="#c0392b",
                                font=("Arial", 12), width=18, bd=0)
        logout_button.pack(pady=10, ipady=5)

        # Right frame for content
        self.right_frame = tk.Frame(self, bg="#ecf0f1", width=600, relief=tk.SUNKEN, bd=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Show dashboard by default
        self.show_dashboard_screen()
    
    def show_dashboard_screen(self):
        self.clear_right_frame()
        self.right_frame.unbind_all("<MouseWheel>")

        # Header
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        
        dashboard_label = tk.Label(header_frame, text="ATTENDANCE LOG", 
                                font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        dashboard_label.pack(pady=20)
        
        # Control buttons frame
        control_frame = tk.Frame(self.right_frame, bg="#ecf0f1")
        control_frame.pack(fill="x", pady=10, padx=20)
        
        # Course selection
        tk.Label(control_frame, text="Select Course:", font=("Arial", 12), bg="#ecf0f1").pack(side="left", padx=5)
        self.course_var = tk.StringVar()
        course_combobox = ttk.Combobox(control_frame, textvariable=self.course_var, font=("Arial", 12), width=25)
        course_combobox.pack(side="left", padx=5)
        
        # Load courses into combobox
        try:
            self.db.cursor.execute(
                "SELECT name FROM courses WHERE professor_id = ?",
                (self.current_professor,)
            )
            courses = [course[0] for course in self.db.cursor.fetchall()]
            course_combobox['values'] = courses
            if courses:
                course_combobox.current(0)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load courses: {str(e)}")

        # Attendance buttons
        button_frame = tk.Frame(control_frame, bg="#ecf0f1")
        button_frame.pack(side="right", padx=10)
        
        self.attendance_running = False  
        self.attendance_thread = None  

        start_button = tk.Button(button_frame, text="Start Attendance", font=("Arial", 12),
                               bg="#2ecc71", fg="white", command=self.start_attendance,
                               width=15)
        start_button.pack(side="left", padx=5)

        stop_button = tk.Button(button_frame, text="Stop Attendance", font=("Arial", 12),
                              bg="#e74c3c", fg="white", command=self.stop_attendance,
                              width=15)
        stop_button.pack(side="left", padx=5)
        
        # Add these buttons to your control_frame
        register_button = tk.Button(button_frame, text="Register Fingerprint", font=("Arial", 12),
                                  bg="#9b59b6", fg="white", command=self.register_fingerprint,
                                  width=15)
        register_button.pack(side="left", padx=5)

        

        # Attendance records table
        table_frame = tk.Frame(self.right_frame, bg="#ecf0f1")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        self.attendance_tree = ttk.Treeview(table_frame, columns=("Student ID", "Name", "Time In"), 
                                          show="headings", yscrollcommand=scrollbar.set)
        self.attendance_tree.heading("Student ID", text="Student ID")
        self.attendance_tree.heading("Name", text="Name")
        self.attendance_tree.heading("Time In", text="Time In")
        self.attendance_tree.column("Student ID", width=120, anchor="center")
        self.attendance_tree.column("Name", width=200, anchor="w")
        self.attendance_tree.column("Time In", width=150, anchor="center")
        self.attendance_tree.pack(fill="both", expand=True)

        scrollbar.config(command=self.attendance_tree.yview)
        
        status_frame = tk.Frame(self.right_frame, bg="#ecf0f1")
        status_frame.pack(fill="x", pady=5, padx=20)
        
        report_button = tk.Button(status_frame, text="Generate Report", font=("Arial", 12),
                                 bg="#f39c12", fg="white", command=self.generate_report,
                                 width=15)
        report_button.pack(side="left", padx=5)
        
        self.connection_status = tk.Label(
            status_frame, 
            text="Online" if self.parent.firebase_sync.check_connection() else "Offline",
            font=("Arial", 10),
            fg="green" if self.parent.firebase_sync.check_connection() else "red"
        )
        self.connection_status.pack(side="right")
        
        # Add a refresh button
        tk.Button(
            status_frame,
            text="Refresh Connection",
            font=("Arial", 10),
            command=self.check_connection_status
        ).pack(side="right", padx=5)

        # Load sample data (replace with actual database query)
        self.load_attendance_data_from_db()

    def check_connection_status(self):
        """Check and update connection status"""
        is_connected = self.parent.firebase_sync.check_connection()
        self.connection_status.config(
            text="Online" if is_connected else "Offline",
            fg="green" if is_connected else "red"
        )
        if is_connected:
            messagebox.showinfo("Connection", "Connected to Firebase")
        else:
            messagebox.showwarning("Connection", "Offline - Working locally. Data will sync when connection is restored.")
        
    def load_attendance_data_from_db(self):
        """Load attendance data with proper column references"""
        try:
            self.db.cursor.execute('''
                SELECT 
                    attendance.student_id, 
                    students.name, 
                    attendance.time_in,
                    attendance.course_name,
                    attendance.section_name,
                    attendance.subject_name
                FROM attendance
                JOIN students ON attendance.student_id = students.student_id
                ORDER BY attendance.time_in DESC
            ''')

            records = self.db.cursor.fetchall()

            # Clear existing table entries
            for item in self.attendance_tree.get_children():
                self.attendance_tree.delete(item)

            # Insert records
            for record in records:
                self.attendance_tree.insert("", "end", values=record)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load attendance records:\n{str(e)}")



    def show_records_screen(self):
        """Show the view/add records screen with course hierarchy"""
        self.clear_right_frame()
        self.right_frame.unbind_all("<MouseWheel>")
        self.current_course = None
        self.current_section = None
        self.current_subject = None
        
        # Header
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=50)
        header_frame.pack(fill="x", pady=(0, 20))
        
        records_label = tk.Label(header_frame, text="VIEW/ADD RECORDS", 
                              font=("Helvetica", 18, "bold"), bg="#4682B4", fg="white")
        records_label.pack(pady=15)
        

        
        

        # Load courses from database
        self.load_courses()

    def load_courses(self):
        """Load courses from database with fixed layout"""
        # Clear previous widgets
        if hasattr(self, 'courses_container'):
            self.courses_container.destroy()
        
        # Create main container
        self.courses_container = tk.Frame(self.right_frame, bg="#f8f9fa",relief=tk.SUNKEN, bd=2)
        self.courses_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header frame
        header_frame = tk.Frame(self.courses_container, bg="#f8f9fa")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Add Course button
        add_btn = tk.Button(
            header_frame,
            text="+ Add New Course",
            font=("Arial", 14, "bold"),
            bg="#28a745",
            fg="white",
            bd=0,
            padx=15,
            command=self.add_course_dialog
        )
        add_btn.pack(side="left", anchor="w", pady=8, padx=8)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="COURSES",
            font=("Helvetica", 25, "bold"),
            bg="#f8f9fa",
            fg="#343a40",

        )
        title_label.pack(side="left", padx=70)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.courses_container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.courses_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f8f9fa")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        try:
            # Get courses from database
            self.db.cursor.execute(
                "SELECT name FROM courses WHERE professor_id = ?",
                (self.current_professor,)
            )
            courses = [course[0] for course in self.db.cursor.fetchall()]
            
            if not courses:
                # Empty state
                empty_frame = tk.Frame(scroll_frame, bg="#f8f9fa", pady=50)
                empty_frame.pack(fill="x")
                
                tk.Label(
                    empty_frame,
                    text="📚 No courses found",
                    font=("Arial", 16),
                    bg="#f8f9fa",
                    fg="#6c757d"
                ).pack()
            else:
                # Display courses in single column
                for course in courses:
                    # Create course card frame
                    course_frame = tk.Frame(
                        scroll_frame,
                        bg="white",
                        bd=1,
                        relief="solid",
                        padx=15,
                        pady=10
                    )
                    course_frame.pack(fill="x", pady=5, padx=90)
                    
                    # Course name label (top part)
                    name_label = tk.Label(
                        course_frame,
                        text=course,
                        font=("Arial", 14, "bold"),
                        bg="white",
                        fg="#343a40",
                        anchor="center"
                    )
                    name_label.pack(fill="x", pady=(0, 5),padx=5)
                    
                    # Add clickable behavior to the name
                    name_label.bind("<Button-1>", lambda e, c=course: self.load_sections(c))
                    
                    # Button frame (bottom part)
                    btn_frame = tk.Frame(course_frame, bg="white")
                    btn_frame.pack(fill="x", side="right")
                    
                    # View Sections button
                    view_btn = tk.Button(
                        btn_frame,
                        text="View Sections",
                        font=("Arial", 12),
                        bg="#007bff",
                        fg="white",
                        bd=0,
                        padx=12,
                        pady=3,
                        command=lambda c=course: self.load_sections(c)
                    )
                    view_btn.pack(side="left", padx=(0, 5))
                    
                    # Delete button
                    del_btn = tk.Button(
                        btn_frame,
                        text="Delete",
                        font=("Arial", 12),
                        bg="#dc3545",
                        fg="white",
                        bd=0,
                        padx=12,
                        pady=3,
                        command=lambda c=course: self.delete_course(c)
                    )
                    del_btn.pack(side="right")
        
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load courses: {str(e)}")

    def add_course_dialog(self):
        """Modern dialog to add a new course"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Course")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Set dialog background
        dialog.configure(bg="#f8f9fa")
        
        # Header
        header_frame = tk.Frame(dialog, bg="#343a40", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="Add New Course",
            font=("Helvetica", 16, "bold"),
            bg="#343a40",
            fg="white"
        ).pack(pady=15)
        
        # Form content
        content_frame = tk.Frame(dialog, bg="#f8f9fa", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        tk.Label(
            content_frame,
            text="Course Name:",
            font=("Arial", 12),
            bg="#f8f9fa",
            fg="#495057"
        ).pack(anchor="w", pady=(0, 5))
        
        course_entry = tk.Entry(
            content_frame,
            font=("Arial", 12),
            width=30,
            bd=1,
            relief="solid",
            highlightbackground="#ced4da",
            highlightcolor="#007bff",
            highlightthickness=1
        )
        course_entry.pack(fill="x", pady=(0, 15))
        course_entry.focus()
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_course():
            course_name = course_entry.get().strip()
            if not course_name:
                messagebox.showwarning("Warning", "Course name cannot be empty!")
                return
                
            try:
                self.db.cursor.execute(
                    "INSERT INTO courses (name, professor_id) VALUES (?, ?)",
                    (course_name, self.current_professor)
                )
                self.db.conn.commit()
                self.load_courses()
                dialog.destroy()
                messagebox.showinfo("Success", "Course added successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add course: {str(e)}")

        # Save button with modern design
        save_btn = tk.Button(
            button_frame,
            text="Save Course",
            font=("Arial", 12, "bold"),
            bg="#28a745",
            fg="white",
            bd=0,
            padx=15,
            pady=5,
            activebackground="#218838",
            command=save_course
        )
        save_btn.pack(side="right", padx=(5, 0))
        
        # Cancel button with modern design
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 12),
            bg="#6c757d",
            fg="white",
            bd=0,
            padx=15,
            pady=5,
            activebackground="#5a6268",
            command=dialog.destroy
        )
        cancel_btn.pack(side="right")

    def delete_course(self, course_name):
        """Modern dialog to confirm course deletion"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the course '{course_name}'?\nThis will also delete all associated sections and subjects.",
            icon="warning"
        )
        
        if confirm:
            try:
                # First delete all sections and subjects associated with this course
                self.db.cursor.execute(
                    "DELETE FROM subjects WHERE course_name = ? AND professor_id = ?",
                    (course_name, self.current_professor)
                )  # Added missing closing parenthesis
                
                self.db.cursor.execute(
                    "DELETE FROM sections WHERE course_name = ? AND professor_id = ?",
                    (course_name, self.current_professor)
                )  # Added missing closing parenthesis
                
                # Then delete the course itself
                self.db.cursor.execute(
                    "DELETE FROM courses WHERE name = ? AND professor_id = ?",
                    (course_name, self.current_professor)
                )
                
                self.db.conn.commit()
                self.load_courses()
                messagebox.showinfo("Success", "Course deleted successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete course: {str(e)}")
                self.db.conn.rollback()


    def manage_course(self, course_name):
        """Manage sections for a specific course"""
        self.clear_right_frame()
        self.current_course = course_name
        self.current_section = None
        self.current_subject = None
        
        # Header with back button
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        
        back_btn = tk.Button(header_frame, text="← Back to Courses", font=("Arial", 12),
                          bg="#3498db", fg="white", command=self.show_records_screen)
        back_btn.pack(side="left", padx=20)

        course_label = tk.Label(header_frame, text=f"Course: {course_name}", 
                             font=("Helvetica", 16, "bold"), bg="#4682B4", fg="white")
        course_label.pack(side="left", padx=10)

        # Add Section Button
        add_section_btn = tk.Button(self.right_frame, text="+ Add New Section",
                                  font=("Arial", 12), bg="#2ecc71", fg="white",
                                  command=lambda: self.add_section_dialog(course_name))
        add_section_btn.pack(pady=10, ipadx=10, ipady=5)

        # Load existing sections
        self.load_sections(course_name)

    def add_section_for_year(self, course_name, year_level):
        """Helper method to add section for specific year level"""
        # You'll need to implement logic to determine section prefix based on year
        default_prefix = ""
        if "1ST" in year_level:
            default_prefix = "LFCA1"
        elif "2ND" in year_level:
            default_prefix = "LFCA2"
        # Add similar for 3rd and 4th year
        
        section_name = simpledialog.askstring(
            "Add Section", 
            f"Enter section name for {year_level}:", 
            initialvalue=f"{default_prefix}XXMXXX"
        )
        
        if section_name:
            try:
                self.db.cursor.execute(
                    "INSERT INTO sections (name, course_name, professor_id) VALUES (?, ?, ?)",
                    (section_name, course_name, self.current_professor)
                )
                self.db.conn.commit()
                self.load_sections(course_name)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add section: {str(e)}")
            
    def add_section_dialog(self, course_name, year_level="1ST YEAR"):
        """Modern dialog to add new section with year level"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Section to {course_name}")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg="#f5f5f5")

        # Header
        header_frame = tk.Frame(dialog, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text=f"Add {year_level} Section",
            font=("Helvetica", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)

        # Content
        content_frame = tk.Frame(dialog, bg="#f5f5f5", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)

        tk.Label(
            content_frame,
            text="Section Name:",
            font=("Arial", 12),
            bg="#f5f5f5"
        ).pack(anchor="w", pady=(0, 5))

        section_entry = tk.Entry(
            content_frame,
            font=("Arial", 12),
            width=30
        )
        section_entry.pack(fill="x", pady=(0, 15))
        section_entry.focus()

        # Generate default section name based on year level
        default_prefix = {
            "1ST YEAR": "LFCA1",
            "2ND YEAR": "LFCA2",
            "3RD YEAR": "LFCA3",
            "4TH YEAR": "LFCA4"
        }.get(year_level, "SEC")
        section_entry.insert(0, f"{default_prefix}")

        def save_section():
            section_name = section_entry.get().strip()
            if not section_name:
                messagebox.showwarning("Warning", "Section name cannot be empty!")
                return
                
            try:
                self.db.cursor.execute(
                    """INSERT INTO sections 
                    (name, course_name, professor_id, year_level) 
                    VALUES (?, ?, ?, ?)""",
                    (section_name, course_name, self.current_professor, year_level)
                )
                self.db.conn.commit()
                self.load_sections(course_name)
                dialog.destroy()
                messagebox.showinfo("Success", "Section added successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add section: {str(e)}")

        # Buttons
        btn_frame = tk.Frame(content_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x", pady=(10, 0))

        save_btn = tk.Button(
            btn_frame,
            text="Save Section",
            font=("Arial", 12),
            bg="#27ae60",
            fg="white",
            bd=0,
            padx=15,
            command=save_section
        )
        save_btn.pack(side="right", padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            bd=0,
            padx=15,
            command=dialog.destroy
        )
        cancel_btn.pack(side="right")

    def delete_section(self, course_name, section_name):
        """Delete section with confirmation"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete section '{section_name}'?\n"
            f"This will also delete all associated subjects.",
            icon="warning"
        )
        
        if confirm:
            try:
                # First delete all subjects in this section
                self.db.cursor.execute(
                    """DELETE FROM subjects 
                    WHERE course_name = ? AND section_name = ? AND professor_id = ?""",
                    (course_name, section_name, self.current_professor)
                )
                
                # Then delete the section itself
                self.db.cursor.execute(
                    """DELETE FROM sections 
                    WHERE name = ? AND course_name = ? AND professor_id = ?""",
                    (section_name, course_name, self.current_professor)
                )
                
                self.db.conn.commit()
                self.load_sections(course_name)
                messagebox.showinfo("Success", "Section deleted successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete section: {str(e)}")
                self.db.conn.rollback()

    def load_sections(self, course_name):
        """Load sections with improved year-level grouped design"""
        self.clear_right_frame()
        self.current_course = course_name
        self.right_frame.pack_propagate(False)

        # Header with back button and course name
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 10))

        back_btn = tk.Button(
            header_frame,
            text="← Back to Courses",
            font=("Arial", 12),
            bg="#3498db",
            fg="white",
            bd=0,
            command=self.show_records_screen
        )
        back_btn.pack(side="left", padx=20, pady=10)

        course_label = tk.Label(
            header_frame,
            text=f"Course: {course_name}",
            font=("Helvetica", 16, "bold"),
            bg="#4682B4",
            fg="white"
        )
        course_label.pack(side="left", padx=10, pady=10)

        # Main container with scrollable area
        container = tk.Frame(self.right_frame, bg="#f5f5f5",relief=tk.SUNKEN, bd=2)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Scrollbar setup
        canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Mouse wheel scrolling
        def on_mouse_wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        try:
            # Get all sections for this course from database
            self.db.cursor.execute(
                "SELECT name, year_level FROM sections WHERE course_name = ? AND professor_id = ?",
                (course_name, self.current_professor)
            )
            sections = self.db.cursor.fetchall()

            # Organize sections by year level
            year_levels = {
                "1ST YEAR": [],
                "2ND YEAR": [],
                "3RD YEAR": [],
                "4TH YEAR": []
            }

            for section_name, year_level in sections:
                year_level = year_level.strip().upper() if year_level else "1ST YEAR"
                if year_level in year_levels:
                    year_levels[year_level].append(section_name)

            # Create UI for each year level
            for year, sections_list in year_levels.items():
                # Year level group frame
                year_frame = tk.Frame(
                    scroll_frame,
                    bg="white",
                    bd=1,
                    relief="groove",
                    padx=15,
                    pady=10
                )
                year_frame.pack(fill="x", padx=70, pady=15, ipady=10,ipadx=170)

                # Year level header
                year_header = tk.Frame(year_frame, bg="white")
                year_header.pack(fill="x", pady=(0, 10))

                tk.Label(
                    year_header,
                    text=year,
                    font=("Helvetica", 14, "bold"),
                    bg="white",
                    fg="#2c3e50"
                ).pack(side="left")

                # Add section button for this year level
                add_btn = tk.Button(
                    year_header,
                    text="+ Add Section",
                    font=("Arial", 10),
                    bg="#27ae60",
                    fg="white",
                    bd=0,
                    padx=10,
                    command=lambda y=year: self.add_section_dialog(course_name, y)
                )
                add_btn.pack(side="right")

                # Display sections for this year level
                if sections_list:
                    for section in sections_list:
                        section_frame = tk.Frame(
                            year_frame,
                            bg="#f8f9fa",
                            padx=10,
                            pady=8
                        )
                        section_frame.pack(fill="x", pady=3)

                        # Section name (clickable)
                        section_btn = tk.Label(
                            section_frame,
                            text=section,
                            font=("Arial", 12, "bold"),
                            bg="#f8f9fa",
                            fg="#3498db",
                            cursor="hand2"
                        )
                        section_btn.pack(side="left")
                        section_btn.bind("<Button-1>", lambda e, s=section: self.manage_section(course_name, s))

                        # Action buttons
                        btn_frame = tk.Frame(section_frame, bg="#f8f9fa")
                        btn_frame.pack(side="right")

                        # View Subjects button
                        view_btn = tk.Button(
                            btn_frame,
                            text="View Subjects",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            bd=0,
                            padx=8,
                            command=lambda s=section: self.manage_section(course_name, s)
                        )
                        view_btn.pack(side="left", padx=2)

                        # Delete button
                        del_btn = tk.Button(
                            btn_frame,
                            text="Delete",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            bd=0,
                            padx=8,
                            command=lambda s=section: self.delete_section(course_name, s)
                        )
                        del_btn.pack(side="left", padx=2)
                else:
                    # Empty state for this year level
                    tk.Label(
                        year_frame,
                        text="No sections yet",
                        font=("Arial", 11),
                        bg="white",
                        fg="#7f8c8d"
                    ).pack(pady=5)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load sections: {str(e)}")

        # Bottom frame with back button
        bottom_frame = tk.Frame(self.right_frame, height=30, bg="#f5f5f5")
        bottom_frame.pack(fill="x", side="bottom")

    def manage_section(self, course_name, section_name):
        """Manage subjects for a specific section"""
        self.clear_right_frame()
        self.current_course = course_name
        self.current_section = section_name
        
        # Header with back button
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        
        back_btn = tk.Button(header_frame, 
                            text="← Back to Courses", 
                            font=("Arial", 12),
                            bg="#3498db", 
                            fg="white", 
                            command=self.show_records_screen)
        back_btn.pack(side="left", padx=20)

        section_label = tk.Label(header_frame, 
                            text=f"{course_name} > {section_name}", 
                            font=("Helvetica", 16, "bold"), 
                            bg="#4682B4", fg="white")
        section_label.pack(side="left", padx=10)

        # Add Subject Button
        add_subject_btn = tk.Button(self.right_frame, 
                                text="+ Add New Subject",
                                font=("Arial", 12), 
                                bg="#2ecc71", 
                                fg="white",
                                command=lambda: self.add_subject_dialog(course_name, section_name))
        add_subject_btn.pack(pady=10, ipadx=10, ipady=5)

        # Load existing subjects
        self.load_subjects(course_name, section_name)
    
    def add_subject_dialog(self, course_name, section_name):
        """Modern dialog to add new subject"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Subject to {section_name}")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg="#f5f5f5")

        # Header
        header_frame = tk.Frame(dialog, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text=f"Add New Subject",
            font=("Helvetica", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)

        # Content
        content_frame = tk.Frame(dialog, bg="#f5f5f5", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)

        tk.Label(
            content_frame,
            text="Subject Name:",
            font=("Arial", 12),
            bg="#f5f5f5"
        ).pack(anchor="w", pady=(0, 5))

        subject_entry = tk.Entry(
            content_frame,
            font=("Arial", 12),
            width=30
        )
        subject_entry.pack(fill="x", pady=(0, 15))
        subject_entry.focus()

        def save_subject():
            subject_name = subject_entry.get().strip()
            if not subject_name:
                messagebox.showwarning("Warning", "Subject name cannot be empty!")
                return
                
            try:
                self.db.cursor.execute(
                    """INSERT INTO subjects 
                    (name, course_name, section_name, professor_id) 
                    VALUES (?, ?, ?, ?)""",
                    (subject_name, course_name, section_name, self.current_professor)
                )
                self.db.conn.commit()
                self.load_subjects(course_name, section_name)
                dialog.destroy()
                messagebox.showinfo("Success", "Subject added successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to add subject: {str(e)}")

        # Buttons
        btn_frame = tk.Frame(content_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x", pady=(10, 0))

        save_btn = tk.Button(
            btn_frame,
            text="Save Subject",
            font=("Arial", 12),
            bg="#27ae60",
            fg="white",
            bd=0,
            padx=15,
            command=save_subject
        )
        save_btn.pack(side="right", padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            bd=0,
            padx=15,
            command=dialog.destroy
        )
        cancel_btn.pack(side="right")

    def delete_subject(self, course_name, section_name, subject_name):
        """Delete subject with confirmation"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete subject '{subject_name}'?\n"
            f"This will also delete all associated attendance records.",
            icon="warning"
        )
        
        if confirm:
            try:
                # First delete attendance records
                self.db.cursor.execute(
                    """DELETE FROM attendance 
                    WHERE subject_id IN (
                        SELECT id FROM subjects 
                        WHERE name = ? AND course_name = ? AND section_name = ? AND professor_id = ?
                    )""",
                    (subject_name, course_name, section_name, self.current_professor)
                )
                
                # Then delete the subject itself
                self.db.cursor.execute(
                    """DELETE FROM subjects 
                    WHERE name = ? AND course_name = ? AND section_name = ? AND professor_id = ?""",
                    (subject_name, course_name, section_name, self.current_professor)
                )
                
                self.db.conn.commit()
                self.load_subjects(course_name, section_name)
                messagebox.showinfo("Success", "Subject deleted successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete subject: {str(e)}")
                self.db.conn.rollback()
    
    def load_subjects(self, course_name, section_name):
        """Load subjects with consistent UI design matching courses/sections"""
        self.clear_right_frame()
        self.current_course = course_name
        self.current_section = section_name
        
        # Set background color scheme
        self.right_frame.configure(bg="#f5f7fa")
        
        # Header with decorative elements
        header_frame = tk.Frame(
            self.right_frame, 
            bg="#4682B4",
            height=100,
            bd=0,
            highlightthickness=0
        )
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Header canvas for decorative elements
        header_canvas = tk.Canvas(
            header_frame,
            bg="#4682B4",
            height=100,
            bd=0,
            highlightthickness=0
        )
        header_canvas.pack(fill="both", expand=True)
        
        # Add subtle pattern to header
        for i in range(0, 1000, 30):
            header_canvas.create_arc(
                i, 80, i+60, 180,
                start=0, extent=180,
                fill="#3a6ea5", outline=""
            )
        
        # Header content
        header_content = tk.Frame(header_canvas, bg="#4682B4")
        header_canvas.create_window((0,0), window=header_content, anchor="nw")
        
        # Back button
        back_btn = tk.Button(
            header_content,
            text="← Back to Sections",
            font=("Arial", 11, "bold"),
            bg="#3498db",
            fg="white",
            bd=0,
            padx=15,
            pady=5,
            activebackground="#2980b9",
            command=lambda: self.manage_section(course_name, section_name)
        )
        back_btn.pack(side="left", padx=20, pady=10)
        
        # Title with section info
        title_label = tk.Label(
            header_content,
            text=f"{course_name} > {section_name} > Subjects",
            font=("Helvetica", 16, "bold"),
            bg="#4682B4",
            fg="white"
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Main content container
        main_container = tk.Frame(self.right_frame, bg="#f5f7fa")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Decorative left sidebar
        sidebar = tk.Frame(
            main_container,
            bg="#e1e8ed",
            width=50,
            relief="sunken",
            bd=1
        )
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        
        # Add icon in sidebar
        tk.Label(
            sidebar,
            text="📚",
            font=("Arial", 18),
            bg="#e1e8ed",
            fg="#7f8c8d",
            pady=15
        ).pack()
        
        # Content frame with shadow effect
        content_frame = tk.Frame(
            main_container,
            bg="white",
            bd=0,
            highlightthickness=0,
            padx=0,
            pady=0
        )
        content_frame.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=(0, 20))
        
        # Shadow effects
        shadow = tk.Frame(content_frame, bg="#d1d8dd", height=2)
        shadow.pack(fill="x", side="bottom")
        shadow = tk.Frame(content_frame, bg="#e1e8ed", height=2)
        shadow.pack(fill="x", side="bottom")
        
        # Scrollable canvas
        canvas = tk.Canvas(
            content_frame,
            bg="white",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel scrolling
        def on_mouse_wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        
        # Add subject button at top
        add_subject_btn = tk.Button(
            scroll_frame,
            text="+ Add New Subject",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            bd=0,
            padx=15,
            pady=8,
            command=lambda: self.add_subject_dialog(course_name, section_name)
        )
        add_subject_btn.pack(fill="x", padx=20, pady=15)
        
        try:
            # Get subjects from database
            self.db.cursor.execute(
                """SELECT name FROM subjects 
                WHERE course_name = ? AND section_name = ? AND professor_id = ?""",
                (course_name, section_name, self.current_professor)
            )
            subjects = [subject[0] for subject in self.db.cursor.fetchall()]
            
            if subjects:
                # Create grid container
                grid_frame = tk.Frame(scroll_frame, bg="white")
                grid_frame.pack(fill="both", expand=True, padx=15, pady=(0, 20))
                
                # Display subjects in 2-column grid
                for i, subject in enumerate(subjects):
                    # Subject card
                    subject_card = tk.Frame(
                        grid_frame,
                        bg="white",
                        bd=1,
                        relief="solid",
                        highlightthickness=0,
                        padx=15,
                        pady=12
                    )
                    subject_card.grid(
                        row=i//2,
                        column=i%2,
                        padx=10,
                        pady=10,
                        sticky="nsew"
                    )
                    grid_frame.columnconfigure(i%2, weight=1)
                    
                    # Hover effects
                    def on_enter(e, card=subject_card):
                        card.config(bg="#f1f5f9")
                    
                    def on_leave(e, card=subject_card):
                        card.config(bg="white")
                    
                    subject_card.bind("<Enter>", on_enter)
                    subject_card.bind("<Leave>", on_leave)
                    
                    # Subject name (clickable)
                    subject_label = tk.Label(
                        subject_card,
                        text=subject,
                        font=("Arial", 12, "bold"),
                        bg="white",
                        fg="#3498db",
                        anchor="w"
                    )
                    subject_label.pack(fill="x", pady=(0, 10))
                    subject_label.bind(
                        "<Button-1>", 
                        lambda e, s=subject: self.manage_subject(course_name, section_name, s)
                    )
                    
                    # Buttons frame
                    btn_frame = tk.Frame(subject_card, bg="white")
                    btn_frame.pack(fill="x")
                    
                    # View Attendance button
                    view_btn = tk.Button(
                        btn_frame,
                        text="View Attendance →",
                        font=("Arial", 10),
                        bg="#3498db",
                        fg="white",
                        bd=0,
                        padx=10,
                        pady=3,
                        command=lambda s=subject: self.manage_subject(course_name, section_name, s)
                    )
                    view_btn.pack(side="left", padx=(0, 5))
                    
                    # Delete button
                    del_btn = tk.Button(
                        btn_frame,
                        text="Delete",
                        font=("Arial", 10),
                        bg="#e74c3c",
                        fg="white",
                        bd=0,
                        padx=10,
                        pady=3,
                        command=lambda s=subject: self.delete_subject(course_name, section_name, s)
                    )
                    del_btn.pack(side="left")
                    
                    # Make entire card clickable
                    for child in subject_card.winfo_children():
                        child.bind("<Button-1>", lambda e, s=subject: self.manage_subject(course_name, section_name, s))
            else:
                # Empty state design
                empty_frame = tk.Frame(
                scroll_frame,
                bg="#f1f5f9",
                height=150,
                bd=1,
                relief="solid",  # Changed from "dashed" to "solid"
                highlightthickness=0
                )
                empty_frame.pack(fill="x", padx=20, pady=20)
                
                tk.Label(
                    empty_frame,
                    text="📚 No subjects yet",
                    font=("Arial", 14),
                    bg="#f1f5f9",
                    fg="#7f8c8d"
                ).pack(expand=True, pady=10)
                
        
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load subjects: {str(e)}")
        
        # Footer with course/section info
        footer = tk.Frame(
            self.right_frame,
            bg="#e1e8ed",
            height=30,
            bd=0,
            highlightthickness=0
        )
        footer.pack(fill="x", side="bottom", pady=(10, 0))
        
        tk.Label(
            footer,
            text=f"{course_name} • {section_name} • {len(subjects) if 'subjects' in locals() else 0} subjects",
            font=("Arial", 9),
            bg="#e1e8ed",
            fg="#7f8c8d"
        ).pack(side="right", padx=20)

    
    def manage_subject(self, course_name, section_name, subject_name):
        """Navigate to attendance list for the selected subject"""
        self.pack_forget()  # Hide the dashboard frame
        self.parent.show_attendanceList(section_name, subject_name, course_name)
        
        # Header with back button - REMOVED self.pack_forget()
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Back button command now properly manages the navigation
        back_btn = tk.Button(header_frame, 
                            text="← Back to Sections", 
                            font=("Arial", 12),
                            bg="#3498db", 
                            fg="white", 
                            command=lambda: self.show_section_view(course_name, section_name))
        back_btn.pack(side="left", padx=20)

        subject_label = tk.Label(header_frame, 
                            text=f"{course_name} > {section_name} > {subject_name}", 
                            font=("Helvetica", 16, "bold"), 
                            bg="#4682B4", fg="white")
        subject_label.pack(side="left", padx=10)

        # Content frame for subject management
        content_frame = tk.Frame(self.right_frame, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Placeholder for attendance management functionality
        tk.Label(content_frame, 
                text=f"Attendance Management for {subject_name}",
                font=("Arial", 14), 
                bg="#ecf0f1").pack(pady=50)

    def show_section_view(self, course_name, section_name):
        """Helper method to properly show the section view"""
        self.clear_right_frame()
        self.manage_section(course_name, section_name)
    
    # Inside the DashboardFrame class

    def start_attendance(self):
        """Start attendance tracking"""
        if not self.current_course:
            messagebox.showwarning("Warning", "Please select a course first")
            return
            
        if not self.attendance_app:
            self.attendance_app = AttendanceApp(self)
        
        if self.attendance_app.start_attendance():
            messagebox.showinfo("Attendance", "Attendance tracking started")
        else:
            messagebox.showerror("Error", "Failed to start attendance tracking")

    

    def stop_attendance(self):
        """Stop attendance tracking"""
        if self.attendance_app:
            self.attendance_app.stop_attendance()
            messagebox.showinfo("Attendance", "Attendance tracking stopped")
        else:
            messagebox.showwarning("Warning", "No attendance tracking is running")


    def generate_report(self):
        """Generate attendance report"""
        if not self.attendance_app:
            messagebox.showwarning("Warning", "Attendance app not initialized")
            return
            
        success, message = self.attendance_app.generate_report()
        if success:
            messagebox.showinfo("Report Generated", message)
        else:
            messagebox.showerror("Report Error", message)


    def register_fingerprint(self):
        """Register fingerprint for a student"""
        if not self.attendance_app:
            self.attendance_app = AttendanceApp(self.right_frame)
        
        student_id = simpledialog.askstring("Register Fingerprint", "Enter Student ID:")
        if not student_id:
            return
            
        # Check if student exists first
        try:
            self.db.cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            result = self.db.cursor.fetchone()
            
            if result:
                name = result[0]
                email = simpledialog.askstring("Register Fingerprint", "Enter Student Email (optional):")
                success, message = self.attendance_app.enroll_fingerprint(student_id, name, email)
            else:
                name = simpledialog.askstring("Register Fingerprint", "Enter Student Name:")
                if not name:
                    return
                email = simpledialog.askstring("Register Fingerprint", "Enter Student Email (optional):")
                success, message = self.attendance_app.enroll_fingerprint(student_id, name, email)
                
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to check student: {str(e)}")

    def show_schedule_screen(self):
        """Show the schedule management screen with calendar view and schedule editor"""
        self.clear_right_frame()
        self.right_frame.unbind_all("<MouseWheel>")
        
        # Header with gradient background
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 15))
        
        header_canvas = tk.Canvas(header_frame, bg="#4682B4", height=80, highlightthickness=0)
        header_canvas.pack(fill="both", expand=True)
        
        # Create gradient effect
        for i in range(80):
            color = "#{:02x}{:02x}{:02x}".format(
                70 + int(i * 1.5), 
                130 + int(i * 1.2), 
                180 + int(i * 0.8)
            )
            header_canvas.create_line(0, i, 1000, i, fill=color)

        
        tk.Label(header_canvas, 
                text="CLASS SCHEDULE", 
                font=("Helvetica", 20, "bold"), 
                bg="#4682B4", fg="white").place(relx=0.5, rely=0.5, anchor="center")
        
        # Main content container with shadow effect
        main_container = tk.Frame(self.right_frame, bg="#f5f7fa")
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Navigation and control panel
        control_frame = tk.Frame(main_container, bg="#f5f7fa")
        control_frame.pack(fill="x", pady=(0, 15))
        
        # Week navigation
        nav_frame = tk.Frame(control_frame, bg="#f5f7fa")
        nav_frame.pack(side="left")
        
        self.current_week = tk.StringVar(value="Current Week")
        tk.Button(nav_frame, text="◀", font=("Arial", 10), 
                bg="#3498db", fg="white", bd=0,
                command=self.prev_week).pack(side="left", padx=2)
        tk.Label(nav_frame, textvariable=self.current_week, 
                font=("Arial", 12, "bold"), bg="#f5f7fa").pack(side="left", padx=5)
        tk.Button(nav_frame, text="▶", font=("Arial", 10), 
                bg="#3498db", fg="white", bd=0,
                command=self.next_week).pack(side="left", padx=2)
        
        # Add new schedule button
        tk.Button(control_frame, text="+ Add New Schedule", 
                font=("Arial", 12), bg="#27ae60", fg="white",
                command=self.add_schedule_dialog).pack(side="right", padx=5)
        
        # Filter controls
        filter_frame = tk.Frame(control_frame, bg="#f5f7fa")
        filter_frame.pack(side="right", padx=10)
        
        tk.Label(filter_frame, text="Filter:", font=("Arial", 10), bg="#f5f7fa").pack(side="left")
        self.filter_course = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.filter_course.pack(side="left", padx=5)
        self.filter_course.bind("<<ComboboxSelected>>", self.filter_schedules)
        
        # Schedule display area
        schedule_container = tk.Frame(main_container, bg="white", bd=1, relief="solid")
        schedule_container.pack(fill="both", expand=True)
        
        # Create days of week headers
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for i, day in enumerate(days):
            day_header = tk.Frame(schedule_container, bg="#4682B4", height=30)
            day_header.grid(row=0, column=i, sticky="nsew", padx=1, pady=(0, 1))
            tk.Label(day_header, text=day[:3], font=("Arial", 10, "bold"), 
                    bg="#4682B4", fg="white").pack(pady=5)
            schedule_container.columnconfigure(i, weight=1)
        
        # Create time slots
        time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(7, 19)]
        for i, time_slot in enumerate(time_slots):
            time_label = tk.Frame(schedule_container, bg="#f5f7fa", height=40)
            time_label.grid(row=i+1, column=6, sticky="nsew", padx=(1, 0), pady=1)
            tk.Label(time_label, text=time_slot, font=("Arial", 8), 
                    bg="#f5f7fa").pack(side="left", padx=5)
            
            for j in range(6):  # For each day
                cell = tk.Frame(schedule_container, bg="white", bd=1, relief="solid", 
                            height=40, width=100)
                cell.grid(row=i+1, column=j, sticky="nsew", padx=1, pady=1)
                cell.bind("<Button-1>", lambda e, r=i+1, c=j: self.cell_clicked(r, c))
        
        # Load professor's schedules
        self.load_schedules()
        self.load_course_filters()

    def load_course_filters(self):
        """Load courses for filter dropdown"""
        try:
            self.db.cursor.execute(
                "SELECT DISTINCT course_name FROM schedules WHERE professor_id = ?",
                (self.current_professor,)
            )
            courses = ["All Courses"] + [course[0] for course in self.db.cursor.fetchall()]
            self.filter_course["values"] = courses
            if courses:
                self.filter_course.current(0)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load courses: {str(e)}")

    def filter_schedules(self, event=None):
        """Filter schedules based on selected course"""
        course = self.filter_course.get()
        self.load_schedules(course if course != "All Courses" else None)

    def load_schedules(self, course_filter=None):
        """Load schedules from database and display them"""
        try:
            query = """
                SELECT id, course_name, section_name, subject_name, 
                    day, start_time, end_time, room 
                FROM schedules 
                WHERE professor_id = ?
            """
            params = [self.current_professor]
            
            if course_filter:
                query += " AND course_name = ?"
                params.append(course_filter)
            
            self.db.cursor.execute(query, params)
            schedules = self.db.cursor.fetchall()
            
            # Clear existing schedule items
            for child in self.right_frame.winfo_children():
                if hasattr(child, "schedule_id"):
                    child.destroy()
            
            # Display schedules
            for schedule in schedules:
                sched_id, course, section, subject, day, start, end, room = schedule
                self.display_schedule_item(sched_id, course, section, subject, 
                                        day, start, end, room)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load schedules: {str(e)}")

    def display_schedule_item(self, sched_id, course, section, subject, day, start, end, room):
        """Display a schedule item on the calendar"""
        try:
            # Convert day to column index (0=Monday, 5=Saturday)
            day_index = ["Monday", "Tuesday", "Wednesday", 
                        "Thursday", "Friday", "Saturday"].index(day)
            
            # Convert time to row index (7:00 = row 1, 8:00 = row 2, etc.)
            start_hour = int(start.split(":")[0])
            row_index = start_hour - 6  # 7:00 is row 1
            
            # Calculate duration in rows (1 hour = 1 row)
            end_hour = int(end.split(":")[0])
            row_span = end_hour - start_hour
            
            # Create schedule item frame
            item_frame = tk.Frame(self.right_frame, bg="#e3f2fd", bd=1, relief="solid")
            item_frame.place(
                relx=0.21 + day_index*0.132, 
                rely=0.25 + (row_index-1)*0.035, 
                relwidth=0.13, 
                relheight=0.035*row_span,
                anchor="nw"
            )
            item_frame.schedule_id = sched_id
            
            # Display schedule info
            tk.Label(item_frame, 
                    text=f"{subject}\nSec: {section}\nRm: {room}", 
                    font=("Arial", 8), 
                    bg="#e3f2fd", 
                    justify="left").pack(padx=2, pady=2)
            
            # Add context menu
            item_frame.bind("<Button-3>", lambda e, id=sched_id: self.show_schedule_context_menu(e, id))
        except Exception as e:
            print(f"Error displaying schedule: {e}")

    def show_schedule_context_menu(self, event, schedule_id):
        """Show context menu for schedule item"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.edit_schedule(schedule_id))
        menu.add_command(label="Delete", command=lambda: self.delete_schedule(schedule_id))
        menu.add_separator()
        menu.add_command(label="Send Reminder", 
                        command=lambda: self.send_schedule_reminder(schedule_id))
        menu.post(event.x_root, event.y_root)

    def add_schedule_dialog(self):
        """Modern dialog to add new schedule"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Schedule")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Header
        header_frame = tk.Frame(dialog, bg="#4682B4", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, 
                text="Add New Class Schedule", 
                font=("Helvetica", 14, "bold"), 
                bg="#4682B4", fg="white").pack(pady=15)
        
        # Content
        content_frame = tk.Frame(dialog, padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Form fields
        fields = [
            ("Course:", "course", self.get_professor_courses()),
            ("Section:", "section", []),
            ("Subject:", "subject", []),
            ("Day:", "day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
            ("Start Time:", "start_time", [f"{h:02d}:00" for h in range(7, 19)]),
            ("End Time:", "end_time", [f"{h:02d}:00" for h in range(8, 20)]),
            ("Room:", "room", ["Room 101", "Room 102", "Room 201", "Room 202", "Online"])
        ]
        
        self.schedule_entries = {}
        
        for i, (label, name, options) in enumerate(fields):
            tk.Label(content_frame, text=label, font=("Arial", 10)).grid(row=i, column=0, sticky="e", pady=5)
            
            if options:
                var = tk.StringVar()
                cb = ttk.Combobox(content_frame, textvariable=var, values=options, state="readonly")
                cb.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                self.schedule_entries[name] = var
                
                # Store the combobox widgets for section and subject
                if name == "section":
                    self.section_combobox = cb  # Initialize section_combobox here
                elif name == "subject":
                    self.subject_combobox = cb  # Initialize subject_combobox here
                
                # Load sections when course is selected
                if name == "course":
                    var.trace("w", lambda *args: self.load_sections_for_course(
                        var.get(), self.schedule_entries["section"]))
                
                # Load subjects when section is selected
                if name == "section":
                    var.trace("w", lambda *args: self.load_subjects_for_section(
                        self.schedule_entries["course"].get(), 
                        var.get(), 
                        self.schedule_entries["subject"]))
            else:
                var = tk.StringVar()
                entry = tk.Entry(content_frame, textvariable=var, font=("Arial", 10))
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                self.schedule_entries[name] = var
        
        # Buttons
        button_frame = tk.Frame(content_frame)
        button_frame.grid(row=len(fields)+1, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="Save", font=("Arial", 10), bg="#27ae60", fg="white",
                command=lambda: self.save_schedule(dialog)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", font=("Arial", 10), bg="#e74c3c", fg="white",
                command=dialog.destroy).pack(side="left", padx=5)

    def get_professor_courses(self):
        """Get list of courses taught by professor"""
        try:
            self.db.cursor.execute(
                "SELECT DISTINCT course_name FROM sections WHERE professor_id = ?",
                (self.current_professor,)
            )
            return [course[0] for course in self.db.cursor.fetchall()]
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load courses: {str(e)}")
            return []
    
    def load_sections_for_course(self, course, section_var):
        """Load sections for selected course"""
        try:
            self.db.cursor.execute(
                "SELECT name FROM sections WHERE course_name = ? AND professor_id = ?",
                (course, self.current_professor)
            )
            sections = [section[0] for section in self.db.cursor.fetchall()]
            section_var.set("")
            self.section_combobox['values'] = sections  # Update the combobox directly
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load sections: {str(e)}")

    def load_subjects_for_section(self, course, section, subject_var):
        """Load subjects for selected section"""
        try:
            self.db.cursor.execute(
                """SELECT name FROM subjects 
                WHERE course_name = ? AND section_name = ? AND professor_id = ?""",
                (course, section, self.current_professor)
            )
            subjects = [subject[0] for subject in self.db.cursor.fetchall()]
            subject_var.set("")
            self.subject_combobox['values'] = subjects  # Update the combobox directly
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load subjects: {str(e)}")

    def save_schedule(self, dialog):
        """Save new schedule to database"""
        try:
            data = {name: var.get() if isinstance(var, tk.StringVar) else var.get("1.0", "end-1c") 
                for name, var in self.schedule_entries.items()}
            
            # Validate data
            if not all(data.values()):
                messagebox.showwarning("Warning", "Please fill in all fields")
                return
                
            # Check if end time is after start time
            start = datetime.datetime.strptime(data["start_time"], "%H:%M")
            end = datetime.datetime.strptime(data["end_time"], "%H:%M")
            if end <= start:
                messagebox.showwarning("Warning", "End time must be after start time")
                return
                
            # Save to database
            self.db.cursor.execute(
                """INSERT INTO schedules 
                (professor_id, course_name, section_name, subject_name, 
                day, start_time, end_time, room) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.current_professor, data["course"], data["section"], 
                data["subject"], data["day"], data["start_time"], 
                data["end_time"], data["room"])
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Schedule saved successfully")
            dialog.destroy()
            self.load_schedules()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save schedule: {str(e)}")

    def edit_schedule(self, schedule_id):
        """Edit existing schedule"""
        try:
            self.db.cursor.execute(
                "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
            )
            schedule = self.db.cursor.fetchone()
            
            if not schedule:
                messagebox.showerror("Error", "Schedule not found")
                return
                
            dialog = tk.Toplevel(self)
            dialog.title("Edit Schedule")
            dialog.geometry("500x400")
            dialog.grab_set()
            
            # Header
            header_frame = tk.Frame(dialog, bg="#4682B4", height=60)
            header_frame.pack(fill="x")
            
            tk.Label(header_frame, 
                    text="Edit Class Schedule", 
                    font=("Helvetica", 14, "bold"), 
                    bg="#4682B4", fg="white").pack(pady=15)
            
            # Content
            content_frame = tk.Frame(dialog, padx=20, pady=20)
            content_frame.pack(fill="both", expand=True)
            
            # Form fields with current values
            fields = [
                ("Course:", "course", schedule[2], False),
                ("Section:", "section", schedule[3], False),
                ("Subject:", "subject", schedule[4], False),
                ("Day:", "day", schedule[5], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
                ("Start Time:", "start_time", schedule[6], [f"{h:02d}:00" for h in range(7, 19)]),
                ("End Time:", "end_time", schedule[7], [f"{h:02d}:00" for h in range(8, 20)]),
                ("Room:", "room", schedule[8], ["Room 101", "Room 102", "Room 201", "Room 202", "Online"])
            ]
            
            self.schedule_entries = {}
            
            for i, (label, name, value, options) in enumerate(fields):
                tk.Label(content_frame, text=label, font=("Arial", 10)).grid(row=i, column=0, sticky="e", pady=5)
                
                if options:
                    var = tk.StringVar(value=value)
                    cb = ttk.Combobox(content_frame, textvariable=var, values=options, state="readonly")
                    cb.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                    self.schedule_entries[name] = var
                else:
                    entry = tk.Entry(content_frame, font=("Arial", 10))
                    entry.insert(0, value)
                    entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                    self.schedule_entries[name] = entry
            
            # Buttons
            button_frame = tk.Frame(content_frame)
            button_frame.grid(row=len(fields)+1, columnspan=2, pady=10)
            
            tk.Button(button_frame, text="Update", font=("Arial", 10), bg="#27ae60", fg="white",
                    command=lambda: self.update_schedule(dialog, schedule_id)).pack(side="left", padx=5)
            tk.Button(button_frame, text="Cancel", font=("Arial", 10), bg="#e74c3c", fg="white",
                    command=dialog.destroy).pack(side="left", padx=5)
        
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to edit schedule: {str(e)}")

    def update_schedule(self, dialog, schedule_id):
        """Update schedule in database"""
        try:
            data = {name: var.get() if isinstance(var, tk.StringVar) else var.get("1.0", "end-1c") 
                for name, var in self.schedule_entries.items()}
            
            # Validate data
            if not all(data.values()):
                messagebox.showwarning("Warning", "Please fill in all fields")
                return
                
            # Check if end time is after start time
            start = datetime.datetime.strptime(data["start_time"], "%H:%M")
            end = datetime.datetime.strptime(data["end_time"], "%H:%M")
            if end <= start:
                messagebox.showwarning("Warning", "End time must be after start time")
                return
                
            # Update database
            self.db.cursor.execute(
                """UPDATE schedules SET 
                course_name = ?, section_name = ?, subject_name = ?,
                day = ?, start_time = ?, end_time = ?, room = ?
                WHERE id = ?""",
                (data["course"], data["section"], data["subject"], 
                data["day"], data["start_time"], data["end_time"], 
                data["room"], schedule_id)
            )
            self.db.conn.commit()
            messagebox.showinfo("Success", "Schedule updated successfully")
            dialog.destroy()
            self.load_schedules()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update schedule: {str(e)}")

    def delete_schedule(self, schedule_id):
        """Delete schedule with confirmation"""
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            "Are you sure you want to delete this schedule?",
            icon="warning"
        )
        if confirm:
            try:
                self.db.cursor.execute(
                    "DELETE FROM schedules WHERE id = ?", (schedule_id,)
                )
                self.db.conn.commit()
                messagebox.showinfo("Success", "Schedule deleted successfully")
                self.load_schedules()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete schedule: {str(e)}")

    def send_schedule_reminder(self, schedule_id):
        """Send email reminder for this schedule"""
        try:
            self.db.cursor.execute(
                "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
            )
            schedule = self.db.cursor.fetchone()
            
            if not schedule:
                messagebox.showerror("Error", "Schedule not found")
                return
                
            # Get students in this section
            self.db.cursor.execute(
                """SELECT email FROM students 
                WHERE student_id IN (
                    SELECT student_id FROM professor_students 
                    WHERE professor_id = ? AND section_name = ?
                )""",
                (self.current_professor, schedule[3])
            )
            recipients = [row[0] for row in self.db.cursor.fetchall()]
            
            if not recipients:
                messagebox.showwarning("Warning", "No students found in this section")
                return
                
            subject = f"Reminder: {schedule[4]} Class"
            body = f"""This is a reminder for your {schedule[4]} class:
            
    Course: {schedule[2]}
    Section: {schedule[3]}
    Day: {schedule[5]}
    Time: {schedule[6]} - {schedule[7]}
    Room: {schedule[8]}

    Please be on time!"""
            
            success = self.email_handler.send_bulk_email_reminder(recipients, subject, body)
            if success:
                messagebox.showinfo("Success", f"Reminder sent to {len(recipients)} students")
            else:
                messagebox.showerror("Error", "Failed to send reminders")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to send reminders: {str(e)}")

    def prev_week(self):
        """Navigate to previous week"""
        # Implement week navigation logic
        pass

    def next_week(self):
        """Navigate to next week"""
        # Implement week navigation logic
        pass

    def cell_clicked(self, row, col):
        """Handle click on schedule cell"""
        # Could be used for quick schedule addition
        pass

    def show_account_screen(self):
        """Show the account management screen"""
        self.clear_right_frame()
        self.right_frame.unbind_all("<MouseWheel>")
        
        # Header
        header_frame = tk.Frame(self.right_frame, bg="#4682B4", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        
        account_label = tk.Label(header_frame, text="ACCOUNT", 
                              font=("Helvetica", 20, "bold"), bg="#4682B4", fg="white")
        account_label.pack(pady=20)

        # Content frame
        content_frame = tk.Frame(self.right_frame, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Get professor details from database
        try:
            self.db.cursor.execute(
                "SELECT name, email FROM professors WHERE id = ?",
                (self.current_professor,)
            )
            professor_data = self.db.cursor.fetchone()
            
            if professor_data:
                name, email = professor_data
                
                # Display account information
                info_frame = tk.Frame(content_frame, bg="#ecf0f1")
                info_frame.pack(pady=20)
                
                tk.Label(info_frame, text="Name:", font=("Arial", 12, "bold"), 
                        bg="#ecf0f1").grid(row=0, column=0, sticky="e", padx=5, pady=5)
                tk.Label(info_frame, text=name, font=("Arial", 12), 
                        bg="#ecf0f1").grid(row=0, column=1, sticky="w", padx=5, pady=5)
                
                tk.Label(info_frame, text="Email:", font=("Arial", 12, "bold"), 
                        bg="#ecf0f1").grid(row=1, column=0, sticky="e", padx=5, pady=5)
                tk.Label(info_frame, text=email, font=("Arial", 12), 
                        bg="#ecf0f1").grid(row=1, column=1, sticky="w", padx=5, pady=5)
                
                # Change password button
                change_pass_btn = tk.Button(content_frame, text="Change Password", 
                                         font=("Arial", 12), bg="#3498db", fg="white",
                                         command=self.change_password_dialog)
                change_pass_btn.pack(pady=20, ipadx=10, ipady=5)
            else:
                tk.Label(content_frame, text="Account information not found.",
                       font=("Arial", 12), bg="#ecf0f1").pack(pady=50)
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load account information: {str(e)}")
            tk.Label(content_frame, text="Error loading account information.",
                   font=("Arial", 12), bg="#ecf0f1").pack(pady=50)

    def change_password_dialog(self):
        """Dialog to change password"""
        dialog = tk.Toplevel(self)
        dialog.title("Change Password")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Current Password:", font=("Arial", 12)).pack(pady=5)
        current_pass_entry = tk.Entry(dialog, font=("Arial", 12), width=30, show="*")
        current_pass_entry.pack(pady=5)

        tk.Label(dialog, text="New Password:", font=("Arial", 12)).pack(pady=5)
        new_pass_entry = tk.Entry(dialog, font=("Arial", 12), width=30, show="*")
        new_pass_entry.pack(pady=5)

        tk.Label(dialog, text="Confirm New Password:", font=("Arial", 12)).pack(pady=5)
        confirm_pass_entry = tk.Entry(dialog, font=("Arial", 12), width=30, show="*")
        confirm_pass_entry.pack(pady=5)

        def save_password():
            current_pass = current_pass_entry.get()
            new_pass = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            
            if not current_pass or not new_pass or not confirm_pass:
                messagebox.showwarning("Warning", "All fields are required!")
                return
                
            if new_pass != confirm_pass:
                messagebox.showerror("Error", "New passwords do not match!")
                return
                
            if new_pass == current_pass:
                messagebox.showerror("Error", "New password must be different from current password!")
                return
                
            # Verify current password and update in database
            try:
                self.db.cursor.execute(
                    "SELECT password FROM professors WHERE id = ?",
                    (self.current_professor,)
                )
                result = self.db.cursor.fetchone()
                
                if result and result[0] == current_pass:  # In real app, use hashed passwords
                    self.db.cursor.execute(
                        "UPDATE professors SET password = ? WHERE id = ?",
                        (new_pass, self.current_professor)
                    )
                    self.db.conn.commit()
                    messagebox.showinfo("Success", "Password changed successfully!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Current password is incorrect!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to change password: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        save_btn = tk.Button(button_frame, text="Save", font=("Arial", 12),
                           bg="#2ecc71", fg="white", command=save_password)
        save_btn.pack(side="left", padx=10)

        cancel_btn = tk.Button(button_frame, text="Cancel", font=("Arial", 12),
                             bg="#e74c3c", fg="white", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=10)

    def clear_right_frame(self):
        """Clear all widgets from the right frame"""
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def send_email_reminder(self, recipient, subject, body):
        """Send email reminder to single recipient"""
        success = self.email_handler.send_email_reminder(recipient, subject, body)
        if success:
            messagebox.showinfo("Success", f"Email sent to {recipient}")
        else:
            messagebox.showerror("Error", "Failed to send email.")

    def send_bulk_email_reminder(self, recipients, subject, body):
        """Send email reminder to multiple recipients"""
        success = self.email_handler.send_bulk_email_reminder(recipients, subject, body)
        if success:
            messagebox.showinfo("Success", f"Emails sent to {len(recipients)} recipients.")
        else:
            messagebox.showerror("Error", "Failed to send bulk emails.")
