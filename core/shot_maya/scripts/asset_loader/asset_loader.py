# Maya Asset Loader (ly, ani, lgt)
import sys
import os
import subprocess
import json
from datetime import datetime
from glob import glob
from configparser import ConfigParser
from pprint import pprint
from functools import partial

try:
    from PySide6.QtWidgets import QApplication, QWidget, QGridLayout
    from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout
    from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import QFile, Qt, Signal
except:
    from PySide2.QtWidgets import QApplication, QWidget, QGridLayout
    from PySide2.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout
    from PySide2.QtWidgets import QLabel, QMessageBox, QPushButton
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtGui import QPixmap
    from PySide2.QtCore import QFile, Qt, Signal

from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi



class AssetLoader(QWidget):

    def __init__(self, user_id):
        super().__init__()

        self.user_id = user_id

        self.sg_api = ShotgunApi
        self.maya_api = MayaApi
        self.sg_api.get_datas_by_user_id(self.user_id)
        self.get_user_id() # Loader를 통해서 마야를 실행했을 때 터미널에 있는 user_id를 받아서 user_name을 찾는다

        self.make_ui()
        self.event_func() # 이벤트 함수 모음

        self.get_shot_info_from_current_directory() # 현재 작업 파일 경로에서 데이터 추출
        self.current_dict = self.self.maya_api.get_reference_assets() # 현재 씬에 있는 reference Asset name, 경로
        self.classify_task() # task 별로 다른 함수를 실행할 수 있도록 classyfy_task 함수에 task 전달
        self.compare_assets()

        self.get_linked_cam_link_info()
        self.set_undistortion_size() # render resolution setting
        self.set_frame_range() # frame range setting

    def event_func(self):
        self.ui.tableWidget.itemSelectionChanged.connect(self.selected_asset_thumbnail) # 테이블 위젯 아이템 클릭할 때마다 썸네일 보이게
        self.label_img.doubleClicked.connect(self.open_thumbnail) # 썸네일 더블 클릭하면 이미지 오픈

        self.ui.pushButton_import.clicked.connect(self.get_checked_row) # Import 버튼 누르면 선택한 리스트의 에셋 Import
        self.ui.pushButton_refresh.clicked.connect(self.refresh_sg) # Refresh 버튼 누르면 샷그리드 연동 새로고침



    def get_user_id(self): # Loader를 통해 마야를 실행했을 때 user_id 받아오기
        try:
            self.user_id = os.environ["USER_ID"] # loader에서 publish, upload, import로 user_id 전달
        except:
            QMessageBox.about(self, "경고", "유효한 사용자가 아닙니다")

    def get_user_name(self): # self.user_name
        # user_id로 user_name 찾는 모듈 사용
        user_datas = self.sg_api.get_datas_by_user_id(self.user_id)
        user_name = user_datas["name"]
        self.user_name = user_name

    def get_shot_info_from_current_directory(self): # project, seq_name, seq_num, task, version, shot_id 추출

        current_file_path = self.maya_api.get_current_file_directory()
        self.project = current_file_path.split("/")[4] # Moomins
        seq_name = current_file_path.split("/")[6] # AFT
        self.seq_num = current_file_path.split("/")[7] # AFT_0010
        self.task = current_file_path.split("/")[8] # ly
        self.version = current_file_path.split("/")[11] # v001

        self.ui.label_project.setText(self.project)
        self.ui.label_sqnum.setText(self.seq_num)
        self.ui.label_task.setText(self.task)

        self.shot_id = self.sg_api.get_shot_id(self.seq_num)
        print(f"현재 작업 샷 넘버 : {self.seq_num} (id : {self.shot_id})")



# Task(ly, ani, lgt) 구분해서 ini를 만드는 다른 함수 실행
    def classify_task(self):
        print(f"현재 작업 Task : {self.task}")

        if self.task == "ly":
            print("레이아웃 작업을 시작합니다.\nlkd 또는 rig asset과 rendercam Import하세요.")
            self.get_ly_assigned_assets() # seq num에 부여된 asset들의 정보들을 찾아서 ini를 만든다.
            self.make_table_ui_for_ly() # ini 파일 받아서 ui에 넣기

        elif self.task == "ani":
            print("애니메이션 작업을 시작합니다.\nly과 rendercam Import하세요.")
            self.get_lgt_assgined_assets() # seq num가 같은 ly, ani, fx task의 정보들을 찾아서 ini를 만든다.
            self.make_table_ui_for_ani()

        elif self.task == "lgt":
            print("라이팅 작업을 시작합니다.\nly, ani, fx, rendercam Import하세요.")
            self.get_lgt_assgined_assets() # seq num가 같은 ly, ani, fx task의 정보들을 찾아서 ini를 만든다.
            self.make_table_ui_for_lgt()

        else: # Maya Shot 작업자가(ly, ani, lgt) 아닌 경우 아무것도 할 수 없도록
            print("마야에서 에셋을 import할 수 있는 작업 상태가 아닙니다.")
            QMessageBox.about(self, "경고", "'Import Assets'는 maya를 사용하는 Shot 작업에서만 실행할 수 있습니다.\n현재 작업 중인 task를 확인해주세요.")



