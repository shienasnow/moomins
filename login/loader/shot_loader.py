# shot loader
import sys
import os
import shutil
import re
import webbrowser
import subprocess
from pprint import pprint
# from shotgun_api3 import Shotgun
from PySide6.QtWidgets import QApplication, QWidget, QTreeWidgetItem
from PySide6.QtWidgets import QLabel, QMenu, QMessageBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap, QAction,QGuiApplication

sys.path.append("/home/rapa/git/pipeline/api_scripts")

from shotgun_api import ShotgunApi


class ShotLoader (QWidget): 

    def __init__(self, user_id=None):
        super().__init__()
        self.user_id = user_id

        self.sg_cls = ShotgunApi()
        # print (user_id)
        self.sg_cls.get_datas_by_id(self.user_id)

        self.make_ui()

        # self.connect_id()
        self.get_task_data()
        self.set_treewidget()
        self.make_tablewidget()

        self.events()
    
        

    def make_ui(self): # ui 만드는 메서드 
        """
        ui 만드는 메서드 
        """
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/loader.ui"
        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self) 
        self.setWindowTitle("Shot loader")
        ui_file.close() 
        self.make_ui_center()

    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def events (self): # 실행 이벤트 모음
        """ 
        event 모음
        """
        self.tree.itemClicked.connect(self.click_treewiget_event) # 트리위젯 클릭 용
        self.table.cellPressed.connect(self.get_click_data) # 테이블위젯 클릭 용
        self.table.setContextMenuPolicy(Qt.CustomContextMenu) # 테이블위젯 우클릭 용
        self.table.customContextMenuRequested.connect(self.click_right_menu) # 테이블위젯 우클릭 용
        self.ui.listWidget.itemDoubleClicked.connect(self.double_clicked_item) # 리스트위젯 더블클릭 용
        self.ui.pushButton.clicked.connect(self.refresh) # refresh 용 버튼
     
    def get_task_data(self): # 할당된 데이터 정보 가져와서 딕셔너리로 정리
        """
        user data dict으로 재정리
        """
        self.datas_list = self.sg_cls.get_task_data(self.user_id)
        # pprint (self.datas_list) # 모든 task 정상적으로 출력됨 ########################################## ok

        # data 정리
        self.projects_data_dict = {}
        
        for data_dict in self.datas_list: # 리스트 풀기 
            project_name = data_dict["project"]["name"]                  # 프로젝트 이름 Moomins
            seq_name_part = data_dict["entity"]["name"].split("_")[0]    # 시퀀스 이름만 나와 있는 부분 AFT
            seq = data_dict["entity"]["name"]                            # 시퀀스 풀네임 AFT_0010
            task = data_dict["step"]["name"]                             # 소속 파트 ani
            start_date = data_dict["start_date"]                         # 시작 날짜 2024-09-03
            due_date = data_dict["due_date"]                             # 마감 날짜 2024-09-11
            status = data_dict["sg_status_list"]                         # 작업 상황 wtg


            # for task in task_list:
            # 버전 정리
            ver_path = f"/home/rapa/wip/{project_name}/seq/{seq_name_part}/{seq}/{task}/wip/scene"
            if not os.path.exists(ver_path):
                version = "v001"
            else:
                ver_folders = os.listdir(ver_path)
                if not ver_folders:
                    version = "v001"
                else:
                    version = sorted(ver_folders)[-1]
            

            # 데이터 딕셔너리로 정리
            if project_name not in self.projects_data_dict:
                self.projects_data_dict[project_name] = {}

            if seq not in self.projects_data_dict[project_name]:
                self.projects_data_dict[project_name][seq] = {}

            self.projects_data_dict[project_name][seq]["task"] = task
            self.projects_data_dict[project_name][seq]["start_date"] = start_date
            self.projects_data_dict[project_name][seq]["due_date"] = due_date
            self.projects_data_dict[project_name][seq]["status"] = status
            self.projects_data_dict[project_name][seq]["version"] = version
        
        print("---------------------------------")
        pprint(self.projects_data_dict)

    # treewidget 관련 메서드들
    def set_treewidget(self): # 트리 위젯에 정보 띄우기
        """
        treeWidget 에 정보 띄우기 
        """
        self.tree = self.ui.treeWidget
        self.tree.clear()
        # self.ui.listWidget.clear()

        # 트리에 띄울 project 와 seq 이름의 알파벳 부분만 딕셔너리에 넣기
        treewiget_project_dict = {}
        for project_name, seq_dict in self.projects_data_dict.items():
            # print (treewiget_project_dict)

            for seq_name in seq_dict.keys():
                seq_name_parts = seq_name.split("_")[0]
                # print (seq_name_parts)
                
                if project_name not in treewiget_project_dict:
                    treewiget_project_dict[project_name] = []

                if seq_name_parts not in treewiget_project_dict[project_name]:
                    treewiget_project_dict[project_name].append(seq_name_parts)

            # print (treewiget_project_dict) # {'Marvelous': ['OPN', 'hyo'], 'Moomins': ['STG', 'BRK', 'RST', 'RVL', 'FIN', 'AFT', 'KLL', 'MAD', 'MSK', 'OPN', 'TRS'], 'Test_phoenix': ['OPN', 'END']}

        # 트리 위젯에 추가 
        for project, seq_name_parts in treewiget_project_dict.items():
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, project)

            for seq_name_part in sorted(seq_name_parts):
                seq_item = QTreeWidgetItem(project_item)
                seq_item.setText(0, seq_name_part)

    def click_treewiget_event(self, item): # 트리 위젯에서 클릭했을 때 매치 되는 데이터 보내기
        """
        treeWidget 을 클릭했을 때 매치되는 데이터 찾기
        """
        self.table.clear()
        self.ui.listWidget.clear()

        if item.childCount() > 0: # 프로젝트 ( 부모 )
            selected_project = item.text(0)
            for project_name, seq_data_dict in self.projects_data_dict.items():
                if project_name == selected_project:
                    matching_project_dict = self.projects_data_dict[selected_project]
                    if matching_project_dict:
                        self.update_table_items(matching_project_dict, None)

        else:                      # 시퀀스 ( 자식 )
            matching_seq_dict = {}
            selected_seq_name_parts = item.text(0)
            selected_project = item.parent().text(0)
            for project_name, seq_data_dict in self.projects_data_dict.items():
                if project_name == selected_project:
                    for seq in seq_data_dict.keys():
                        seq_name_parts = seq.split("_")[0]
                        if seq_name_parts == selected_seq_name_parts:
                            matching_seq_data_dict = seq_data_dict[seq]
                            matching_seq_dict[seq] = matching_seq_data_dict
                            if matching_seq_dict:
                                self.update_table_items(None, matching_seq_dict)


    # tablewidget 관련 메서드들
    def make_tablewidget(self): # 테이블 위젯 기본 세팅
        """
        tableWidget 기본 setting
        """
        self.table = self.ui.tableWidget
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 300)


    def update_table_items(self, matching_project_dict=None, matching_seq_dict=None): # 테이블위젯에 row 추가
        """
        data 양에 맞게 tableWidget 에 row 추가
        """
        if matching_project_dict:
            data_dict = matching_project_dict
        elif matching_seq_dict:
            data_dict = matching_seq_dict
        else:
            return  # 매칭되는 테스크가 없을 때
        
        self.table.setRowCount(len(data_dict)) 
        row = 0
        for row, seq_name in enumerate(data_dict):
            self.make_table_hard_coding(row, data_dict, seq_name)
            # print (row, data_dict, seq_name)
            row += 1

    def make_table_hard_coding(self, row, data_dict, seq_name): # 하드 코딩으로 테이블 만들기
        """
        하드 코딩으로 tableWidget 만들기
        """
        # print (row, data_dict) 0 {'BRK_0010': {'task': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 're', 'version': 'v001'}}

        # 데이터 정리 {'BRK_0010': {'task': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 're', 'version': 'v001'}}
        task = data_dict[seq_name]["task"]
        version = data_dict[seq_name]["version"]
        start_date = data_dict[seq_name]["start_date"]
        due_date = data_dict[seq_name]["due_date"]
        date_range = f"{start_date} - {due_date}"
        status = data_dict[seq_name]["status"]

        container_widget = QWidget() # 컨테이너 위젯 생성
        grid_layout = QGridLayout() # 그리드 레이아웃 생성
        container_widget.setLayout(grid_layout) # 컨테이너에 레이아웃 설정

        self.table.setRowHeight(row, 80) # 행 row 의 높이 조절

        self.table.setCellWidget(row, 0, container_widget) # 테이블 위젯에 컨테이너 추가
        

        # 프로그램 로고 사진 라벨 제작
        label_node_name1 = QLabel()
        if task in ["ly", "ani", "lgt"]:
            image_path = "/home/rapa/git/pipeline/sourceimages/maya.png"
        elif task == "fx":
            image_path = "/home/rapa/git/pipeline/sourceimages/houdini.png"
        elif task  in ["prc", "cmp"]:
            image_path = "/home/rapa/git/pipeline/sourceimages/nuke.png"
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(60, 60,  Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_node_name1.setPixmap(scaled_pixmap)
        label_node_name1.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_node_name1.setFixedSize(80, 80)

        # 시퀀스 이름 라벨 제작
        label_node_name2 = QLabel()
        label_node_name2.setText(seq_name)
        label_node_name2.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_node_name2.setObjectName("seq_name")
        label_node_name2.setStyleSheet("font-size: 12px;")
        label_node_name2.setFixedSize(80, 20)

        # 버전 이름 라벨 제작

        label_node_name3 = QLabel()
        label_node_name3.setText(version)
        label_node_name3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_node_name3.setObjectName("version")
        label_node_name3.setStyleSheet("font-size: 12px;")
        label_node_name3.setFixedSize(70, 20)    
        
        # 유저 파트 라벨 제작
        label_node_name4 = QLabel()
        label_node_name4.setText(task)
        label_node_name4.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_node_name4.setObjectName("task")
        label_node_name4.setStyleSheet("font-size: 12px;")
        label_node_name4.setFixedSize(80, 20)   
        
        # 제작 기간 라벨 제작
        label_node_name5 = QLabel()
        label_node_name5.setText(date_range)
        label_node_name5.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_node_name5.setStyleSheet("font-size: 12px;")
        label_node_name5.setFixedSize(145, 20)

        # # 작업 상태 라벨 제작
        # label_node_name6 = QLabel()
        # label_node_name6.setText(status)
        # label_node_name6.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # label_node_name6.setStyleSheet("font-size: 12px;")
        # label_node_name6.setFixedSize(100, 20)       

        # 작업 상태 라벨 제작
        label_node_name6 = QLabel()
        if status == "wtg":
            image_path = "/home/rapa/git/pipeline/sourceimages/wtg.png"
        elif status == "re":
            image_path = "/home/rapa/git/pipeline/sourceimages/re.png"
        elif status == "wip":
            image_path = "/home/rapa/git/pipeline/sourceimages/wip.png"
        elif status == "pub":
            image_path = "/home/rapa/git/pipeline/sourceimages/pub.png"
        elif status == "sc":
            image_path = "/home/rapa/git/pipeline/sourceimages/sc.png"
        elif status == "fin":
            image_path = "/home/rapa/git/pipeline/sourceimages/fin.png"

        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(30, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_node_name6.setPixmap(scaled_pixmap)
        label_node_name6.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_node_name6.setFixedSize(80, 20)
        
        # 레이아웃에 라벨 넣기
        grid_layout.addWidget(label_node_name1, 0, 0) # 프로그램 로고 사진
        grid_layout.addWidget(label_node_name2, 0, 1) # 시퀀스 이름
        grid_layout.addWidget(label_node_name3, 0, 2) # 버전 이름
        grid_layout.addWidget(label_node_name4, 0, 3) # 유저 테스크
        grid_layout.addWidget(label_node_name5, 1, 1, 1, 2) # 제작 기간
        grid_layout.addWidget(label_node_name6, 1, 3) # 작업 상태 

        

    def get_click_data(self, row,_): # 테이블위젯에서 선택한 row 를 전역변수로 선언해주는 메서드
        """
        tableWidet 에서 선택한 row를 self.click_row 로 선언하는 메서드
        """

        self.click_row = row
        self.set_listwidget()

   # listwidget 관련 메서드            
    def set_listwidget (self): # 리스트 위젯에 wip 파일 띄우기
        """
        listWidget 에 wip 파일 리스트 띄우기 
        """
        self.ui.listWidget.clear()

        _, _, _, _, _, _, ver_path = self.get_tablewidget_data()
 
        if not os.path.exists(ver_path):
            self.ui.listWidget.addItem("No File")
            return
        wip_files = os.listdir(ver_path)
        if not wip_files:
            self.ui.listWidget.addItem("No File")
            return
        for wip_file in wip_files:
            self.ui.listWidget.addItem(wip_file)
                    
    def double_clicked_item(self,item): # 리스트 위젯에서 파일 더블클릭하면 실행하기
        """
        listWidget 의 파일을 더블 클릭 하면 파일 실행하기
        """
        _, _, _, version, wip_path, _, _ = self.get_tablewidget_data()

        file_name = item.text()
        file_path = f"{wip_path}/scenes/{version}/{file_name}"
        print (file_path)

        # 파일이 없을 경우
        if file_name == "No File":
            self.msg_box("NoFile")
            return
        
        # 파일 확장명 별로 오픈되는 프로그램 분리
        ext = file_name.split(".")[-1]
        if ext == "mb":
            subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {file_path}'],start_new_session=True)
        elif ext == "hip":
            self.msg_box("FX")
        elif ext == "nknc":
            self.run_nuke_nknc(file_path)


    def run_nuke_nknc(self, file_path): # nknc 실행 용 메서드
        """
        nuke non-commercial 용 실행 메서드
        """
        nuke_path = 'source /home/rapa/git/pipeline/env/nuke.env && /opt/Nuke/Nuke15.1v1/Nuke15.1 --nc'
        command = f"{nuke_path} {file_path}" 
        subprocess.Popen(command, shell=True)



    # 우클릭 관련 메서드들
    def click_right_menu(self,pos): # 우클릭 띄우기
        """
        우클릭을 띄우기 위한 메서드
        """
        context_menu = QMenu()

        new_scene = QAction("New Scene", self)
        wip_version_up = QAction("Wip Version Up", self)
        shotgun_site = QAction("Shotgun Site", self)
        current_path = QAction("Current Path", self)
        retake = QAction("Retake", self)
        refresh = QAction("Refresh", self)

        new_scene.triggered.connect(self.make_new_scene)
        wip_version_up.triggered.connect(self.make_new_wip_version)
        shotgun_site.triggered.connect(self.open_shotgrid_site)
        current_path.triggered.connect(self.open_current_path)
        retake.triggered.connect(self.version_up_for_retake)
        refresh.triggered.connect(self.refresh)

        context_menu.addAction(new_scene)
        context_menu.addAction(wip_version_up)
        context_menu.addAction(shotgun_site)
        context_menu.addAction(current_path)
        context_menu.addAction(retake)
        context_menu.addAction(refresh)

        context_menu.exec(self.table.mapToGlobal(pos))

    def get_tablewidget_data(self): # 선택한 테이블 위젯의 데이터 가져오기 
        """
        tableWidget 에서 사용
        """

        # 테이블 위젯에서 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        if not widget :
            return
        seq_label = widget.findChild(QLabel, "seq_name")
        seq_name_of_table = seq_label.text() 

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 매치하기
        for project_name, seq_data_dict in self.projects_data_dict.items():
            selected_tree_item = self.tree.currentItem() 
            if selected_tree_item.childCount() > 0: # 부모일 경우 
                selected_project = selected_tree_item.text(0)
                if project_name == selected_project:
                    for seq_name, data in seq_data_dict.items():
                        task = data["task"]
                        seq_name_part = seq_name.split("_")[0]
                        version = data["version"]
                        status = data["status"]

                        if seq_name_of_table == seq_name:
                            pub_path = f"/home/rapa/pub/{project_name}/seq/{seq_name_part}/{seq_name}/{task}/pub/scenes/{version}"
                            wip_path = f"/home/rapa/wip/{project_name}/seq/{seq_name_part}/{seq_name}/{task}/wip"
                            ver_path = f"{wip_path}/scenes/{version}"
                            return seq_name, task, status, version, wip_path, pub_path, ver_path
                        
                        continue
            else:
                selected_project = selected_tree_item.parent().text(0) # 트리에서 선택한 아이템의 부모 ( 선택한 시퀀스의 프로젝트 이름 )
                if project_name == selected_project:
                    for seq_name, data in seq_data_dict.items():
                        task = data["task"]
                        seq_name_part = seq_name.split("_")[0]
                        version = data["version"]
                        status = data["status"]

                        if seq_name_of_table == seq_name:
                            pub_path = f"/home/rapa/pub/{project_name}/seq/{seq_name_part}/{seq_name}/{task}/pub/scenes/{version}"
                            wip_path = f"/home/rapa/wip/{project_name}/seq/{seq_name_part}/{seq_name}/{task}/wip"
                            ver_path = f"{wip_path}/scenes/{version}"
                            return seq_name, task, status, version, wip_path, pub_path, ver_path

######
    def make_new_scene(self): # New Scene 눌렀을 때 파트별로 새 씬(w001)이 열리거나 이미 있다면 작업 중이라고 경고 창
        self.ui.listWidget.clear()

        seq_name, task, _, version, wip_path, _, ver_path = self.get_tablewidget_data()

        print("-----------------------------------------")
        self.sg_cls.sg_shot_task_status_update(seq_name, task) ###### Backend 연결

        # 폴더 만들기
        folder_list = ["scenes", "sourceimages", "cache", "images"]
        for folder in folder_list:
            os.makedirs(f"{wip_path}/{folder}/{version}", exist_ok=True)

        # 복사할 빈 씬 경로 
        empth_file_path = os.path.dirname(__file__)

        # 레이아웃, 애니 작업자의 경우, wip 파일 없으면 만들고 실행
        if task in ["ly", "ani", "lgt"]: 
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.mb"):
                shutil.copy(os.path.join(empth_file_path, ".emptymaya.mb"), os.path.join(ver_path, ".emptymaya.mb")) # 빈 파일 복사
                os.rename(f"{ver_path}/.emptymaya.mb", f"{ver_path}/{seq_name}_{version}_w001.mb") # 파일명 지정
                subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {ver_path}/{seq_name}_{version}_w001.mb'],start_new_session=True) # 파일 실행
                return
            self.msg_box("WipStatusError")

        # # 라이팅 작업자의 경우 wip 파일 없으면 마야가 만들어지고 실행, status 가 pub 일 경우 누크가 뉴씬 되도록 
        # if task == "lgt":
        #     if os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.mb"): # 마야 경로가 존재할 경우
        #         if status == "pub": # 프리컴프 단계에선 누크가 뉴씬 되도록
        #             shutil.copy(os.path.join(empth_file_path, ".emptynuke.nknc"), os.path.join(ver_path, ".emptynuke.nknc")) # 빈 파일 복사
        #             os.rename(f"{ver_path}/.emptynuke.nknc", f"{ver_path}/{seq_name}_{version}_w001.nknc") # 파일명 지정
        #             file_path = f"{ver_path}/{seq_name}_{version}_w001.nknc"
        #             self.run_nuke_nknc(file_path)
        #         else: # 마야 작업 중일 경우
        #             self.msg_box("WipStatusError")
        #     else: # 마야 뉴씬 할 경우
        #         os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.mb")
        #         shutil.copy(os.path.join(empth_file_path, ".emptymaya.mb"), os.path.join(ver_path, ".emptymaya.mb")) # 빈 파일 복사
        #         os.rename(f"{ver_path}/.emptymaya.mb", f"{ver_path}/{seq_name}_{version}_w001.mb") # 파일명 지정
        #         subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {ver_path}/{seq_name}_{version}_w001.mb'],start_new_session=True)
                    

        # 후디니 작업자의 경우, wip 파일 없으면 만들고 실행
        elif task == "fx":
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.hip"):
                self.msg_box("FX")
                return
            self.msg_box("WipStatusError")

        # 누크 작업자의 경우, wip 파일 없으면 만들고 실행
        elif task  in ["prc", "cmp"]:
            print ("누크 작업자")
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.nknc"):
                shutil.copy(os.path.join(empth_file_path, ".emptynuke.nknc"), os.path.join(ver_path, ".emptynuke.nknc")) # 빈 파일 복사
                os.rename(f"{ver_path}/.emptynuke.nknc", f"{ver_path}/{seq_name}_{version}_w001.nknc") # 파일명 지정
                file_path = f"{ver_path}/{seq_name}_{version}_w001.nknc"
                self.run_nuke_nknc(file_path)
                return
            self.msg_box("WipStatusError")
        
        else:
            print ("작업자 아님")


        self.set_listwidget()

    def make_new_wip_version(self): # wip 파일 버전 업 / wip 파일이 아예 없다면 경고창 띄우기

        _, task, _, _, _, _, ver_path = self.get_tablewidget_data()
        
        # 파트별 확장명 정리
        if task in ["ly", "ani", "lgt"]:
            ext = "mb"
        elif task == "fx":
            ext = "hip"
        elif task  in ["prc", "cmp"]:
            ext = "nknc"

        # 경로나 wip 파일 없으면 작업 전 알리는 경고창 띄우기
        if not os.path.exists(ver_path):
            self.msg_box("NoFile")
            return
        wip_files = os.listdir(ver_path)
        if not wip_files:
            self.msg_box("NoFile")
            return
        
        # wip 파일 있으면 마지막 버전에서 버전 업 생성
        last_wip_file = sorted(wip_files)[-1]
        
        match = re.search(rf'_w(\d+)\.{ext}', last_wip_file)
        wip_num = int(match.group(1))
        wip_ver_up = wip_num + 1
        new_wip_num = f"_w{wip_ver_up:03d}.{ext}"

        new_wip_file = last_wip_file.replace(match.group(0), new_wip_num)
        shutil.copy(os.path.join(ver_path, last_wip_file), os.path.join(ver_path, new_wip_file))

        self.set_listwidget()

    def open_shotgrid_site(self): # 샷그리드 오픈 메서드

        shotgrid_url = "https://4thacademy.shotgrid.autodesk.com/projects/"
        webbrowser.open(shotgrid_url)

    def open_current_path(self): # 현재 버전의 경로를 열어주는 메서드

        _, _, _, _, _, _, ver_path = self.get_tablewidget_data()

        if not os.path.exists (ver_path):
            self.msg_box("NoPath")
            return
        subprocess.call(["xdg-open", ver_path]) # 리눅스 버전
######
    def version_up_for_retake(self): # pub 한 파일 retake 받았을 때 wip 에 새로운 ver 폴더와 wip 파일 생성되는 메서드
       
        seq_name, task, status, _, wip_path, pub_path, _ = self.get_tablewidget_data()

        print("-----------------------------------------")
        self.sg_cls.sg_shot_task_status_update(seq_name, task) ###### Backend 연결

        # 파트별 확장명 정리
        if task in ["ly", "ani", "lgt"]:
            ext = "mb"
        elif task == "fx":
            ext = "hip"
        elif task == ["prc", "cmp"]:
            ext = "nknc"

        if status == "re":
            pub_files = os.listdir(pub_path)
            last_pub_file = sorted(pub_files)[-1]

            # retake 받았을 때 pub 에 있는 파일을 버전을 높이기
            match = re.search(rf'_v(\d+)\.{ext}', last_pub_file)
            ver_num = int(match.group(1))
            ver_up_num = ver_num + 1
            new_ver_num = f"v{ver_up_num:03d}"

            # 폴더 경로 만들기 
            folder_list = ["scenes", "sourceimages", "cache", "images"]
            for folder in folder_list:
                os.makedirs(f"{wip_path}/{folder}/{new_ver_num}", exist_ok=True)

            new_ver_path = f"{wip_path}/scene/{new_ver_num}"

            # wip 폴더에 파일 복사하기
            shutil.copy(os.path.join(pub_path, last_pub_file), os.path.join(new_ver_path, f"{seq_name}_{new_ver_num}_w001.{ext}"))
            
            # 새로운 wip 파일을 작업자 프로그램 별로 다른 프로그램 오픈
            if task in ["ly", "ani", "lgt"]:
                subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {new_ver_path}/{seq_name}_{new_ver_num}_w001.mb'],start_new_session=True)
            elif task == "fx":
                self.mX
            elif task in ["prc", "cmp"]:
                file_path = f"nuke {new_ver_path}/{seq_name}_{new_ver_num}_w001.nknc"
                self.run_nuke_nknc(file_path)

        else:
            self.msg_box("StatusError")

        self.set_listwidget()


    def refresh(self): # data 를 다시 가져오는 메서드 ( 새로고침 )
        self.clear_ui()
        self.reload_data()

    def clear_ui(self): # refresh 때 ui 비우는 메서드
        self.tree.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.ui.listWidget.clear()

    def reload_data(self): # refresh 때 다시 데이터를 가져오는 메서드
        self.get_task_data()
        self.set_treewidget()
    

    # qkrwntjr1@#
    # 에러 메세지
    def msg_box(self, message_type): # 에러 메세지 띄우는 함수..
    
        if message_type == "WipStatusError":
            QMessageBox.critical(self, "Error", "이미 작업 중입니다.", QMessageBox.Yes)
        if message_type == "StatusError":
            QMessageBox.critical(self, "Error", "Retake 상태가 아닙니다. Status를 확인해주세요.", QMessageBox.Yes)
        if message_type == "NoFile":
            QMessageBox.critical(self, "Error", "파일이 없습니다.", QMessageBox.Yes)
        if message_type == "NoPath":
            QMessageBox.critical(self, "Error", "경로가 생성 되지 않았습니다. New Scene 먼저 해주세요", QMessageBox.Yes)
        if message_type == "FX":
            QMessageBox.critical(self, "FX", "hip 파일 작업 예정입니다.",QMessageBox.Yes)


 

    
if __name__=="__main__": 
    app = QApplication(sys.argv)
    win = ShotLoader()
    win.show()
    app.exec() 