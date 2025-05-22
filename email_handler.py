# email_handler.py
import smtplib
import ssl
import datetime

class EmailHandler:
    def __init__(self, sender_email, sender_password):
        self.GMAIL_SENDER = "bio.hunters10@gmail.com"
        self.GMAIL_PASSWORD = "ljab fqkc ptdf qwzk" 

    def send_email_reminder(self, recipient, subject, body):
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.GMAIL_SENDER, self.GMAIL_PASSWORD)
                msg = f"Subject: {subject}\nFrom: {self.GMAIL_SENDER}\nTo: {recipient}\n\n{body}"
                server.sendmail(self.GMAIL_SENDER, recipient, msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_bulk_email_reminder(self, recipients, subject, body):
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.GMAIL_SENDER, self.GMAIL_PASSWORD)
                for recipient in recipients:
                    msg = f"Subject: {subject}\nFrom: {self.GMAIL_SENDER}\nTo: {recipient}\n\n{body}"
                    server.sendmail(self.GMAIL_SENDER, recipient, msg)
            return True
        except Exception as e:
            print(f"Failed to send bulk email: {e}")
            return False