# Layout : shot number에 태그된 asset들(mod.mb 또는 rig.mb)의 정보 찾기
    def get_ly_assigned_assets(self): # shot에 태그된 asset id들을 가져와서 list로 만들어서 다음 함수에 넘긴다
        assets_of_seq = self.sg_api.get_assets_of_seq(self.seq_num)
        asset_list = assets_of_seq["assets"]
        # print(asset_list)
        # [{'id': 1546, 'name': 'bat', 'type': 'Asset'},
        # {'id': 1479, 'name': 'car', 'type': 'Asset'},
        # {'id': 1547, 'name': 'joker', 'type': 'Asset'}]

        asset_id_list = []
        for asset in asset_list:
            asset_id = asset["id"] # 1546
            asset_id_list.append(asset_id) ###################### 이거 왜 한 번에 안하고 이렇게 id를 따로 뺐었지?

        self.make_asset_ini_for_ly(asset_id_list) # shot에 부여된 asset id 리스트를 넘겨준다

    def make_asset_ini_for_ly(self, asset_id_list): # ★ asset id 기준으로 찾은 정보들을 self.asset.ini에 넣는다
        self.asset_ini_for_ly = ConfigParser()

        # Rendercam 섹션을 가장 처음에 추가
        linked_cam_info_dict = self.get_linked_cam_link_info()
        self.asset_ini_for_ly["rendercam"] = {}
        self.asset_ini_for_ly["rendercam"]["asset status"] = linked_cam_info_dict["asset status"]
        self.asset_ini_for_ly["rendercam"]["asset pub directory"] = linked_cam_info_dict["asset pub directory"]
        self.asset_ini_for_ly["rendercam"]["asset artist"] = linked_cam_info_dict["asset artist"]
        self.asset_ini_for_ly["rendercam"]["asset task"] = linked_cam_info_dict["asset task"]
        self.asset_ini_for_ly["rendercam"]["asset file ext"] = linked_cam_info_dict["asset file ext"]
        self.asset_ini_for_ly["rendercam"]["asset version"] = linked_cam_info_dict["asset veresion"]
        self.asset_ini_for_ly["rendercam"]["asset pub date"] = linked_cam_info_dict["asset pub date"]

        # mod, lkd 에셋들을 카메라 다음 섹션에 추가
        # SG Asset Entity에서 가져오는 것 : 각 Asset의 Name, Status, Task
        for asset_id in asset_id_list:
            # print (asset_id)
            # [1546, 1479, 1547]
            asset_info = self.sg_api.get_asset_info(asset_id)

            asset_info = asset_info[0]
            asset_name = asset_info["code"] # joker
            self.asset_ini_for_ly[asset_name] = {} # asset name을 section으로 사용


            # task ID로 작업자, step 정보 가져오기 (lkd, mod, rig 알파벳 순서))
            # Asset에 연결된 모든 Task의 ID를 추출
            task_ids = [task['id'] for task in asset_info['tasks']] # [6353, 6350, 6352, 6351, 6348, 6349]

            for task_id in task_ids:
                # tasks_info = self.sg.find("Task", [["id", "is", task_id]], ["task_assignees", "step", "sg_status_list"])

                tasks_info = self.sg_api.get_tasks_info(task_id)
                task_info = tasks_info[0]

                artist_list = task_info["task_assignees"]
                for i in artist_list:
                    artist_info = i
                asset_artist = artist_info["name"]
                asset_task = task_info["step"]["name"]
                asset_status = task_info["sg_status_list"]

                self.asset_ini_for_ly[asset_name]["asset artist"] = asset_artist
                self.asset_ini_for_ly[asset_name]["asset task"] = asset_task
                self.asset_ini_for_ly[asset_name]["asset status"] = asset_status


                # 파일 경로, 펍 날짜
                path_info, date_info = self.sg_api.get_path_info(task_id)

                path_description = str(path_info["sg_description"]) # 펍된 파일 경로
                pub_file_name = os.path.basename(path_description) # BRK_0010_v001.mb
                self.asset_ini_for_ly[asset_name]["asset pub directory"] = path_description

                pub_dates = date_info["updated_at"]
                pub_date = str(pub_dates).split("+")[0]
                self.asset_ini_for_ly[asset_name]["asset pub date"] = pub_date

            file_exts = pub_file_name.split(".")[-1]
            file_ext = "." + file_exts
            version = pub_file_name.split(".")[0].split("_")[-1]
            self.asset_ini_for_ly[asset_name]["asset file ext"] = file_ext # .mb
            self.asset_ini_for_ly[asset_name]["asset version"] = version # v001

        print("*"*20,"\nini 파일 확인용 출력", "*"*20)
        for section in self.asset_ini_for_ly.sections():
            for k, v in self.asset_ini_for_ly[section].items():
                print(f"{section}, {k}: {v}")
            #     # bat, asset status: wip
            #     # bat, asset pub directory: /home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v001/bat_v001.mb
            #     # bat, asset artist: 정현 염
            #     # bat, asset task: rig
            #     # bat, asset file ext: .mb
            #     # bat, asset version: v001
            #     # bat, asset pub date: 2024-08-23 17:21:08
            #     # joker, asset status: pub
            #     # joker, asset pub directory: /home/rapa/pub/Moomins/asset/character/joker/rig/pub/scenes/v001/joker_v001.mb
            #     # joker, asset artist: 정현 염
            #     # joker, asset task: rig
            #     # joker, asset file ext: .mb
            #     # joker, asset version: v001
            #     # joker, asset pub date: 2024-08-23 17:21:08


