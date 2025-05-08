# widgets/fingerprint_scanner.py
import tkinter as tk
from tkinter import messagebox

class FingerprintScanner:
    def __init__(self, parent):
        self.parent = parent
        self.fingerprint_status = tk.Label(
            parent,
            text="Fingerprint Status: Not Scanned",
            font=("Arial", 10),
            fg="red",
            bg="white"
        )
        self.fingerprint_status.pack(pady=10)

        self.scan_btn = tk.Button(
            parent,
            text="Scan Fingerprint",
            font=("Arial", 12),
            bg="blue",
            fg="white",
            command=self.scan_fingerprint
        )
        self.scan_btn.pack(pady=5)

    def scan_fingerprint(self):
        self.fingerprint_status.config(text="Fingerprint Status: Scanning...", fg="blue")
        self.fingerprint_status.after(2000, self._scan_success)

    def _scan_success(self):
        self.fingerprint_status.config(text="Fingerprint Status: Scanned Successfully", fg="green")
        messagebox.showinfo("Success", "Fingerprint scanned successfully!")
