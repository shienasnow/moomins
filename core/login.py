# login
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QAbstractButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt
from PySide6.QtGui import QPixmap,QGuiApplication
sys.path.append("/home/rapa/git/pipeline/api_scripts")


from shotgun_api import ShotgunApi

# sys.path.append("/home/rapa/python-api")

# URL = "https://4thacademy.shotgrid.autodesk.com"
# SCRIPT_NAME = "moomins_key"
# API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"



class Login(QWidget):

    def __init__(self):
        super().__init__()

        self.sg_cls = ShotgunApi()

        self.make_ui()
        self.ui.pushButton.clicked.connect(self.get_login_info) # 버튼으로 실행
        self.ui.lineEdit_pw.returnPressed.connect(self.get_login_info) # 엔터로 실행
        self.count = 0 # 5번 틀리면 강제 종료되고, 시간 지나서 실행 가능하도록

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/login.ui"
        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Moomins")

        img_path = "/home/rapa/git/pipeline/sourceimages/moomins.png"
        pixmap = QPixmap(img_path)
        scaled_pixmap = pixmap.scaled(160, 160,  Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.label_img.setPixmap(scaled_pixmap)
        self.make_ui_center()
        
    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def get_login_info(self): # 사용자가 입력한 로그인 정보 가져와서 get_shotgrid_email로 보내기
        input_id = self.ui.lineEdit_id.text()
        input_pw = self.ui.lineEdit_pw.text()

        if input_id == "" and input_pw != "":
            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                QMessageBox.about(self, "경고", f"ID를 입력하세요\n로그인 시도 {self.count}회입니다.\n로그인 시도 5회 이상 시 로그인이 제한됩니다.")

        if input_pw == "" and input_id != "":
            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                QMessageBox.about(self, "경고", f"패스워드를 입력하세요\n로그인 시도 {self.count}회입니다.\n로그인 시도 5회 이상 시 로그인이 제한됩니다.")

        if input_id == "" and input_pw == "":
            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                QMessageBox.about(self, "경고", f"ID와 패스워드를 입력하세요\n로그인 시도 {self.count}회입니다.\n로그인 시도 5회 이상 시 로그인이 제한됩니다.")

        if self.count >= 5:
            QMessageBox.about(self, "경고", f"로그인 시도 {self.count}회입니다.\n로그인 시도 횟수 초과로 프로그램이 종료됩니다.")
            self.timeout_popup()
            win.close()
        else:
            self.get_shotgrid_email(input_id, input_pw) # 입력 받은 id, pw 전달

    def get_shotgrid_email(self, input_id, input_pw): # shotgrid 정보랑 입력한 정보가 같을 때 get_dept
        # 패스워드로 id에 접근하는 방식 (오토데스크 토큰을 발급&등록, Legacy Login PW 생성 필요)
        # a = shotgun.Shotgun(URL, input_id, input_pw) # 사용자의 권한을 그대로 반영하여 API 호출
        # user = a.authenticate_human_user(input_id, input_pw) # 사용자의 자격 증명을 확인해서 유효한 사용자이면 사용자 정보 반환
        user = self.sg_cls.get_shotgrid_email(input_id, input_pw)
        
        if not user: # user가 None일 경우
            # QMessageBox.about(self, "경고", "등록되지 않은 사용자입니다!\n올바른 정보를 입력해주세요")
            self.ui.lineEdit_id.clear()
            self.ui.lineEdit_pw.clear()
            self.count += 1
            if not self.count >= 5:
                QMessageBox.about(self, "경고", f"등록되지 않은 사용자입니다!\n로그인 시도 {self.count}회입니다.\n로그인 시도 5회 이상 시 로그인이 제한됩니다.")

        if self.count >= 5:
            QMessageBox.about(self, "경고", f"로그인 시도 {self.count}회입니다.\n로그인 시도 횟수 초과로 프로그램이 종료됩니다.")
            self.timeout_popup()
            win.close()

        # user 출력 {'type': 'HumanUser', 'id': 121, 'login': 'shiena0302@gmail.com'}
        shotgrid_email = user["login"]
        shotgrid_id = user["id"]

        if shotgrid_email == input_id:
            print("정보 일치")

            datas = self.sg_cls.get_dept(shotgrid_id)
            user_dept = datas["department"]["name"]  # Shot
            self.ui.label_timeout.setText(f"로그인 완료! {user_dept} Loader 접속 중입니다!")
            self.get_dept(shotgrid_id)



    def timeout_popup(self):
        # Dialog 팝업 창 생성
        self.popup = QDialog(self)
        self.popup.setWindowTitle("타이머 팝업")
        self.popup.setGeometry(200, 100, 200, 100)

        # 타이머 설정
        self.remaining_time = 0.1 * 60 # 180초
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        # self.timer.start(1000) # 1ch 간격으로 타이머 업데이트

        # 팝업 창에 시간 표시
        self.timer_label = QLabel(f"남은 시간: {self.remaining_time}초", self.popup)
        layout = QVBoxLayout(self.popup)
        layout.addWidget(self.timer_label)

        # 모달로 팝업 창 표시
        self.popup.setModal(True)
        self.popup.show() # 다이얼로그를 모달로 실행

        # 닫기 버튼 비활성화
        self.find_close_button()

        self.timer.start(1000) # 1초 간격으로 타이머 업데이트

        self.popup.exec() # Dialog가 닫힌 후의 작업은 여기에서 수행

    def find_close_button(self): # 닫기 버튼을 찾아서 비활성화
        # Qt의 다이얼로그는 기본적으로 닫기 버튼이 QAbstractButton으로 존재합니다.
        for btn in self.popup.findChildren(QAbstractButton):
            if btn.text() == "X":
                self.close_button = btn
                self.close_button.setEnabled(False)
                break

    def closeEvent(self, event):
        # 타이머가 완료되지 않았을 때는 닫기 버튼 클릭을 무시합니다.
        if self.remaining_time > 0:
            event.ignore()
        else:
            super().closeEvent(event)

    def update_time(self):
        self.remaining_time -= 1
        self.timer_label.setText(f"남은 시간: {self.remaining_time}초")

        if self.remaining_time <= 0:
            self.timer.stop()
            if hasattr(self, 'close_button'):
                self.close_button.setEnabled(True)
            self.ui.label_timeout.setText("로그인 접근 제한이 해제되었습니다.\n로그인을 다시 시도할 수 있습니다.")
            # self.popup.accept() # Dialog 닫기

        # total_seconds = 0.1 * 60 # 6초 테스트

        # def update_time():
        #     nonlocal total_seconds
        #     total_seconds -= 1
        #     self.ui.label_timeout.setText(f"{total_seconds}초 후 다시 접근 가능")
        #     self.ui.label_timeout.setText(f"로그인 횟수 5회 초과로 3분 동안 로그인 프로그램 접근이 제한됩니다.\n남은 시간 : {total_seconds}초")
        #     if total_seconds == 0:
        #         loop.quit()

        # loop = QEventLoop()
        # timer = QTimer(self)
        # timer.timeout.connect(update_time) # timer라는 QTimer 객체의 timeout 시그널이 발생할 때마다 update_time 함수 호출
        # timer.start(1000) # 1000 밀리초마다 update_time을 호출해서 남은 시간을 업데이트
        # loop.exec() # total_seconds 동안 실행되는 동안 매초 남은 시간이 업데이트 됨
        # timer.stop() # 타이머 종료
        # self.ui.label_timeout.setText("로그인 접근 제한이 해제되었습니다.\n로그인을 다시 시도할 수 있습니다.")



    # def connect_sg(self):
    #     sg = shotgun.Shotgun(URL,
    #                         SCRIPT_NAME,
    #                         API_KEY)
    #     return sg

    def get_dept(self, shotgrid_id): # 사용자 이름, Department 정보 가져오기
        # print(shotgrid_id) # 작업자의 id
        # sg = self.connect_sg()

        # filter_dept = [["id", "is", shotgrid_id]]
        # field_dept = ["name", "department"]
        # datas = sg.find_one("HumanUser", filters=filter_dept, fields=field_dept) # "~"에서 filters 조건에 맞는 fields를 찾는다
        # print(datas) # {'type': 'HumanUser', 'id': 121, 'name': 'hyoeun seol', 'department': {'id': 41, 'name': 'Shot', 'type': 'Department'}}

        datas = self.sg_cls.get_dept(shotgrid_id)

        user_name = datas["name"]  # hyoeun seol
        user_dept = datas["department"]["name"]  # Shot
        user_id = datas["id"] # 121

        self.load_Loader(user_name, user_dept, user_id)

    def load_Loader(self, user_name, user_dept, user_id): # 작업자의 Department(asset, shot)에 따라 Loader에 연결 (서브 윈도우 실행)

        if user_dept == "Asset":
            print(f"에셋 작업자입니다. {user_name}님 에셋 로더로 연결합니다.")
            from loader import asset_loader # 파일 이름
            global asset_window # login.py(메인 파일)에서 QApplication를 실행할 때 asset_window를 포함하도록
            asset_window = asset_loader.AssetLoader(user_id) # 클래스 이름
            asset_window.show()
            win.close()

        if user_dept == "Shot":
            print(f"샷 작업자입니다. {user_name}님 샷 로더로 연결합니다.")
            from loader import shot_loader
            global shot_window
            shot_window = shot_loader.ShotLoader(user_id)
            shot_window.show()
            win.close()
        
        os.environ["USER_ID"] = user_id # 대문자는 약속
        print(user_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Login()
    win.show()
    app.exec()