# Animation, Lighting : 같은 shot number에 해당되는 ly, ani, fx의 정보들 찾기
    def get_lgt_assgined_assets(self): # task id에 해당되는 ly, ani, fx의 abc 파일 경로를 찾습니다
        ly_asset_info, ani_asset_info, fx_asset_info = self.sg_api.get_lgt_assgined_assets(self.shot_id)

        ly_asset_id = ly_asset_info["id"] # 6328
        ani_asset_id = ani_asset_info["id"] # 6326
        fx_asset_id = fx_asset_info["id"] # 6331

        ly_asset_directory = ly_asset_info["sg_description"] # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/scenes/v001/AFT_0010_ly_v001.abc
        ani_asset_directory = ani_asset_info["sg_description"] # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/ani/pub/scenes/v001/AFT_0010_ani_v001.abc
        fx_asset_directory = fx_asset_info["sg_description"] # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/fx/pub/scenes/v001/AFT_0010_fx_v001.abc

        shot_asset_dict = {}
        shot_asset_dict[ly_asset_id] = ly_asset_directory
        shot_asset_dict[ani_asset_id] = ani_asset_directory
        shot_asset_dict[fx_asset_id] = fx_asset_directory
        self.make_asset_ini_for_lgt(shot_asset_dict)

    def make_asset_ini_for_lgt(self, shot_asset_dict): # ly, ani, fx에서 pub한 파일의 정보가 담긴 ini 만들기
        self.asset_ini_for_lgt = ConfigParser()

        # Rendercam 섹션을 가장 처음에 추가
        linked_cam_info_dict = self.get_linked_cam_link_info()
        self.asset_ini_for_lgt["rendercam"] = {}
        self.asset_ini_for_lgt["rendercam"]["asset status"] = linked_cam_info_dict["asset status"]
        self.asset_ini_for_lgt["rendercam"]["asset pub directory"] = linked_cam_info_dict["asset pub directory"]
        self.asset_ini_for_lgt["rendercam"]["asset artist"] = linked_cam_info_dict["asset artist"]
        self.asset_ini_for_lgt["rendercam"]["asset task"] = linked_cam_info_dict["asset task"]
        self.asset_ini_for_lgt["rendercam"]["asset file ext"] = linked_cam_info_dict["asset file ext"]
        self.asset_ini_for_lgt["rendercam"]["asset version"] = linked_cam_info_dict["asset veresion"]
        self.asset_ini_for_lgt["rendercam"]["asset pub date"] = linked_cam_info_dict["asset pub date"]

        # ly, ani, fx 에셋들을 그 다음 섹션에 추가
        for asset_id, asset_directory in shot_asset_dict.items():
            asset_datas = self.sg_api.get_asset_datas(asset_id)
            asset_data = asset_datas[0]

            artist_data_list= asset_data["task_assignees"]
            for i in artist_data_list:
                artist_data = i
            asset_artist = artist_data["name"]
            asset_status = asset_data["sg_status_list"]
            asset_pub_dates = asset_data["updated_at"]
            asset_pub_date = str(asset_pub_dates).split("+")[0]
            asset_name = asset_data["content"] # AFT_0010_ly, AFT_0010_ani, AFT_0010_fx
            asset_task = asset_data["step"]["name"]
            file_name = os.path.basename(asset_directory) # AFT_0010_lgt_v001.abc
            file_ext = "." + file_name.split(".")[-1]

            # ani 경로에서 필요한 거 따기
            self.asset_ini_for_lgt[asset_name] = {}
            self.asset_ini_for_lgt[asset_name]["asset pub directory"] = asset_directory # 가져올 파일 경로
            self.asset_ini_for_lgt[asset_name]["asset task"] = asset_task # 해당 에셋의 task
            self.asset_ini_for_lgt[asset_name]["asset file ext"] = file_ext # .abc
            self.asset_ini_for_lgt[asset_name]["asset version"] = self.version # v001
            self.asset_ini_for_lgt[asset_name]["asset artist"] = asset_artist # hyoeun seol
            self.asset_ini_for_lgt[asset_name]["asset status"] = asset_status # pub
            self.asset_ini_for_lgt[asset_name]["asset pub date"] = asset_pub_date # 2024-08-28 14:42:12

        # self.asset_ini_for_lgt 출력 확인
        for section in self.asset_ini_for_lgt.sections():
            print (section)
            for k, v in self.asset_ini_for_lgt[section].items():
                print(f"{section}, {k}: {v}")
            # AFT_0010_ly, asset pub directory: /home/rapa/pub/project/seq/AFT/AFT_0010/ly/pub/scenes/v001/AFT_0010_ly_v001.abc
            # AFT_0010_ly, asset task: ly
            # AFT_0010_ly, asset file ext: .abc
            # AFT_0010_ly, asset version: v001
            # AFT_0010_ly, asset artist: hyoeun seol
            # AFT_0010_ly, asset status: pub
            # AFT_0010_ly, asset pub date: 2024-08-28 15:26:44
            # AFT_0010_ani, asset pub directory: /home/rapa/pub/Moomins/seq/AFT/AFT_0010/ani/pub/scenes/v001/AFT_0010_ani_v001.abc
            # AFT_0010_ani, asset task: ly
            # AFT_0010_ani, asset file ext: .abc
            # AFT_0010_ani, asset version: v001
            # AFT_0010_ani, asset artist: 한별 박
            # AFT_0010_ani, asset status: wtg
            # AFT_0010_ani, asset pub date: 2024-08-28 14:42:06
            # AFT_0010_fx, asset pub directory: /home/rapa/pub/Moomins/seq/AFT/AFT_0010/fx/pub/scenes/v001/AFT_0010_fx_v001.abc
            # AFT_0010_fx, asset task: ly
            # AFT_0010_fx, asset file ext: .abc
            # AFT_0010_fx, asset version: v001
            # AFT_0010_fx, asset artist: seonil hong
            # AFT_0010_fx, asset status: wtg
            # AFT_0010_fx, asset pub date: 2024-08-28 14:42:12



