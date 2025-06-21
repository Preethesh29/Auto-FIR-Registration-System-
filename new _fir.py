import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
import geocoder
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import cv2
import pytesseract
import logging
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



# Global database connection
db = None

class Navbar(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()
    switch_to_view_log = QtCore.pyqtSignal()
    switch_to_login = QtCore.pyqtSignal()
    switch_to_records = QtCore.pyqtSignal()

    def __init__(self):
        super(Navbar, self).__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("Navbar")
        self.setStyleSheet("""
            background-color: qlineargradient(
                x1: 0, y1: 0, 
                x2: 1, y2: 0, 
                stop: 0 #4c669f, stop: 0.5 #3b5998, stop: 1 #192f6a
            );
        """)
        self.setMinimumHeight(50)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(20)

        # Home button
        self.home_button = QtWidgets.QPushButton("Home")
        self.home_button.setFixedSize(100, 35)
        self.home_button.setStyleSheet(self.button_style())
        self.home_button.clicked.connect(self.switch_to_home.emit)
        layout.addWidget(self.home_button)

        # View Log button
        self.view_log_button = QtWidgets.QPushButton("View Log")
        self.view_log_button.setFixedSize(100, 35)
        self.view_log_button.setStyleSheet(self.button_style())
        self.view_log_button.clicked.connect(self.switch_to_view_log.emit)
        layout.addWidget(self.view_log_button)

        # Add a spacer to push the buttons to the left
        layout.addStretch()

        # Logout button
        self.logout_button = QtWidgets.QPushButton("Logout")
        self.logout_button.setFixedSize(100, 35)
        self.logout_button.setStyleSheet(self.button_style())
        self.logout_button.clicked.connect(self.switch_to_login.emit)
        layout.addWidget(self.logout_button)

    def button_style(self):
        return """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.8);
            color: #333;
            border: 1px solid #333;
            padding: 5px 15px;
            border-radius: 18px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.9);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 1.0);
        }
        """
class ViewLogTimePage(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()
    def __init__(self):
        super(ViewLogTimePage, self).__init__()
        self.layout = QtWidgets.QVBoxLayout(self)

        self.log_times_table = QtWidgets.QTableWidget(self)
        self.log_times_table.setColumnCount(2)
        self.log_times_table.setHorizontalHeaderLabels(["Timestamp", "Event"])
        self.layout.addWidget(self.log_times_table)
        
        
        self.back_to_home_button = QtWidgets.QPushButton("Back to Home")
        self.back_to_home_button.clicked.connect(self.on_back_to_home)
        self.layout.addWidget(self.back_to_home_button)

        
        
    def load_log_times(self):
        # Clear the existing rows
        self.log_times_table.setRowCount(0)
        
        # Load the log times from the log file
        try:
            with open('app.log', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    timestamp, event = self.parse_log_line(line)
                    self.add_log_time_to_table(timestamp, event)
        except Exception as e:
            print("Error loading log times:", e)

    def parse_log_line(self, line):
        # Assuming the log format is "timestamp - event"
        parts = line.strip().split(" - ")
        if len(parts) == 2:
            return parts[0], parts[1]
        return "", ""

    def add_log_time_to_table(self, timestamp, event):
        row_position = self.log_times_table.rowCount()
        self.log_times_table.insertRow(row_position)
        self.log_times_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(timestamp))
        self.log_times_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(event))
    def on_back_to_home(self):
        self.switch_to_home.emit()






        
    
class RecordsPage(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()
    switch_to_login = QtCore.pyqtSignal(str)
    switch_to_records = QtCore.pyqtSignal(str)  # Signal to switch to different FIR pages

    def __init__(self, fir_type, parent=None):
        super(RecordsPage, self).__init__(parent)
        self.fir_type = fir_type
        self.logged_in = False  # Add a logged-in state
        self.setupUi()
        self.dialog = RegisterFIRDialog(self.fir_type)
        self.dialog.fir_registered.connect(self.display_updated_records)

    def display_updated_records(self):
        self.display_records()

    def setupUi(self):
        self.setObjectName("RecordsPage")
        self.resize(800, 700)

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        # Navbar
        self.navbar = Navbar()
        self.navbar.switch_to_home.connect(self.switch_to_home.emit)
        self.navbar.switch_to_records.connect(lambda: self.switch_to_records.emit(self.fir_type))
        self.navbar.switch_to_login.connect(lambda: self.switch_to_login.emit("admin"))
        self.main_layout.addWidget(self.navbar)

        # Title label
        self.title_label = QtWidgets.QLabel(f"{self.fir_type} FIR Records")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(85, 98, 112, 255);")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        # Search layout
        search_layout = QtWidgets.QHBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        # self.search_bar.setPlaceholderText("Search cases...")
        self.search_bar.setStyleSheet("font-size: 16px; padding: 10px;")
        # search_button = QtWidgets.QPushButton("Search")
        # search_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
        #                             "color: white;\n"
        #                             "font-size: 16px;\n"
        #                             "padding: 10px 20px;\n"
        #                             "border-radius: 10px;")
        # search_button.clicked.connect(self.search_records)
        # search_layout.addWidget(self.search_bar)
        # search_layout.addWidget(search_button)
        # self.main_layout.addLayout(search_layout)

        # Table for displaying records
        self.records_table = QtWidgets.QTableWidget()
        self.records_table.setColumnCount(7)  # Adjusted for the email field and "Generate PDF" button
        self.records_table.setHorizontalHeaderLabels(["Number Plate", "Victim's Name", "Victim Address", "Incident Date", "Case Stage", "Email", "Actions"])  # Updated headers
        self.records_table.horizontalHeader().setStretchLastSection(True)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setStyleSheet("font-size: 16px; color: rgba(85, 98, 112, 255);")
        self.main_layout.addWidget(self.records_table)

        # Horizontal layout for buttons
        buttons_layout = QtWidgets.QHBoxLayout()

        # Save changes button
        save_button = QtWidgets.QPushButton("Save Changes")
        save_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                  "color: white;\n"
                                  "font-size: 16px;\n"
                                  "padding: 10px 20px;\n"
                                  "border-radius: 10px;")
        save_button.clicked.connect(self.save_changes)
        buttons_layout.addWidget(save_button)

        # Back to home button
        back_button = QtWidgets.QPushButton("Back to Home")
        back_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                  "color: white;\n"
                                  "font-size: 16px;\n"
                                  "padding: 10px 20px;\n"
                                  "border-radius: 10px;")
        back_button.clicked.connect(self.switch_to_home.emit)
        back_button.setMaximumWidth(150)
        buttons_layout.addWidget(back_button)

        # Export to CSV button
        export_button = QtWidgets.QPushButton("Export to CSV")
        export_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                    "color: white;\n"
                                    "font-size: 16px;\n"
                                    "padding: 10px 20px;\n"
                                    "border-radius: 10px;")
        export_button.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(export_button)

        # Center the buttons layout
        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(buttons_layout)
        buttons_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(buttons_container, alignment=QtCore.Qt.AlignCenter)

        # Fetch and display records initially (comment this out if you don't want to display records before login)
        # self.display_records()

    def display_records(self, search_query=None):
        # Clear current records
        self.records_table.setRowCount(0)  # Clear existing rows

        try:
            cursor = db.cursor()
            cursor.execute("SELECT details, victim_name, victim_address, incident_date, case_stage,  email FROM fir_records WHERE type=?", (self.fir_type,))
            records = cursor.fetchall()

            self.records_table.setRowCount(len(records))

            for row_num, record in enumerate(records):
                for col_num, data in enumerate(record):
                    item = QtWidgets.QTableWidgetItem(str(data))
                    self.records_table.setItem(row_num, col_num, item)

                # Generate PDF button in the "Actions" column
                generate_pdf_button = QtWidgets.QPushButton("Generate PDF")
                generate_pdf_button.clicked.connect(lambda _, rec=record: self.generate_record_pdf(rec))
                self.records_table.setCellWidget(row_num, 6, generate_pdf_button)  # Set in the "Actions" column

        except sqlite3.Error as e:
            print(f"Error loading {self.fir_type} records from database: {e}")

    

    

    def save_changes(self):
        try:
            cursor = db.cursor()
            for row in range(self.records_table.rowCount()):
                fir_id = self.records_table.item(row, 0).text()
                fir_details = self.records_table.item(row, 0).text()
                victim_name = self.records_table.item(row, 1).text()
                victim_address = self.records_table.item(row, 2).text()
                incident_date = self.records_table.item(row, 3).text()
                case_stage = self.records_table.item(row, 4).text()
                email = self.records_table.item(row, 5).text()  # Added email field

                cursor.execute("UPDATE fir_records SET details=?, victim_name=?, victim_address=?, incident_date=?, case_stage=?, email=? WHERE id=?",
                               (fir_details, victim_name, victim_address, incident_date, case_stage, email, fir_id))

                # Send update email if needed
                self.send_update_email(fir_id, victim_name, victim_address, incident_date, case_stage, email)

            db.commit()
            QtWidgets.QMessageBox.information(self, "Success", "Records updated successfully.")
        except sqlite3.Error as e:
            print(f"Error updating records: {e}")
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while updating the records.")

    def send_update_email(self, details, victim_name, victim_address, incident_date, case_stage, email):
        try:
            sender_email = "rishald1410@gmail.com"
            sender_password = "eiwx yxyu xqci eyaz"

            subject = f"Updated FIR Details (ID: {details})"
            body = f"""
            The details of FIR ID {details} have been updated.

            FIR Details: {details}
            Victim's Name: {victim_name}
            Victim's Address: {victim_address}
            Incident Date: {incident_date}
            Case Stage: {case_stage}
            """

            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()

            print(f"Email sent to {email} with updated FIR details.")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def generate_record_pdf(self, record):
        try:
            pdf_filename = f"{record[1]}_FIR_{record[0]}.pdf"
            pdf_path = os.path.join(os.path.expanduser('~'), "Documents", pdf_filename)

            c = canvas.Canvas(pdf_path, pagesize=letter)

            text_content = f"""
            {record[0]} FIR Details

            FIR Details: {record[0]}
            Number Plate: {record[1]}
            Victim's Name: {record[2]}
            Victim's Address: {record[3]}
            Incident Date: {record[4]}
            Case Stage: {record[5]}
            """

            lines = text_content.splitlines()
            y = 750
            for line in lines:
                c.drawString(100, y, line.strip())
                y -= 20

            c.save()
            print(f"PDF generated for {record[1]} FIR {record[0]} at {pdf_path}")
        except Exception as e:
            print("Error generating PDF:", e)

    def export_to_csv(self):
        try:
            cursor = db.cursor()
            cursor.execute("SELECT details, victim_name, victim_address, email FROM fir_records WHERE type = ?", (self.fir_type,))
            rows = cursor.fetchall()

            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save to CSV", f"{self.fir_type}_records.csv", "CSV Files (*.csv)")

            if file_name:
                with open(file_name, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(["FIR Details", "Victim's Name", "Victim's Address", "Email"])
                    csvwriter.writerows(rows)

                QtWidgets.QMessageBox.information(self, "Success", f"Records exported to {file_name} successfully.")
        except sqlite3.Error as e:
            print("Error exporting records:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while exporting the records.")







class RegisterFIRDialog(QtWidgets.QDialog):
    fir_registered = QtCore.pyqtSignal()  # Signal for FIR registration success

    def __init__(self, fir_type, parent=None):
        super(RegisterFIRDialog, self).__init__(parent)
        self.fir_type = fir_type
        self.setWindowTitle(f"Register {fir_type} FIR")
        self.setGeometry(300, 200, 500, 600)  # Adjusted size for additional fields
        self.setStyleSheet("background-color: #f0f0f0;")  # Set background color

        self.setupUi()

    def setupUi(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        self.title_label = QtWidgets.QLabel(f"Register {self.fir_type} FIR")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        self.lineedit_fir_details = QtWidgets.QLineEdit()
        self.lineedit_fir_details.setPlaceholderText(f" {self.fir_type} Number Plate")
        self.lineedit_fir_details.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_fir_details)

        self.lineedit_victim_name = QtWidgets.QLineEdit()
        self.lineedit_victim_name.setPlaceholderText("Victim's Name")
        self.lineedit_victim_name.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_victim_name)

        self.lineedit_victim_address = QtWidgets.QLineEdit()
        self.lineedit_victim_address.setPlaceholderText("Victim's Address")
        self.lineedit_victim_address.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_victim_address)

        self.lineedit_other_details = QtWidgets.QLineEdit()
        self.lineedit_other_details.setPlaceholderText("Other Details")
        self.lineedit_other_details.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_other_details)

        self.lineedit_user_email = QtWidgets.QLineEdit()
        self.lineedit_user_email.setPlaceholderText("Your Email Address")
        self.lineedit_user_email.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_user_email)

        self.lineedit_incident_date = QtWidgets.QDateEdit()
        self.lineedit_incident_date.setCalendarPopup(True)
        self.lineedit_incident_date.setDate(QtCore.QDate.currentDate())
        self.lineedit_incident_date.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_incident_date)

        self.lineedit_case_stage = QtWidgets.QLineEdit()
        self.lineedit_case_stage.setPlaceholderText("Case Stage")
        self.lineedit_case_stage.setStyleSheet("font-size: 14px; padding: 8px;")
        self.main_layout.addWidget(self.lineedit_case_stage)

        self.location_label = QtWidgets.QLabel("Location: ")
        self.location_label.setStyleSheet("font-size: 14px; color: #555;")
        self.main_layout.addWidget(self.location_label)

        self.upload_button = QtWidgets.QPushButton("Upload Number Plate Image")
        self.upload_button.setStyleSheet("font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;")
        self.upload_button.clicked.connect(self.upload_image)
        self.main_layout.addWidget(self.upload_button)

        self.number_plate_label = QtWidgets.QLabel()
        self.number_plate_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.number_plate_label)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)

        self.fetch_geolocation()

    def fetch_geolocation(self):
        try:
            # Use geocoder library to get location based on IP address
            g = geocoder.ip('me')
            if g.ok:
                location = f"{g.city}, {g.state}, {g.country}"
                self.location_label.setText(f"Location: {location}")
        except Exception as e:
            print("Error fetching geolocation:", e)

    
    def send_email(self, fir_details, victim_name, victim_address, other_details, user_email):
        try:
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = "rishald1410@gmail.com"
            smtp_password = "eiwx yxyu xqci eyaz"  # Replace with your actual password

            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = user_email
            msg['Subject'] = f"New {self.fir_type} FIR Registered"

            body = (f"FIR Details: {fir_details}\n"
                    f"Victim's Name: {victim_name}\n"
                    f"Victim's Address: {victim_address}\n"
                    f"Other Details: {other_details}")
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, user_email, msg.as_string())
            server.quit()

            print("Email sent successfully")
        except Exception as e:
            print("Error sending email:", e)

    def upload_image(self):
        file_dialog = QtWidgets.QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, "Select Number Plate Image", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)")

        if image_path:
            number_plate = self.read_number_plate(image_path)
            self.number_plate_label.setText(f"Number Plate: {number_plate}")
            self.lineedit_fir_details.setText(number_plate)

    def read_number_plate(self, image_path):
        try:
            # Load image using OpenCV
            image = cv2.imread(image_path)

            if image is None:
                raise ValueError(f"Image at path {image_path} could not be loaded.")

            # Convert image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply thresholding or other preprocessing if needed
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Perform OCR using Tesseract
            number_plate_text = pytesseract.image_to_string(thresh, config='--psm 6')

            return number_plate_text.strip()
        except Exception as e:
            print(f"Error reading number plate: {e}")
            return ""

    def accept(self):
        fir_details = self.lineedit_fir_details.text()
        victim_name = self.lineedit_victim_name.text()
        victim_address = self.lineedit_victim_address.text()
        other_details = self.lineedit_other_details.text()
        user_email = self.lineedit_user_email.text()
        incident_date = self.lineedit_incident_date.date().toString(QtCore.Qt.ISODate)
        case_stage = self.lineedit_case_stage.text()

        if not self.validate_email(user_email):
            QtWidgets.QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return

        try:
            
            cursor = db.cursor()
            cursor.execute("INSERT INTO fir_records (type, details, victim_name, victim_address, other_details, incident_date, case_stage,email) "
                           "VALUES (?, ?, ?, ?, ?,?, ?,?)",
                           (self.fir_type, fir_details, victim_name, victim_address, other_details, incident_date, case_stage, user_email))
            db.commit()
            print("FIR Details inserted successfully")
            self.send_email(fir_details, victim_name, victim_address, other_details, user_email)
            self.fir_registered.emit()  # Emit signal upon successful insertion
            super().accept()
        except sqlite3.Error as e:
            print("Error inserting FIR details:", e)

        super().accept()

    def validate_email(self, email):
        import re
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None



