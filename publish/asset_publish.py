#현재 마야 파일 작업 경로
# /home/rapa/wip/moomins/asset/prop/test_chair/mod/wip/scenes/
# chair_mod_v001_w001.mb
# 가상의 pub서버 /home/rapa/team_projects/moomins/asset/prop/test_chair/mod/pub/scenes/
# publish 버튼 누르면 폴더생성 pub 서버에 폴더생성

import PySide6
import os
import sys
from PySide6.QtWidgets import QApplication, QLabel, QTableWidgetItem
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from shotgun_api3 import shotgun

# maya tap버튼 누르면 dcc 창 오픈 (효은)

class AssetPublish(QWidget):
    def __init__(self):
        super().__init__()

        self.make_ui()

        self.ui.pushButton_pub.clicked.connect(self.set_pub_path)

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/asset_publish.ui"

        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        self.ui.show()
        ui_file.close()

    def connect_sg(self):
        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"
    
        sg = shotgun.Shotgun(URL,
                            SCRIPT_NAME,
                            API_KEY)
        return sg

    def set_pub_path(self):
        """
        pub 버튼을 눌렀을 때
        /home/rapa/pub .....으로 바꿔야함
        # path = f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/scene/{version}" 
        나는 파일 경로 와 파일 명에서 정보를 가져와야함
        그러기 위해서는 현재파일경로를 가져오고
        현재파일경로에서 "/"제외 이름 중 필요한 것들을 변수에 넣고
        펍 경로로 바꾸기
        """
        #현재 작업중인 경로가져오기 (py 말고, maya...mb)
        current_file_path = "/home/rapa/wip/moomins/asset/prop/test_chair/mod/pub/scene/v001" 
        current_file_name = "chair_mod_v001_w001.mb"
        # os.getcwd() #수정
        print (current_file_path)
        get_file_path = current_file_path.split('/')
        print (get_file_path)

        project = get_file_path[4]
        asset_type = get_file_path[6]
        asset_name = get_file_path[7]
        task = get_file_path[8]
        version = get_file_path[11]

        pub_path = f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/scene/{version}"
        os.makedirs(pub_path, exist_ok=False) #폴더가 이미 있으면 file exists error 발생

        # pub할 경로 표시
        self.ui.label_filepath.setText(os.path.dirname(__file__)) #디벨럽 중


    # def get_user_task(self):
    #     """
    #     생성된 폴더의 이름 mod/lkd/rig 가져오기               
    #     """





if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AssetPublish()
    # win.show()
    app.exec()