# UI (현재 Task에 따라 필요한 ini 불러와서 UI에 넣기)
    def make_ui(self): # ui를 띄우고 하드 코딩 필요한 부분 추가 (아이콘, 썸네일)
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/asset_loader.ui"

        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.ui.show()
        self.setWindowTitle("Asset Loader")
        ui_file.close()

        # 더블 클릭 할 수 있는 라벨 생성해서 vereticalLayout_2의 가장 상단에 넣기
        self.label_img = DoubleClickableLabel("THUMBNAIL")
        self.label_img.setFixedSize(320, 180) # 16:9 비율 고정
        self.label_img.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.ui.verticalLayout_2.insertWidget(2, self.label_img)
        self.ui.label_artist.setText(self.user_name)

    def make_table_ui_for_ly(self): # asset 갯수만큼 컨테이너 생성하고 ini 정보를 컨테이너에 넣기

        # asset(lkd, rig) 갯수 만큼 컨테이너 한 칸씩 만들기
        row_count = len(self.asset_ini_for_ly.sections())
        self.ui.tableWidget.setRowCount(row_count)

        # self.asset_ini_for_ly에 모아놓은 에셋 정보들을 각 컨테이너에 넣기
        row_idx = 0
        for section in self.asset_ini_for_ly.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1

    def make_table_ui_for_ani(self): # lgt ini에서 ly만 추출해서 새로운 configParser 만들기

        self.asset_ini_for_ani = ConfigParser()
        for section in self.asset_ini_for_lgt.sections():
            # if self.asset_ini_for_lgt.has_option(section, "asset task") and self.asset_ini_for_lgt.get(section, "asset task" == "ly"):
            if self.asset_ini_for_lgt.get(section, "asset task") == "ly":
                self.asset_ini_for_ani.add_section(section)
                for k, v in self.asset_ini_for_lgt.items(section):
                    self.asset_ini_for_ani.set(section, k, v)

        # asset 갯수 만큼 컨테이너 한 칸씩 만들기
        row_count = len(self.asset_ini_for_ani.sections())
        self.ui.tableWidget.setRowCount(row_count)

        # self.asset_ini_for_ani에 모아놓은 에셋 정보들을 각 컨테이너에 넣기
        row_idx = 0
        for section in self.asset_ini_for_ani.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1

    def make_table_ui_for_lgt(self): # task asset(ly, ani, fx) 갯수만큼 컨테이너 생성하고 ini 정보를 컨테이너에 넣기

        # asset(ly, ani, fx) 갯수 만큼 컨테이너 한 칸씩 만들기
        row_count = len(self.asset_ini_for_lgt.sections())
        self.ui.tableWidget.setRowCount(row_count)
        
        # self.asset_ini_for_lgt에 모아놓은 에셋 정보들을 각 컨테이너에 넣기
        row_idx = 0
        for section in self.asset_ini_for_lgt.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1