class HomePage(QtWidgets.QWidget):
    switch_to_login = QtCore.pyqtSignal()
    switch_to_records = QtCore.pyqtSignal(str)  # Signal to switch to different FIR pages
    switch_to_register_fir = QtCore.pyqtSignal(str)  # Signal to switch to register FIR page
    switch_to_view_log_time = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(HomePage, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("HomePage")
        self.resize(800, 700)

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)  # Adjust spacing between widgets

        # Navbar
        self.navbar = Navbar()
        self.navbar.switch_to_home.connect(self.show_home)
        self.navbar.switch_to_records.connect(self.switch_to_records.emit)
        self.navbar.switch_to_view_log.connect(self.switch_to_view_log_time.emit)
        self.navbar.switch_to_login.connect(self.switch_to_login.emit)
        self.main_layout.addWidget(self.navbar)

        # Content layout
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(20)

        # Title label
        title_label = QtWidgets.QLabel("Welcome to FIR Management System")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.content_layout.addWidget(title_label)

        # Create three FIR cards as buttons
        self.card_murder = self.create_card("Murder FIR", "File FIR for murder cases", "#FF6347")
        self.card_suicide = self.create_card("Suicide FIR", "File FIR for suicide cases", "#4682B4")
        self.card_accident = self.create_card("Accident FIR", "File FIR for accident cases", "#228B22")

        # Add cards to layout
        self.content_layout.addWidget(self.card_murder)
        self.content_layout.addWidget(self.card_suicide)
        self.content_layout.addWidget(self.card_accident)

        self.main_layout.addLayout(self.content_layout)

    def create_card(self, title, description, color):
        card = QtWidgets.QWidget()
        card.setObjectName("FIRCard")
        card.setStyleSheet(f"background-color: {color}; border-radius: 10px; border: 1px solid #ccc;")
        card.setMinimumHeight(200)  # Adjust minimum height for longer cards
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        card_layout.addWidget(title_label)

        desc_label = QtWidgets.QLabel(description)
        desc_label.setStyleSheet("font-size: 14px; color: white;")
        card_layout.addWidget(desc_label)

        button_layout = QtWidgets.QHBoxLayout()
        view_button = QtWidgets.QPushButton("View Records")
        view_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.8); color: black; padding: 8px 16px; border-radius: 10px;")
        view_button.clicked.connect(lambda: self.switch_to_records.emit(title.split()[0]))
        button_layout.addWidget(view_button)

        register_button = QtWidgets.QPushButton("Register FIR")
        register_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.8); color: black; padding: 8px 16px; border-radius: 10px;")
        register_button.clicked.connect(lambda: self.switch_to_register_fir.emit(title.split()[0]))
        button_layout.addWidget(register_button)

        card_layout.addLayout(button_layout)
        return card

    def show_home(self):
        self.switch_to_home.emit()




