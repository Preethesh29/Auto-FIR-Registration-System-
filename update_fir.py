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
    switch_to_records = QtCore.pyqtSignal(str)

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

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        self.navbar = Navbar()
        self.navbar.switch_to_home.connect(self.switch_to_home.emit)
        self.navbar.switch_to_records.connect(lambda: self.switch_to_records.emit(self.fir_type))
        self.navbar.switch_to_login.connect(lambda: self.switch_to_login.emit("admin"))
        self.main_layout.addWidget(self.navbar)

        self.title_label = QtWidgets.QLabel(f"{self.fir_type} FIR Records")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(85, 98, 112, 255);")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        self.records_table = QtWidgets.QTableWidget()
        self.records_table.setColumnCount(6)
        self.records_table.setHorizontalHeaderLabels(["FIR Details", "Victim's Name", "Victim's Address", "Incident Date", "Case Stage", "Email"])
        self.records_table.horizontalHeader().setStretchLastSection(True)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setStyleSheet("font-size: 16px; color: rgba(85, 98, 112, 255);")
        self.main_layout.addWidget(self.records_table)

        buttons_layout = QtWidgets.QHBoxLayout()

        save_button = QtWidgets.QPushButton("Save Changes")
        save_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                  "color: white;\n"
                                  "font-size: 16px;\n"
                                  "padding: 10px 20px;\n"
                                  "border-radius: 10px;")
        save_button.clicked.connect(self.save_changes)
        buttons_layout.addWidget(save_button)

        back_button = QtWidgets.QPushButton("Back to Home")
        back_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                  "color: white;\n"
                                  "font-size: 16px;\n"
                                  "padding: 10px 20px;\n"
                                  "border-radius: 10px;")
        back_button.clicked.connect(self.switch_to_home.emit)
        back_button.setMaximumWidth(150)
        buttons_layout.addWidget(back_button)

        export_button = QtWidgets.QPushButton("Export to CSV")
        export_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                    "color: white;\n"
                                    "font-size: 16px;\n"
                                    "padding: 10px 20px;\n"
                                    "border-radius: 10px;")
        export_button.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(export_button)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(buttons_layout)
        buttons_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(buttons_container, alignment=QtCore.Qt.AlignCenter)

        self.display_records()

    def display_records(self):
        self.records_table.setRowCount(0)

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
                email = self.records_table.item(row, 5).text()

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
                    csvwriter.writerow(["FIR Details", "Victim's Name", "Victim's Address", "Email"])
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
        self.setWindowTitle(f"Register {fir_type} FIR")
        self.setGeometry(300, 200, 400, 450)
        self.setupUi()

    def setupUi(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.label_fir_details = QtWidgets.QLabel("FIR Details")
        self.main_layout.addWidget(self.label_fir_details)
        self.text_edit_fir_details = QtWidgets.QTextEdit()
        self.main_layout.addWidget(self.text_edit_fir_details)

        self.label_victim_name = QtWidgets.QLabel("Victim's Name")
        self.main_layout.addWidget(self.label_victim_name)
        self.line_edit_victim_name = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.line_edit_victim_name)

        self.label_victim_address = QtWidgets.QLabel("Victim's Address")
        self.main_layout.addWidget(self.label_victim_address)
        self.line_edit_victim_address = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.line_edit_victim_address)

        self.label_incident_date = QtWidgets.QLabel("Incident Date (YYYY-MM-DD)")
        self.main_layout.addWidget(self.label_incident_date)
        self.line_edit_incident_date = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.line_edit_incident_date)

        self.label_case_stage = QtWidgets.QLabel("Case Stage")
        self.main_layout.addWidget(self.label_case_stage)
        self.line_edit_case_stage = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.line_edit_case_stage)

        self.label_email = QtWidgets.QLabel("Email")
        self.main_layout.addWidget(self.label_email)
        self.line_edit_email = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.line_edit_email)

        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.button_register = QtWidgets.QPushButton("Register")
        self.button_register.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                           "color: white;\n"
                                           "font-size: 16px;\n"
                                           "padding: 10px 20px;\n"
                                           "border-radius: 10px;")
        self.button_register.clicked.connect(self.register_fir)
        self.buttons_layout.addWidget(self.button_register)

        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_cancel.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                         "color: white;\n"
                                         "font-size: 16px;\n"
                                         "padding: 10px 20px;\n"
                                         "border-radius: 10px;")
        self.button_cancel.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.button_cancel)

        self.main_layout.addLayout(self.buttons_layout)

    def register_fir(self):
        fir_details = self.text_edit_fir_details.toPlainText()
        victim_name = self.line_edit_victim_name.text()
        victim_address = self.line_edit_victim_address.text()
        incident_date = self.line_edit_incident_date.text()
        case_stage = self.line_edit_case_stage.text()
        email = self.line_edit_email.text()

        try:
            cursor = db.cursor()
            cursor.execute("INSERT INTO fir_records (type, details, victim_name, victim_address, incident_date, case_stage, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (self.fir_type, fir_details, victim_name, victim_address, incident_date, case_stage, email))
            db.commit()

            self.send_email_notification(email, fir_details)

            self.fir_registered.emit()
            QtWidgets.QMessageBox.information(self, "Success", "FIR registered successfully.")
            self.accept()
        except sqlite3.Error as e:
            print("Error registering FIR:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while registering the FIR.")

    def send_email_notification(self, email, fir_details):
        try:
            sender_email = "your_email@example.com"
            sender_password = "your_password"
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = "FIR Registration Notification"
            message.attach(MIMEText(f"Your FIR has been registered successfully.\n\nFIR Details:\n{fir_details}", "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            server.quit()
        except Exception as e:
            print("Error sending email:", e)
            QtWidgets.QMessageBox.critical(self, "Error", "An error occurred while sending the email notification.")

class HomePage(QtWidgets.QWidget):
    switch_to_login = QtCore.pyqtSignal()
    switch_to_records = QtCore.pyqtSignal(str)
    switch_to_register_fir = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(HomePage, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("HomePage")
        self.resize(800, 700)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        self.navbar = Navbar()
        self.navbar.switch_to_login.connect(self.switch_to_login.emit)
        self.main_layout.addWidget(self.navbar)

        self.title_label = QtWidgets.QLabel("Home Page")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(85, 98, 112, 255);")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        buttons_layout = QtWidgets.QHBoxLayout()

        murder_button = QtWidgets.QPushButton("Murder FIRs")
        murder_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                    "color: white;\n"
                                    "font-size: 16px;\n"
                                    "padding: 10px 20px;\n"
                                    "border-radius: 10px;")
        murder_button.clicked.connect(lambda: self.switch_to_records.emit("Murder"))
        buttons_layout.addWidget(murder_button)

        robbery_button = QtWidgets.QPushButton("Robbery FIRs")
        robbery_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                     "color: white;\n"
                                     "font-size: 16px;\n"
                                     "padding: 10px 20px;\n"
                                     "border-radius: 10px;")
        robbery_button.clicked.connect(lambda: self.switch_to_records.emit("Robbery"))
        buttons_layout.addWidget(robbery_button)

        theft_button = QtWidgets.QPushButton("Theft FIRs")
        theft_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                   "color: white;\n"
                                   "font-size: 16px;\n"
                                   "padding: 10px 20px;\n"
                                   "border-radius: 10px;")
        theft_button.clicked.connect(lambda: self.switch_to_records.emit("Theft"))
        buttons_layout.addWidget(theft_button)

        register_fir_button = QtWidgets.QPushButton("Register New FIR")
        register_fir_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                          "color: white;\n"
                                          "font-size: 16px;\n"
                                          "padding: 10px 20px;\n"
                                          "border-radius: 10px;")
        register_fir_button.clicked.connect(lambda: self.switch_to_register_fir.emit("New"))
        buttons_layout.addWidget(register_fir_button)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(buttons_layout)
        buttons_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(buttons_container, alignment=QtCore.Qt.AlignCenter)