# rendercam에 링크된 마지막 Task의 카메라 정보를 담은 dictionary 리턴
    def get_linked_cam_link_info(self):

        shot_camera_directory = self.sg_api.get_link_camera_directory(self.shot_id)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/rendercam/AFT_0010_cam.abc

        if not os.path.islink(shot_camera_directory):
            print(f"{shot_camera_directory}는 심볼릭 링크가 아닙니다.\nrendercam이 존재하는지, 링크되었는지 확인해주세요")
        linked_directory = os.readlink(shot_camera_directory)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/mm/pub/cache/v001/AFT_0010_mm_cam.abc
        linked_file_info = os.stat(linked_directory)

        # 링크된 파일의 마지막 수정 시간
        modified_timess = linked_file_info.st_mtime
        modified_times = datetime.fromtimestamp(modified_timess)
        modified_time = modified_times.strftime("%Y-%m-%d %H:%M:%S")

        cam_task = linked_directory.split("/")[8]
        cam_ext = "." + os.path.basename(linked_directory).split(".")[-1]
        cam_version = linked_directory.split("/")[-2]

        linked_cam_info_dict = {}
        linked_cam_info_dict["asset status"] = "fin"
        linked_cam_info_dict["asset pub directory"] = linked_directory
        linked_cam_info_dict["asset artist"] = ""
        linked_cam_info_dict["asset task"] = cam_task
        linked_cam_info_dict["asset file ext"] = cam_ext
        linked_cam_info_dict["asset veresion"] = cam_version
        linked_cam_info_dict["asset pub date"] = modified_time

        return linked_cam_info_dict

    def table_ui_contents(self, section, row_idx): # UI 컨테이너에 넣을 내용 하드 코딩
        self.ui.tableWidget.setRowHeight(row_idx, 60)
        self.ui.tableWidget.setColumnCount(1)

        container_widget = QWidget()
        checkbox_layout = QVBoxLayout()

        # 체크박스 생성해서 checkbox_layout에 넣기
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("checkbox_import_asset")
        self.checkbox.setChecked(True) # 기본적으로 import하지 않은 에셋은 체크박스 체크되어 있는 상태로
        self.checkbox.setFixedWidth(20)

        checkbox_layout.addWidget(self.checkbox)

        # 사용할 ini 파일 선택
        if self.task == "ly":
            ini = self.asset_ini_for_ly
        elif self.task == "ani":
            ini = self.asset_ini_for_ani
        elif self.task == "lgt":
            ini = self.asset_ini_for_lgt


        ### grid layout 생성해서 h_ly에 넣기

        assetname_artist_layout = QVBoxLayout()
        assetname_artist_layout.setAlignment(Qt.AlignVCenter)

        #  asset name
        label_asset_name = QLabel()
        label_asset_name.setObjectName("label_asset_name")
        label_asset_name.setText(section)
        label_asset_name.setAlignment(Qt.AlignLeft)
        label_asset_name.setStyleSheet("font-size: 14px;")
        label_asset_name.setFixedSize(120, 30)

        # asset artist
        label_asset_artist = QLabel()
        label_asset_artist.setObjectName("label_asset_artist")
        if ini[section]["asset artist"]: # 가장 마지막 task의 작업자
            label_asset_artist.setText(ini[section]["asset artist"])
        label_asset_artist.setAlignment(Qt.AlignLeft)
        label_asset_artist.setStyleSheet("font-size: 10px;")
        label_asset_artist.setFixedSize(100, 30)

        assetname_artist_layout.addWidget(label_asset_name)
        assetname_artist_layout.addWidget(label_asset_artist)

        # asset pub date
        asset_pub_date_layout = QHBoxLayout()

        label_asset_date = QLabel()
        label_asset_date.setObjectName("label_asset_date")
        label_asset_date.setText(ini[section]["asset pub date"])
        label_asset_date.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_date.setStyleSheet("font-size: 10px;")
        label_asset_date.setFixedSize(50, 30)
        asset_pub_date_layout.addWidget(label_asset_date)

        # asset version
        asset_version_task_layout = QHBoxLayout()

        label_asset_version = QLabel()
        label_asset_version.setObjectName("label_asset_version")
        label_asset_version.setText(ini[section]["asset version"])
        label_asset_version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_version.setStyleSheet("font-size: 12px;")
        label_asset_version.setFixedSize(50, 30)
        asset_version_task_layout.addWidget(label_asset_version)

        # asset task
        label_asset_task = QLabel()
        label_asset_task.setObjectName("label_asset_task")
        label_asset_task.setText(ini[section]["asset task"])
        label_asset_task.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_task.setStyleSheet("font-size: 12px;")
        label_asset_task.setFixedSize(50, 30)
        asset_version_task_layout.addWidget(label_asset_task)

        # asset status
        label_asset_status = QLabel()
        if ini[section]["asset status"] == "wtg":
            image_path = "/home/rapa/git/moomins/sourceimages/wtg.png"
        elif ini[section]["asset status"] == "re":
            image_path = "/home/rapa/git/moomins/sourceimages/re.png"
        elif ini[section]["asset status"] == "wip":
            image_path = "/home/rapa/git/moomins/sourceimages/wip.png"
        elif ini[section]["asset status"] == "pub":
            image_path = "/home/rapa/git/moomins/sourceimages/pub.png"
        elif ini[section]["asset status"] == "sc":
            image_path = "/home/rapa/git/moomins/sourceimages/sc.png"
        elif ini[section]["asset status"] == "fin":
            image_path = "/home/rapa/git/moomins/sourceimages/fin.png"

        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(30, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_asset_status.setPixmap(scaled_pixmap)
        label_asset_status.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        label_asset_status.setFixedSize(50, 30)

        # asset fileext
        asset_status_fileext_layout = QVBoxLayout()
        asset_status_fileext_layout.setAlignment(Qt.AlignVCenter)

        label_asset_fileext = QLabel()
        label_asset_fileext.setObjectName("label_asset_fileext")
        label_asset_fileext.setText(ini[section]["asset file ext"])
        label_asset_fileext.setAlignment(Qt.AlignLeft)
        label_asset_fileext.setStyleSheet("font-size: 12px;")
        label_asset_fileext.setFixedSize(50, 30)
        asset_status_fileext_layout.addWidget(label_asset_status)
        asset_status_fileext_layout.addWidget(label_asset_fileext)

        # asset pub directory
        asset_pub_directory_layout = QHBoxLayout()

        label_asset_pub_directory = QLabel()
        label_asset_pub_directory.setObjectName("label_asset_pub_directory")
        label_asset_pub_directory.setText(ini[section]["asset pub directory"])
        asset_pub_directory_layout.addWidget(label_asset_pub_directory)
        label_asset_pub_directory.hide()

        # h_ly 오른쪽에 PushButton 추가
        update_layout = QHBoxLayout()
        pushButton_update = QPushButton("")
        pushButton_update.setMinimumWidth(45)
        pushButton_update.setMaximumWidth(45)
        pushButton_update.setText("Update") # 버튼에 텍스트 넣기
        update_layout.addWidget(pushButton_update)
        
        current_asset_list = self.compare_assets() # 현재 씬에 import된 에셋의 이름
        ref_node, current_version = self.get_version(section) # 현재 씬에 import 된 에셋의 버전

        # 에셋 버전 비교
        if section in current_asset_list: # Import 했으면 (Outliner에 있으면)
            pushButton_update.setEnabled(False) # 버튼 비활성화
            self.checkbox.setChecked(False)     # 체크 해제

            print("*"*20, "버전 비교")
            print(ini[section]["asset version"]) # AFT_0010_v001_w001.mb
            print(current_version) # v001

            if not ini[section]["asset version"] == current_version: # Import 이후 업데이트 되었으면
                # ini에 있는 경로(샷그리드에서 임포터 켤 때 sg에서 불러온 가장 최신 경로)와
                # 딕셔너리에 내가 담아놨던 이미 임포트한 에셋의 version이 같을 때
                pushButton_update.setEnabled(True) # 버튼 활성화

        else: # import 안했으면
            pushButton_update.setEnabled(False) # 버튼 비활성화
            pushButton_update.setStyleSheet("QPushButton { background-color: transparent; border: none; }") # Update 버튼 보이지 않도록 투명하게 숨기기

        new_path = ini[section]["asset pub directory"]
        pushButton_update.clicked.connect(lambda: self.maya_api.update_reference_file_path(ref_node, new_path, pushButton_update))

        # 컨테이너 위젯에 h_ly 설정
        layout = QHBoxLayout()
        layout.addLayout(checkbox_layout)
        layout.addLayout(assetname_artist_layout)
        layout.addLayout(asset_pub_date_layout)
        layout.addLayout(asset_version_task_layout)

        layout.addLayout(asset_status_fileext_layout)
        layout.addLayout(asset_pub_directory_layout)
        layout.addLayout(update_layout)

        container_widget.setLayout(layout)
        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget) # 테이블 위젯의 row_idx 행과 0열에 container_widget을 삽입