class LoginPage(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()  # Signal to switch to home page

    def __init__(self, parent=None):
        super(LoginPage, self).__init__(parent)
        self.setupUi(self)
        self.center()

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(800, 700)
        Form.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        Form.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.widget = QtWidgets.QWidget(Form)
        self.widget.setGeometry(QtCore.QRect(40, 40, 720, 620))
        self.widget.setStyleSheet("background-color: rgba(255, 255, 255, 200);\n"
                                  "border-radius: 20px;")
        self.widget.setObjectName("widget")
        
        self.label_background = QtWidgets.QLabel(self.widget)
        self.label_background.setGeometry(QtCore.QRect(0, 0, 360, 620))
        self.label_background.setStyleSheet("border-top-left-radius: 20px; "
                                            "border-bottom-left-radius: 20px; "
                                            "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, "
                                            "stop:0 rgba(11, 131, 120, 219), stop:1 rgba(85, 98, 112, 226));")
        self.label_background.setObjectName("label_background")
        
        self.label_logo = QtWidgets.QLabel(self.widget)
        self.label_logo.setGeometry(QtCore.QRect(40, 120, 280, 280))
        self.label_logo.setStyleSheet("background-color: rgba(255, 255, 255, 150);\n"
                                      "border-radius: 20px;")
        self.label_logo.setObjectName("label_logo")
        
        self.label_text = QtWidgets.QLabel(self.label_logo)
        self.label_text.setGeometry(QtCore.QRect(10, 10, 260, 260))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.label_text.setFont(font)
        self.label_text.setStyleSheet("color: rgba(85, 98, 112, 255);")
        self.label_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_text.setText("Auto\nFIR\nRegister")
        self.label_text.setObjectName("label_text")

        self.label_login = QtWidgets.QLabel(self.widget)
        self.label_login.setGeometry(QtCore.QRect(380, 50, 300, 50))
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.label_login.setFont(font)
        self.label_login.setStyleSheet("color: rgba(85, 98, 112, 255);")
        self.label_login.setText("Login")
        self.label_login.setObjectName("label_login")
        
        self.lineEdit_username = QtWidgets.QLineEdit(self.widget)
        self.lineEdit_username.setGeometry(QtCore.QRect(380, 150, 300, 40))
        self.lineEdit_username.setStyleSheet("background-color: rgba(255, 255, 255, 255);\n"
                                             "border-radius: 10px;\n"
                                             "padding-left: 10px;")
        self.lineEdit_username.setPlaceholderText("Username")
        self.lineEdit_username.setObjectName("lineEdit_username")
        
        self.lineEdit_password = QtWidgets.QLineEdit(self.widget)
        self.lineEdit_password.setGeometry(QtCore.QRect(380, 220, 300, 40))
        self.lineEdit_password.setStyleSheet("background-color: rgba(255, 255, 255, 255);\n"
                                             "border-radius: 10px;\n"
                                             "padding-left: 10px;")
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_password.setPlaceholderText("Password")
        self.lineEdit_password.setObjectName("lineEdit_password")
        
        self.pushButton_login = QtWidgets.QPushButton(self.widget)
        self.pushButton_login.setGeometry(QtCore.QRect(380, 300, 300, 50))
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.pushButton_login.setFont(font)
        self.pushButton_login.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, "
                                            "stop:0 rgba(11, 131, 120, 219), stop:1 rgba(85, 98, 112, 226));\n"
                                            "color: white;\n"
                                            "border-radius: 15px;")  # Increased border-radius
        self.pushButton_login.setText("Login")
        self.pushButton_login.setObjectName("pushButton_login")
        self.pushButton_login.clicked.connect(self.handle_login)
        
        self.label_forgot = QtWidgets.QLabel(self.widget)
        self.label_forgot.setGeometry(QtCore.QRect(380, 370, 300, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_forgot.setFont(font)
        self.label_forgot.setStyleSheet("color: rgba(85, 98, 112, 255);")
        self.label_forgot.setAlignment(QtCore.Qt.AlignCenter)
        # self.label_forgot.setText("Forgot your username or password?")
        self.label_forgot.setObjectName("label_forgot")
        
        self.label_register = QtWidgets.QLabel(self.widget)
        self.label_register.setGeometry(QtCore.QRect(380, 400, 300, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_register.setFont(font)
        self.label_register.setStyleSheet("color: rgba(85, 98, 112, 255);")
        self.label_register.setAlignment(QtCore.Qt.AlignCenter)
        # self.label_register.setText("New user? Register here.")
        self.label_register.setObjectName("label_register")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Login Form"))

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def handle_login(self):
        # Placeholder login check; replace with actual authentication logic
        if self.lineEdit_username.text() == "user" and self.lineEdit_password.text() == "pass":
            self.switch_to_home.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.stack = QtWidgets.QStackedWidget()
        
        self.login_page = LoginPage()
        self.home_page = HomePage()
        self.records_page_murder = RecordsPage("Murder")
        self.records_page_suicide = RecordsPage("Suicide")
        self.records_page_accident = RecordsPage("Accident")
        self.view_log_time_page = ViewLogTimePage()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.records_page_murder)
        self.stack.addWidget(self.records_page_suicide)
        self.stack.addWidget(self.records_page_accident)
        self.stack.addWidget(self.view_log_time_page)

        self.login_page.switch_to_home.connect(self.show_home_page)
        self.home_page.switch_to_login.connect(self.show_login_page)
        self.home_page.switch_to_records.connect(self.show_records_page)
        self.home_page.switch_to_register_fir.connect(self.show_register_fir_dialog)
        self.home_page.switch_to_view_log_time.connect(self.show_view_log_time_page)
        self.view_log_time_page.switch_to_home.connect(self.show_home_page)

        self.records_page_murder.switch_to_home.connect(self.show_home_page)
        self.records_page_suicide.switch_to_home.connect(self.show_home_page)
        self.records_page_accident.switch_to_home.connect(self.show_home_page)

        self.init_ui()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.stack)

        self.setCentralWidget(central_widget)

    def show_login_page(self):
        self.stack.setCurrentWidget(self.login_page)

    def show_home_page(self):
        self.stack.setCurrentWidget(self.home_page)

    def show_records_page(self, fir_type):
        if fir_type == "Murder":
            self.stack.setCurrentWidget(self.records_page_murder)
            self.records_page_murder.display_records()
        elif fir_type == "Suicide":
            self.stack.setCurrentWidget(self.records_page_suicide)
            self.records_page_suicide.display_records()
        elif fir_type == "Accident":
            self.stack.setCurrentWidget(self.records_page_accident)
            self.records_page_accident.display_records()

    def show_register_fir_dialog(self, fir_type):
        dialog = RegisterFIRDialog(fir_type)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            print("FIR registered successfully")
            self.show_records_page(fir_type)

    def show_view_log_time_page(self):
        self.view_log_time_page.load_log_times()
        self.stack.setCurrentWidget(self.view_log_time_page)




def create_connection():
    global db
    try:
        db = sqlite3.connect("fiirrsss_database.db")
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fir_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                details TEXT,
                victim_name TEXT,
                victim_address TEXT,
                other_details TEXT,
                incident_date TEXT, 
                case_stage TEXT,
                email Text,
                timestamp TEXT
                
                 
            )
        """)
        db.commit()
        print("Database connection and table creation successful")
    except sqlite3.Error as e:
        print("Error creating database connection:", e)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    create_connection()
    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    window = MainWindow()
    window.setWindowTitle("FIR Management System")
    window.show()
    sys.exit(app.exec_())
 