class LoginPage(QtWidgets.QWidget):
    switch_to_home = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(LoginPage, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("LoginPage")
        self.resize(800, 600)

        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(100, 100, 600, 400))
        self.widget.setObjectName("widget")
        self.widget.setStyleSheet("background-color: rgba(255, 255, 255, 255);"
                                  "border-radius: 10px;")

        self.label_username = QtWidgets.QLabel(self.widget)
        self.label_username.setGeometry(QtCore.QRect(100, 100, 80, 40))
        self.label_username.setStyleSheet("color: rgba(85, 98, 112, 255);\n"
                                          "font-size: 16px;")
        self.label_username.setText("Username:")
        self.label_username.setObjectName("label_username")

        self.lineEdit_username = QtWidgets.QLineEdit(self.widget)
        self.lineEdit_username.setGeometry(QtCore.QRect(200, 100, 300, 40))
        self.lineEdit_username.setStyleSheet("background-color: rgba(239, 239, 239, 255);\n"
                                             "padding: 10px;\n"
                                             "border-radius: 10px;")
        self.lineEdit_username.setObjectName("lineEdit_username")

        self.label_password = QtWidgets.QLabel(self.widget)
        self.label_password.setGeometry(QtCore.QRect(100, 180, 80, 40))
        self.label_password.setStyleSheet("color: rgba(85, 98, 112, 255);\n"
                                          "font-size: 16px;")
        self.label_password.setText("Password:")
        self.label_password.setObjectName("label_password")

        self.lineEdit_password = QtWidgets.QLineEdit(self.widget)
        self.lineEdit_password.setGeometry(QtCore.QRect(200, 180, 300, 40))
        self.lineEdit_password.setStyleSheet("background-color: rgba(239, 239, 239, 255);\n"
                                             "padding: 10px;\n"
                                             "border-radius: 10px;")
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")

        self.login_button = QtWidgets.QPushButton(self.widget)
        self.login_button.setGeometry(QtCore.QRect(200, 260, 150, 50))
        self.login_button.setStyleSheet("background-color: rgba(11, 131, 120, 219);\n"
                                        "color: white;\n"
                                        "font-size: 16px;\n"
                                        "padding: 10px 20px;\n"
                                        "border-radius: 10px;")
        self.login_button.setText("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.validate_login)

    def validate_login(self):
        username = self.lineEdit_username.text()
        password = self.lineEdit_password.text()

        if username == "admin" and password == "admin123":
            QtWidgets.QMessageBox.information(self, "Success", "Login successful.")
            self.switch_to_home.emit()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid username or password.")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.login_page = LoginPage()
        self.home_page = HomePage()
        self.setCentralWidget(self.login_page)

        self.login_page.switch_to_home.connect(self.show_home_page)
        self.home_page.switch_to_login.connect(self.show_login_page)
        self.home_page.switch_to_records.connect(self.show_records_page)
        self.home_page.switch_to_register_fir.connect(self.show_register_fir_dialog)

    def show_home_page(self):
        self.setCentralWidget(self.home_page)

    def show_login_page(self):
        self.setCentralWidget(self.login_page)

    def show_records_page(self, fir_type):
        self.records_page = RecordsPage(fir_type)
        self.records_page.switch_to_home.connect(self.show_home_page)
        self.records_page.switch_to_login.connect(self.show_login_page)
        self.records_page.switch_to_records.connect(self.show_records_page)
        self.setCentralWidget(self.records_page)

    def show_register_fir_dialog(self, fir_type):
        self.register_fir_dialog = RegisterFIRDialog(fir_type)
        self.register_fir_dialog.fir_registered.connect(lambda: self.show_records_page(fir_type))
        self.register_fir_dialog.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Connect to the database
    db = sqlite3.connect("firs.db")
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS fir_records (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, details TEXT, victim_name TEXT, victim_address TEXT, incident_date TEXT, case_stage TEXT, email TEXT)")
    db.commit()

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())