# 현재 씬에 Reference로 import 되어있는 에셋 경로를 반환
    def get_version(self, asset_name):
        for k, v in self.current_dict.items():
            if v["asset_name"] == asset_name:
                return k, v["version"]
        return None, None

# 현재 씬에 Reference로 import 되어 있는 에셋 이름을 리스트로 반환
    def compare_assets(self):
        # print(current_dict)
        # {'bat_v001_w001RN': {'asset_name': 'bat', 'reference_file_path': '/home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v001/bat_v001_w001.mb'},
        # 'jane_v001RN': {'asset_name': 'jane', 'reference_file_path': '/home/rapa/pub/Moomins/asset/character/jane/mod/pub/scenes/v001/jane_v001.mb'}}

        if self.task == "ly":
            asset_name_list = self.asset_ini_for_ly.sections()
        elif self.task == "ani":
            asset_name_list = self.asset_ini_for_ani.sections()
        elif self.task == "lgt":
            asset_name_list = self.asset_ini_for_lgt.sections()
        
        # import할 에셋들
        # print(asset_name_list) # ['bat', 'car', 'joker', 'rock']

        # import한 에셋들
        current_asset_list = []
        for k, v in self.current_dict.items(): # 현재 씬에 reference로 불러온 에셋 이름, 경로를 담은 딕셔너리
            asset_name_in_scene = v["asset_name"]

            # import할 에셋들 중 현재 씬에 import한 에셋 이름만 포함
            if asset_name_in_scene in asset_name_list:
                current_asset_list.append(asset_name_in_scene)

        return current_asset_list



