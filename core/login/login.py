# login
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QAbstractButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt
from PySide6.QtGui import QPixmap, QGuiApplication

sys.path.append("/home/rapa/git/pipeline/api_scripts")
from shotgun_api import ShotgunApi


class Login(QWidget):

    def __init__(self):
        super().__init__()

        self.sg_cls = ShotgunApi()

        self.make_ui()
        self.ui.pushButton.clicked.connect(self.get_login_info)
        self.ui.lineEdit_pw.returnPressed.connect(self.get_login_info)
        self.count = 0

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/login.ui"
        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Moomins")

        img_path = "/home/rapa/git/pipeline/sourceimages/moomins.png"
        pixmap = QPixmap(img_path)
        scaled_pixmap = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.label_img.setPixmap(scaled_pixmap)
        self.make_ui_center()

    def make_ui_center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_login_info(self):
        input_id = self.ui.lineEdit_id.text()
        input_pw = self.ui.lineEdit_pw.text()

        if (not input_id and not input_pw or
                not input_id and input_pw or
                input_id and not input_pw):

            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                return QMessageBox.about(self, "Error", f"Enter your ID and Password\n"
                                                        f" {self.count}times.\n"
                                                        f"Login is restricted after 5 login attempts.")

        if self.count >= 5:
            QMessageBox.about(self, "Error", f"Incorrect {self.count}times.\n"
                                             f"The program exits due to an excessive number of login attempts.")
            self.timeout_popup()
            win.close()
        else:
            # Pass the id,pw in shotgrid
            self.get_shotgrid_email(input_id, input_pw)

    def get_shotgrid_email(self, input_id, input_pw):
        # If shotgrid Info correct Input Info => get_dept
        # Access password to id  (Issue & redeem Autodesk tokens, Make Legacy Login PW)
        # a = shotgun.Shotgun(URL, input_id, input_pw) # API calls reflect the user's permissions as they are
        # user = a.authenticate_human_user(input_id, input_pw)
        # => Check the user's credentials and return user information if the user is valid
        user = self.sg_cls.get_shotgrid_email(input_id, input_pw)

        # if have not Info in shotgrid
        if not user:
            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                return QMessageBox.about(self, "Error", f"Unregistered user!\n"
                                                        f"Incorrect {self.count}times.\n"
                                                        f"Login is restricted after 5 login attempts.")

        if self.count >= 5:
            QMessageBox.about(self, "Error", f"Incorrect {self.count}times.\n"
                                             f"The program exits due to an excessive number of login attempts.")
            self.timeout_popup()
            win.close()

        shotgrid_email = user["login"]
        shotgrid_id = user["id"]

        if shotgrid_email == input_id:
            datas = self.sg_cls.get_dept(shotgrid_id)
            user_dept = datas["department"]["name"]
            self.ui.label_timeout.setText(f"Complete! {user_dept} Loader 접속 중입니다!")
            self.get_dept(shotgrid_id)

    def timeout_popup(self):
        self.popup = QDialog(self)
        self.popup.setWindowTitle("Timer")
        self.popup.setGeometry(200, 100, 200, 100)

        # Set timer
        self.remaining_time = 0.1 * 60  # 3min
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        # Show time in popupDialog
        self.timer_label = QLabel(f"Time left: {self.remaining_time}sec", self.popup)
        layout = QVBoxLayout(self.popup)
        layout.addWidget(self.timer_label)

        self.popup.setModal(True)
        self.popup.show()

        # Disable close Button
        self.find_close_button()

        # Update the timer every 1 second
        self.timer.start(1000)

        self.popup.exec()

    def find_close_button(self):
        # find a close button and Disable the Button
        # Qt Dialog close Button is basically QAbstractButton.
        for btn in self.popup.findChildren(QAbstractButton):
            if btn.text() == "X":
                self.close_button = btn
                self.close_button.setEnabled(False)
                break

    def closeEvent(self, event):
        # If not finished timer, ignore close Button.
        if self.remaining_time > 0:
            event.ignore()
        else:
            super().closeEvent(event)

    def update_time(self):
        self.remaining_time -= 1
        self.timer_label.setText(f"Time left : {self.remaining_time}sec")

        if self.remaining_time <= 0:
            self.timer.stop()
            if hasattr(self, 'close_button'):
                self.close_button.setEnabled(True)
            self.ui.label_timeout.setText("Login access restrictions have been lifted.\n"
                                          "Please Try login again.")

    def get_dept(self, shotgrid_id):
        # get name, dept info
        datas = self.sg_cls.get_dept(shotgrid_id)

        user_name = datas["name"]
        user_dept = datas["department"]["name"]
        user_id = datas["id"]

        self.open_loader(user_name, user_dept, user_id)

    def open_loader(self, user_name, user_dept, user_id):
        # Open loaders By Dept

        if user_dept == "Asset":
            print(f"Asset Tasks. {user_name}, Open Assetloader... ")
            from moomins.core.asset_maya.scripts.loader import asset_loader
            global asset_window
            asset_window = asset_loader.AssetLoader(user_id)
            asset_window.show()
            win.close()

        if user_dept == "Shot":
            print(f"Shot Tasks. {user_name}, Open Shotloader... ")
            from loader import shot_loader
            global shot_window
            shot_window = shot_loader.ShotLoader(user_id)
            shot_window.show()
            win.close()

        os.environ["USER_ID"] = user_id


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Login()
    win.show()
    app.exec()