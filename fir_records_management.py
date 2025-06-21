import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
import geocoder

# Global database connection
db = None

class Navbar(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()
    switch_to_records = QtCore.pyqtSignal(str)
    switch_to_login = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Navbar, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        layout = QtWidgets.QHBoxLayout(self)
        
        home_button = QtWidgets.QPushButton("Home")
        home_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                  "color: white;\n"
                                  "font-size: 16px;\n"
                                  "padding: 10px 20px;\n"
                                  "border-radius: 10px;")
        home_button.clicked.connect(self.switch_to_home.emit)
        layout.addWidget(home_button)

        logout_button = QtWidgets.QPushButton("Logout")
        logout_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                    "color: white;\n"
                                    "font-size: 16px;\n"
                                    "padding: 10px 20px;\n"
                                    "border-radius: 10px;")
        logout_button.clicked.connect(self.switch_to_login.emit)
        layout.addWidget(logout_button)

class RecordsPage(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()
    switch_to_login = QtCore.pyqtSignal(str)
    switch_to_records = QtCore.pyqtSignal(str)  # Signal to switch to different FIR pages

    def __init__(self, fir_type, parent=None):
        super(RecordsPage, self).__init__(parent)
        self.fir_type = fir_type
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

        # Table for displaying records
        self.records_table = QtWidgets.QTableWidget()
        self.records_table.setColumnCount(6)  # Adjusted for the email field
        self.records_table.setHorizontalHeaderLabels(["FIR Details", "Victim's Name", "Victim's Address", "Incident Date", "Case Stage", "Email"])  # Updated headers
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

        # Fetch and display records initially
        self.display_records()

    def display_records(self):
        # Clear current records
        self.records_table.setRowCount(0)

        # Fetch FIR records from database and display them
        try:
            cursor = db.cursor()
            cursor.execute("SELECT id, details, victim_name, victim_address, incident_date, case_stage, email FROM fir_records WHERE type = ?", (self.fir_type,))
            rows = cursor.fetchall()
            self.records_table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                fir_id, fir_details, victim_name, victim_address, incident_date, case_stage, email = row
                self.records_table.setItem(row_index, 0, QtWidgets.QTableWidgetItem(fir_details))
                self.records_table.setItem(row_index, 1, QtWidgets.QTableWidgetItem(victim_name))
                self.records_table.setItem(row_index, 2, QtWidgets.QTableWidgetItem(victim_address))
                self.records_table.setItem(row_index, 3, QtWidgets.QTableWidgetItem(incident_date))
                self.records_table.setItem(row_index, 4, QtWidgets.QTableWidgetItem(case_stage))
                self.records_table.setItem(row_index, 5, QtWidgets.QTableWidgetItem(email))

                # Store FIR id in the row's data to identify it later
                self.records_table.setVerticalHeaderItem(row_index, QtWidgets.QTableWidgetItem(str(fir_id)))

        except sqlite3.Error as e:
            print("Error fetching records:", e)

    def save_changes(self):
        try:
            cursor = db.cursor()
            for row in range(self.records_table.rowCount()):
                fir_id = int(self.records_table.verticalHeaderItem(row).text())
                fir_details = self.records_table.item(row, 0).text()
                victim_name = self.records_table.item(row, 1).text()
                victim_address = self.records_table.item(row, 2).text()
                incident_date = self.records_table.item(row, 3).text()
                case_stage = self.records_table.item(row, 4).text()
                email = self.records_table.item(row, 5).text()  # Added email field

                cursor.execute("UPDATE fir_records SET details = ?, victim_name = ?, victim_address = ?, incident_date = ?, case_stage = ?, email = ? WHERE id = ?",
                               (fir_details, victim_name, victim_address, incident_date, case_stage, email, fir_id))
            db.commit()
            QtWidgets.QMessageBox.information(self, "Success", "Records updated successfully.")
        except sqlite3.Error as e:
            print("Error updating records:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while updating the records.")

    def export_to_csv(self):
        try:
            cursor = db.cursor()
            cursor.execute("SELECT details, victim_name, victim_address, email FROM fir_records WHERE type = ?", (self.fir_type,))
            rows = cursor.fetchall()

            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save to CSV", f"{self.fir_type}_records.csv", "CSV Files (*.csv)")

            if file_name:
                with open(file_name, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    # Write header
                    csvwriter.writerow(["FIR Details", "Victim's Name", "Victim's Address", "Email"])  # Updated headers
                    # Write rows
                    csvwriter.writerows(rows)

                QtWidgets.QMessageBox.information(self, "Success", f"Records exported to {file_name} successfully.")
        except sqlite3.Error as e:
            print("Error exporting records:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while exporting the records.")

class RegisterFIRDialog(QtWidgets.QDialog):
    fir_registered = QtCore.pyqtSignal()

    def __init__(self, fir_type, parent=None):
        super(RegisterFIRDialog, self).__init__(parent)
        self.fir_type = fir_type
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Register FIR")
        self.resize(400, 600)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("Register FIR")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.form_layout = QtWidgets.QFormLayout()
        self.fir_details = QtWidgets.QLineEdit()
        self.victim_name = QtWidgets.QLineEdit()
        self.victim_address = QtWidgets.QLineEdit()
        self.incident_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.incident_date.setDate(QtCore.QDate.currentDate())
        self.case_stage = QtWidgets.QLineEdit()
        self.email = QtWidgets.QLineEdit()  # Added email field
        self.form_layout.addRow("FIR Details:", self.fir_details)
        self.form_layout.addRow("Victim's Name:", self.victim_name)
        self.form_layout.addRow("Victim's Address:", self.victim_address)
        self.form_layout.addRow("Incident Date:", self.incident_date)
        self.form_layout.addRow("Case Stage:", self.case_stage)
        self.form_layout.addRow("Email:", self.email)  # Added email field
        self.layout.addLayout(self.form_layout)

        self.submit_button = QtWidgets.QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_fir)
        self.layout.addWidget(self.submit_button)

    def submit_fir(self):
        fir_details = self.fir_details.text()
        victim_name = self.victim_name.text()
        victim_address = self.victim_address.text()
        incident_date = self.incident_date.date().toString("yyyy-MM-dd")
        case_stage = self.case_stage.text()
        email = self.email.text()  # Added email field

        try:
            cursor = db.cursor()
            cursor.execute("INSERT INTO fir_records (type, details, victim_name, victim_address, incident_date, case_stage, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (self.fir_type, fir_details, victim_name, victim_address, incident_date, case_stage, email))
            db.commit()

            self.fir_registered.emit()
            QtWidgets.QMessageBox.information(self, "Success", "FIR registered successfully.")
            self.close()
        except sqlite3.Error as e:
            print("Error registering FIR:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while registering the FIR.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Connect to SQLite database
    db = sqlite3.connect("database.db")

    # Setup database table if not exists
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fir_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        details TEXT,
        victim_name TEXT,
        victim_address TEXT,
        incident_date TEXT,
        case_stage TEXT,
        email TEXT  -- Added email field
    )
    """)
    db.commit()

    fir_type = "Criminal"  # Example FIR type
    records_page = RecordsPage(fir_type)
    records_page.show()
    sys.exit(app.exec_())