# Thumbnail (아직 없을 때는 no thumbnail)
    def selected_asset_thumbnail(self): # 선택한 에셋의 썸네일(캡처 이미지) 경로를 추출해서 보여줌
        indexes = self.ui.tableWidget.selectedIndexes() # 다중 선택이 되기 때문에 Indexes

        for index in indexes:
            # asset이 pub된 directory를 썸네일 이미지가 있는 directory로 바꾸기
            widget = self.ui.tableWidget.cellWidget(index.row(), 0)   # 테이블 위젯의 index.row()행과 0번째 열에 있는 셀의 위젯
            a = widget.findChild(QLabel, "label_asset_pub_directory") # 에셋 ini에서 label_asset_pub_directory인 QLabel의 text
            original_path = a.text()

            # pub된 파일의 경로를 샷 업로더 캡처 경로와 같게 바꾸기 (여러 개일 수 있어서 가장 마지막 w버전 사용)
            if self.task == "ly":
                # 에셋 업로더의 캡처 이미지 경로 : /home/rapa/wip/Moomins/asset/character/jane/mod/wip/images/v002/jane_v002_w001.jpg
                folder_path = original_path.replace("scenes", "images").replace(".mb", ".jpg").replace("pub", "wip")
                directory_path = os.path.dirname(folder_path)
                image_path_list  = glob(os.path.join(directory_path, "*.jpg"))
                print(f"썸네일 이미지 경로 : {image_path_list}")

                if len(image_path_list) == 0:
                    my_path = os.path.dirname(__file__)
                    self.image_path = my_path + "/sourceimages/no_thumbnail.jpg"
                else:
                    self.image_path = sorted(image_path_list)[-1]

            elif self.task in ["ani", "lgt"]:
                # 샷 업로더 캡처 이미지 경로  : /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/images/v001/AFT_0010_v001_w001.jpg
                folder_path = original_path.replace("cache", "images").replace(".abc", ".jpg").replace("pub", "wip")
                directory_path = os.path.dirname(folder_path)
                image_path_list = glob(os.path.join(directory_path, "*.jpg"))   
                print(f"썸네일 이미지 경로 : {image_path_list}")

                if len(image_path_list) == 0:
                    my_path = os.path.dirname(__file__)
                    self.image_path = my_path + "/sourceimages/no_thumbnail.jpg"
                else:
                    self.image_path = sorted(image_path_list)[-1]

            pixmap = QPixmap(self.image_path)
            sclaed_pixmap = pixmap.scaled(364, 216)
            self.label_img.setPixmap(sclaed_pixmap)

    def open_thumbnail(self): # 더블 클릭시 썸네일 오픈
        my_path = os.path.dirname(__file__)
        no_thumbnail_path = my_path + "/sourceimages/no_thumbnail.jpg"

        if not self.image_path == no_thumbnail_path:
            subprocess.Popen(['xdg-open', self.image_path])



# Asset Import
# Import 버튼 누르면 선택된 list에 있는 에셋, shader Import
    def get_checked_row(self): # 체크된 row들을 리스트로 가져옴
        checked_row_list = []
        row_count = self.ui.tableWidget.rowCount()

        for row in range(row_count):
            container = self.ui.tableWidget.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox, "checkbox_import_asset") # 컨테이너에 있는 위젯 찾기

            if checkbox.isChecked():
                checked_row_list.append(row)

        self.get_selected_asset_list(checked_row_list)

    def get_selected_asset_list(self, checked_row_list): # 체크된 row의 에셋 경로들을 담은 리스트 만들기
        if self.task == "ly":
            ini = self.asset_ini_for_ly
        elif self.task == "ani":
            ini = self.asset_ini_for_ani
        elif self.task == "lgt":
            ini = self.asset_ini_for_lgt

        selected_list = []
        sections = ini.sections()
        for idx, section in enumerate(sections):

            if idx in checked_row_list: # 체크된 section만 가져오기
                selected_item = ini[section]["asset pub directory"]
                selected_list.append(selected_item)

        # 현재 Task가 ani일 때
        # ['/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc',
        # '/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc']

        # 현재 Task가 ly일 때
        # ['/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc',
        # '/home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v002/bat_v002.mb',...이하 생략]

        self.import_assets(selected_list) # 선택한 리스트의 에셋과 쉐이드를 씬에 import

    def import_assets(self, selected_list):
        print("선택한 asset들을 현재 scene으로 import 하겠습니다")

        for path in selected_list:
            reference_node = self.maya_api.import_reference_asset(path)
            if not reference_node:
                print (f"{path} 레퍼런스 임포트에 실패했습니다.")
                continue

            self.get_link_shader_path(path, reference_node) # 쉐이더 import

# Shader Import
    def get_link_shader_path(self, path, reference_node):
        print("각각의 에셋에 대한 shader.ma, shader.json이 link된 최종 shader 경로를 가져옵니다.")

        # /home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v002/bat_v002.mb 마야 파일 경로를 받아서

        # /home/rapa/pub/Moomins/asset/prop/knife/lkd/pub/scenes/knife_lkd_shader_link.ma 각각 이렇게 바꾸기
        # /home/rapa/pub/Moomins/asset/prop/knife/lkd/pub/scenes/knife_lkd_json_link.json

        asset_name = path.split("/")[7]
        folder_path = path.replace("rig", "lkd").replace("mod", "lkd").replace("mb", "ma")
        folder_path = os.path.dirname(folder_path)
        folder_path = folder_path.rsplit("/",1)[0]
        file_name = f"{asset_name}_lkd_shader_link.ma"

        shader_ma_path = folder_path + "/" + file_name
        shader_json_path = shader_ma_path.replace("shader", "json").replace(".ma", ".json")
        self.maya_api.assign_shader_to_asset(reference_node, shader_json_path, shader_ma_path)

    def import_shader(self, shader_ma_path, shader_json_path):
        print("shader가 들어있는 shader.ma 파일과 shader assign 정보가 들어있는 shader.json을 불러와서 오브젝트에 붙이기")
        self.maya_api.import_shader(shader_ma_path, shader_json_path)

    def set_undistortion_size(self): # 현재 씬의 Render setting Image Size 설정
        undistortion_height, undistortion_width = self.sg_api.get_undistortion_size(self.shot_id)

        self.maya_api.set_render_resolution(undistortion_height, undistortion_width)

    def set_frame_range(self): # 현재 씬의 Frame Range 설정
        start_frame, end_frame = self.sg_api.get_frame_range()
        frame_offsfet = 1000
        
        if start_frame <= frame_offsfet:
            adjusted_start_frame = start_frame + frame_offsfet
        else:
            start_frame = adjusted_start_frame

        if end_frame <= frame_offsfet:
            adjusted_end_frame = end_frame + frame_offsfet
        else:
            end_frame = adjusted_end_frame

        self.maya_api.set_frame_range(adjusted_start_frame, adjusted_end_frame)



# Refresh
    def refresh_sg(self):
        print("새로고침 실행. 테이블을 비우고 샷그리드의 정보를 다시 읽어와서 넣어줍니다.")

        self.ui.tableWidget.clear() # tableWidet의 모든 row를 비움

        # sg 데이터 다시 불러와서 테이블에 넣음
        self.current_dict = self.maya_api.get_reference_assets() # 현재 씬에 있는 reference Asset name, 경로
        self.classify_task() # task 별로 다른 함수를 실행할 수 있도록 classyfy_task 함수에 task 전달

        self.get_linked_cam_link_info()
        self.set_undistortion_size() # render resolution setting
        self.set_frame_range() # frame range setting




class DoubleClickableLabel(QLabel): # 더블 클릭 가능한 label 객체

    doubleClicked = Signal() # 더블클릭 시그널 정의

    def __init__(self, parent=None):
        super(DoubleClickableLabel, self).__init__(parent)

    def mouseDoubleClickEvent(self, event):
        # 더블클릭 이벤트가 발생했을 때 시그널을 방출합니다.
        super().mouseDoubleClickEvent(event)  # 기본 이벤트 처리
        self.doubleClicked.emit()  # 더블클릭 시그널 방출



if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = AssetLoader()
    win.show()
    app.exec()