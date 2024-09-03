# shot loader
import sys
import os
import shutil
import re
import webbrowser
import subprocess
from pprint import pprint
from shotgun_api3 import Shotgun

from PySide6.QtWidgets import QApplication, QWidget, QTreeWidgetItem
from PySide6.QtWidgets import QLabel, QMenu, QMessageBox
from PySide6.QtWidgets import QGridLayout, QTableWidgetItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap, QAction

class ShotLoader (QWidget): 

    def __init__(self):
        super().__init__()

        self.make_ui()
        self.connect_sg()
        self.get_task_data()
        self.set_treewidget()
        self.make_tablewidget()

        self.tree.itemClicked.connect(self.click_event) # 트리위젯 클릭 용
        self.table.cellClicked.connect(self.get_click_data) # 테이블위젯 클릭 용
        self.table.setContextMenuPolicy(Qt.CustomContextMenu) # 테이블위젯 우클릭 용
        self.table.customContextMenuRequested.connect(self.click_right_menu) # 테이블위젯 우클릭 용
        self.ui.listWidget.itemDoubleClicked.connect(self.double_clicked_item) # 리스트위젯 더블클릭 용
        self.ui.pushButton.clicked.connect(self.refresh)

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/loader.ui"
        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self) 
        ui_file.close() 


    """
    샷그리드 연결
    """
    def connect_sg(self): # 샷그리드 연결 메서드

        URL = "https://4thacademy.shotgrid.autodesk.com/"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"

        sg = Shotgun(URL, SCRIPT_NAME, API_KEY)

        return sg
    
    def get_user_data (self): # 유저 데이터 갖고오기

        sg = self.connect_sg()

        self.user_id = 94
        filters = [["id", "is", self.user_id]]
        fields = ["projects", "name"]
        user_datas = sg.find_one("HumanUser", filters=filters, fields=fields)
        user_name = user_datas["name"]
        
        return user_datas, user_name
    

    """
    테스크 정보 세팅
    """
    def get_task_data(self): # 할당된 테스크 정보 가져와서 딕셔너리로 정리

        sg = self.connect_sg()
        _, user_name = self.get_user_data()

        filters = [["task_assignees", "is", {'id': self.user_id, 'name': user_name, 'type': 'HumanUser'}]]
        fields = ["projects", "entity", "task_assignees", "step", "sg_status_list", "start_date", "due_date", "project"]
        self.task_data = sg.find("Task", filters=filters, fields=fields) # 리스트에 싸여진 딕셔너리들 데이터
        # print (self.task_data)

        # data 정리
        self.projects = {}
        for task in self.task_data:
            project_name = task["project"]["name"]                  # 프로젝트 이름 Moomins
            seq_name_part = task["entity"]["name"].split("_")[0]    # 시퀀스 이름만 나와 있는 부분 AFT
            seq = task["entity"]["name"]                            # 시퀀스 풀네임 AFT_0010
            part = task["step"]["name"]                             # 소속 파트 ani
            start_date = task["start_date"]                         # 시작 날짜 2024-09-03
            due_date = task["due_date"]                             # 마감 날짜 2024-09-11
            status = task["sg_status_list"]                         # 작업 상황 wtg

            # 버전 정리
                        # /home/rapa/wip/Moomins       /seq/AFT          /AFT_0010/ani/wip/scene/v001
            ver_path = f"/home/rapa/wip/{project_name}/seq/{seq_name_part}/{seq}/{part}/wip/scene"
            if not os.path.exists(ver_path):
                version = "v001"
            else:
                ver_folders = os.listdir(ver_path)
                if not ver_folders:
                    version = "v001"
                else:
                    version = sorted(ver_folders)[-1]
            

            # 데이터 딕셔너리로 정리
            if project_name not in self.projects:
                self.projects[project_name] = {}

            if seq not in self.projects[project_name]:
                self.projects[project_name][seq] = {}

            self.projects[project_name][seq]["part"] = part
            self.projects[project_name][seq]["start_date"] = start_date
            self.projects[project_name][seq]["due_date"] = due_date
            self.projects[project_name][seq]["status"] = status
            self.projects[project_name][seq]["version"] = version

        # pprint (self.projects)
    

    """
    트리 위젯 세팅
    """
    def set_treewidget(self): # 트리 위젯 채우기
        self.tree = self.ui.treeWidget
        self.tree.clear()
        # self.ui.listWidget.clear()

        # 프로젝트와 시퀀스 데이터 불러오기
        projects_dict = {} # {'Marvelous': ['hyo'], 'Moomins': ['STG', 'BRK', 'RST', 'RVL', 'FIN', 'AFT', 'KLL', 'MAD', 'MSK', 'OPN', 'TRS']}
        for self.task in self.task_data:
            project_name = self.task["project"]["name"] # 프로젝트 이름
            seqs_name_parts = self.task["entity"]["name"].split("_")[0] # 시퀀스 넘버를 뺀 이름 부분

            # 중복되는 프로젝트 제거
            if project_name not in projects_dict:
                projects_dict[project_name] = []
            
            # 중복되는 시퀀스 이름 제거
            if seqs_name_parts not in projects_dict[project_name]: 
                projects_dict[project_name].append(seqs_name_parts) 

        # 트리 위젯에 추가 
        for project, seq_name_parts in projects_dict.items():
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, project)

            for seq_name_part in sorted(seq_name_parts):
                seq_item = QTreeWidgetItem(project_item)
                seq_item.setText(0, seq_name_part)

    def click_event(self, item, column): # 트리 위젯에서 클릭했을 때 매치 되는 데이터 보내기
        """
        ############################## 여기 수정중이에여 작동 안 됨 주의 ######################################
        """
        self.table.clear()
        self.ui.listWidget.clear()

        select_item = item.text(column) # 트리에서 선택한 아이템

        matching_seq = {}
        seq_name_part = set()
        for project_name, seq_data in self.projects.items(): # 모든 프로젝트 이름과 시퀀스 데이터
            seqs = seq_data.keys() # 각 프로젝트의 시퀀스들 이름
            for seq_name in seqs: # 시퀀스들 중에 시퀀스 
                seq_name_parts = seq_name.split("_")[0]  # 시퀀스들 이름 파트만
                seq_name_part.add(seq_name_parts)# OPN
            print(seq_name_part)

            # print (seq_name_part) # {'MSK', 'BRK', 'END', 'KLL', 'FIN', 'OPN', 'STG', 'RST', 'AFT', 'TRS', 'hyo', 'MAD', 'RVL'}
                # if seq_name_part not in seq_name_parts:
                #     seq_name_parts.append(seq_name_part)
                #     print(seq_name_parts)

            # print (self.projects.items())

            # Project (Marvelous) 를 트리에서 클릭했을 때
            if select_item == project_name:
                matching_project = self.projects[select_item]
                if matching_project:
                    self.update_table_items(matching_project)
                    # print (matching_project)

            # # seq (AFT) 를 트리에서 클릭했을 때
            elif select_item == seq_data.keys() :
                for seq,seq_data in  self.projects[project_name].items():
                    if seq.split("_")[0] == select_item:
                        matching_seq[seq] = seq_data
                        # print (matching_seq) # {'AFT_0010': {'part': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 'wtg', 'version': 'v001'}}
                        if matching_seq:
                            self.update_table_items(matching_seq)

        # self.set_listwidget()

    """
    테이블 위젯 세팅
    """
    def make_tablewidget(self): # 테이블 위젯 기본 세팅
        self.table = self.ui.tableWidget
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 450)

    def update_table_items(self, matching_project=None, matching_seq=None): # task 양에 맞게 테이블에 row 추가

        if matching_project:
            tasks = matching_project
        elif matching_seq:
            tasks = matching_seq
        else:
            return  # 매칭되는 테스크가 없을 때
        
        self.table.setRowCount(len(tasks)) 
        row = 0
        for row, seq in enumerate(tasks):
            # print (tasks)
            self.make_table_hard_coding(row, tasks, seq)
            row += 1

    def make_table_hard_coding(self, row, tasks, seq): # 하드 코딩으로 테이블 만들기
        # print (row, tasks) 0 {'BRK_0010': {'part': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 're', 'version': 'v001'}}

        # 데이터 정리 {'BRK_0010': {'part': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 're', 'version': 'v001'}}
        part = tasks[seq]["part"]
        version = tasks[seq]["version"]
        start_date = tasks[seq]["start_date"]
        due_date = tasks[seq]["due_date"]
        date_range = f"{start_date} - {due_date}"
        status = tasks[seq]["status"]


        container_widget = QWidget() # 컨테이너 위젯 생성
        grid_layout = QGridLayout() # 그리드 레이아웃 생성
        container_widget.setLayout(grid_layout) # 컨테이너에 레이아웃 설정

        self.table.setRowHeight(row, 70) # 행 row 의 높이 조절

        self.table.setCellWidget(row, 0, container_widget) # 테이블 위젯에 컨테이너 추가

        # 프로그램 로고 사진 라벨 제작
        label_node_name1 = QLabel()
        if part in ["ly", "ani", "lgt"]:
            image_path = "/home/rapa/pipeline_0825/pipeline/sourceimages/maya.png"
        elif part == "fx":
            image_path = "/home/rapa/pipeline_0825/pipeline/sourceimages/houdini.png"
        elif part == "cmp":
            image_path = "/home/rapa/pipeline_0825/pipeline/sourceimages/nuke.png"
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(50, 50)
        label_node_name1.setPixmap(scaled_pixmap)
        label_node_name1.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_node_name1.setFixedSize(70, 70)

        # 시퀀스 이름 라벨 제작
        label_node_name2 = QLabel()
        label_node_name2.setText(seq)
        label_node_name2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_node_name2.setObjectName("seq_name")
        label_node_name2.setStyleSheet("font-size: 14px;")
        label_node_name2.setFixedSize(80, 20)

        # 버전 이름 라벨 제작
        label_node_name3 = QLabel()
        label_node_name3.setText(version)
        label_node_name3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_node_name3.setObjectName("version")
        label_node_name3.setStyleSheet("font-size: 14px;")
        label_node_name3.setFixedSize(50, 20)    
        
        # 유저 파트 라벨 제작
        label_node_name4 = QLabel()
        label_node_name4.setText(part)
        label_node_name4.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_node_name4.setObjectName("part")
        label_node_name4.setStyleSheet("font-size: 14px;")
        label_node_name4.setFixedSize(100, 20)   
        
        # 제작 기간 라벨 제작
        label_node_name5 = QLabel()
        label_node_name5.setText(date_range)
        label_node_name5.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_node_name5.setStyleSheet("font-size: 14px;")
        label_node_name5.setFixedSize(200, 20)

        # 작업 상태 라벨 제작
        label_node_name6 = QLabel()
        label_node_name6.setText(status)
        label_node_name6.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_node_name6.setStyleSheet("font-size: 14px;")
        label_node_name6.setFixedSize(100, 20)       
        
        # 레이아웃에 라벨 넣기
        grid_layout.addWidget(label_node_name1, 0, 0) # 프로그램 로고 사진
        grid_layout.addWidget(label_node_name2, 0, 1) # 시퀀스 이름
        grid_layout.addWidget(label_node_name3, 0, 2) # 버전 이름
        grid_layout.addWidget(label_node_name4, 0, 3) # 유저 파트
        grid_layout.addWidget(label_node_name5, 1, 1, 1, 2) # 제작 기간
        grid_layout.addWidget(label_node_name6, 1, 3) # 작업 상태 

    def get_click_data(self, row):
        self.click_row = row
        self.set_listwidget()


    """
    테이블 위젯에서 우클릭 했을 때의 이벤트들
    """
    
    def click_right_menu(self,pos): # 우클릭 띄우기
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


    def make_new_scene(self): # New Scene 눌렀을 때 파트별로 새 씬(w001)이 열리거나 이미 있다면 작업 중이라고 경고 창
        self.ui.listWidget.clear()

        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 맞추기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                version = data["version"]
                seq_name_part = seq.split("_")[0]

                # 매치된 데이터로 새로운 폴더 경로 만들기
                if table_seq == seq:
                    print ("true")
                    wip_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip"
                    ver_path = f"{wip_path}/scene/{version}"

                    # 경로 만들기
                    os.makedirs(ver_path, exist_ok=True) 
                    os.makedirs(f"{wip_path}/source/{version}", exist_ok=True)
                    os.makedirs(f"{wip_path}/cache/{version}", exist_ok=True)
                    os.makedirs(f"{wip_path}/images/{version}", exist_ok=True)
        
                    # 복사할 빈 씬 경로 
                    my_path = os.path.dirname(__file__)

                    # 파트별 프로그램 작업자 정리
                    maya_user = part in ["ly", "ani", "lgt"]
                    houdini_user = part == "fx"
                    nuke_user = part == "cmp"

                    # 마야 작업자의 경우, wip 파일 없으면 만들고 실행
                    if maya_user:
                        if not os.path.exists(f"{ver_path}/{seq}_{version}_w001.mb"):
                            shutil.copy(os.path.join(my_path, ".emptymaya.mb"), os.path.join(ver_path, ".emptymaya.mb")) # 빈 파일 복사
                            os.rename(f"{ver_path}/.emptymaya.mb", f"{ver_path}/{seq}_{version}_w001.mb") # 파일명 지정
                            os.system(f"shot_maya -file {ver_path}/{seq}_{version}_w001.mb") # 파일 실행
                            return
                        self.msg_box("WipStatusError")

                    # 후디니 작업자의 경우, wip 파일 없으면 만들고 실행
                    elif houdini_user:
                        if not os.path.exists(f"{ver_path}/{seq}_{version}_w001.hip"):
                            self.msg_box("FX")
                            return
                        self.msg_box("WipStatusError")

                    # 누크 작업자의 경우, wip 파일 없으면 만들고 실행
                    elif nuke_user:
                        print ("누크 작업자")
                        if not os.path.exists(f"{ver_path}/{seq}_{version}_w001.nknc"):
                            shutil.copy(os.path.join(my_path, ".emptynuke.nknc"), os.path.join(ver_path, ".emptynuke.nknc")) # 빈 파일 복사
                            os.rename(f"{ver_path}/.emptynuke.nknc", f"{ver_path}/{seq}_{version}_w001.nknc") # 파일명 지정
                            file_path = f"{ver_path}/{seq}_{version}_w001.nknc"
                            self.run_nuke_nknc(file_path)
                            return
                        self.msg_box("WipStatusError")
                    
                    else:
                        print ("작업자 아님")

            self.set_listwidget()

    def make_new_wip_version(self): # wip 파일 버전 업 / wip 파일이 아예 없다면 경고창 띄우기

        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 매치하기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                version = data["version"]
                seq_name_part = seq.split("_")[0]

                # wip 파일 경로 확인하기
                if table_seq == seq:
                    wip_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip"
                    ver_path = f"{wip_path}/scene/{version}"
                    if not os.path.exists(ver_path):
                        self.msg_box("NoFile")
                        return
                    # wip 파일 없으면 작업 전 알리는 경고창 띄우기
                    wip_files = os.listdir(ver_path)
                    if not wip_files:
                        self.msg_box("NoFile")
                        return
                    
                    # 파트별 프로그램 작업자와 확장명 정리
                    maya_user = part in ["ly", "ani", "lgt"]
                    houdini_user = part == "fx"
                    nuke_user = part == "cmp"

                    if maya_user:
                        ext = "mb"
                    elif houdini_user:
                        ext = "hip"
                    elif nuke_user:
                        ext = "nknc"
                    
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

        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 맞추기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                version = data["version"]
                seq_name_part = seq.split("_")[0]

                # 매치된 데이터로 경로 열기
                if table_seq == seq:
                    wip_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip"
                    ver_path = f"{wip_path}/scene/{version}"
                    if not os.path.exists (ver_path):
                        self.msg_box("NoPath")
                        return
                    subprocess.call(["xdg-open", ver_path]) # 리눅스 버전
                
    def version_up_for_retake(self): # pub 한 파일 retake 받았을 때 wip 에 새로운 ver 폴더와 wip 파일 생성되는 메서드
       
        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 매치하기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                version = data["version"]
                seq_name_part = seq.split("_")[0]
                status = data["status"]

                if table_seq == seq:
                    pub_path = f"/home/rapa/pub/{project}/seq/{seq_name_part}/{seq}/{part}/pub/scene/{version}"
                    wip_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip"
                    scene_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip/scene"
                    if status == "re":
                        pub_files = os.listdir(pub_path)
                        last_pub_file = sorted(pub_files)[-1]

                        # 파트별 프로그램 작업자 정리
                        maya_user = part in ["ly", "ani", "lgt"]
                        houdini_user = part == "fx"
                        nuke_user = part == "cmp"

                        if maya_user:
                            ext = "mb"
                        elif houdini_user:
                            ext = "hip"
                        elif nuke_user:
                            ext = "cmp"

                        # retake 받았을 때 pub 에 있는 파일을 버전을 높여주고 wip 폴더에 복사하기
                        match = re.search(rf'_v(\d+)\.{ext}', last_pub_file)
                        ver_num = int(match.group(1))
                        ver_up_num = ver_num + 1
                        new_ver_num = f"v{ver_up_num:03d}"
                        new_ver_path = f"{scene_path}/{new_ver_num}"
                        print (new_ver_path) # /home/rapa/wip/Moomins/seq/BRK/BRK_0010/ani/wip/scene/v006

                        os.makedirs(new_ver_path, exist_ok=True)    
                        os.makedirs(f"{wip_path}/source/{new_ver_num}", exist_ok=True)
                        os.makedirs(f"{wip_path}/cache/{new_ver_num}", exist_ok=True)
                        os.makedirs(f"{wip_path}/images/{new_ver_num}", exist_ok=True)


                        shutil.copy(os.path.join(pub_path, last_pub_file), os.path.join(new_ver_path, f"{seq}_{new_ver_num}_w001.{ext}"))
                        
                        # 새로운 wip 파일을 작업자 프로그램 별로 다른 프로그램 오픈
                        if maya_user:
                            os.system(f"shot_maya -file {new_ver_path}/{seq}_{new_ver_num}_w001.mb")
                        elif houdini_user:
                            self.mX
                        elif nuke_user:
                            file_path = f"nuke {new_ver_path}/{seq}_{new_ver_num}_w001.nknc"
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

        
    """
    리스트 위젯
    """                 
    def set_listwidget (self): # 리스트 위젯에 wip 파일 띄우기
        self.ui.listWidget.clear()

        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        if not widget :
            return
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 매치하기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                seq_name_part = seq.split("_")[0]
                version = data["version"]

                if table_seq == seq:
                    version_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip/scene/{version}"
                    if not os.path.exists(version_path):
                        self.ui.listWidget.addItem("No File")
                        return
                    wip_files = os.listdir(version_path)
                    if not wip_files:
                        self.ui.listWidget.addItem("No File")
                        return
                    for wip_file in wip_files:
                        self.ui.listWidget.addItem(wip_file)
                    
    def double_clicked_item(self,item):

        # 테이블 위젯에서 매치할 시퀀스 이름 가져오기 
        widget = self.table.cellWidget(self.click_row, 0)
        seq_label = widget.findChild(QLabel, "seq_name")
        table_seq = seq_label.text()

        # 데이터와 테이블 위젯에서 가져온 시퀀스 이름 매치하기
        for project, seqs in self.projects.items():
            for seq, data in seqs.items():
                part = data["part"]
                seq_name_part = seq.split("_")[0]
                version = data["version"]

                if table_seq == seq:
                    scene_path = f"/home/rapa/wip/{project}/seq/{seq_name_part}/{seq}/{part}/wip/scene/{version}"

                    file_name = item.text()
                    if file_name == "No File":
                        self.msg_box("NoFile")
                        return
                    file_path = f"{scene_path}/{file_name}"

                    # 파트별 프로그램 작업자 정리
                    maya_user = part in ["ly", "ani", "lgt"]
                    houdini_user = part == "fx"
                    nuke_user = part == "cmp"

                    if maya_user:
                        os.system(f"shot_maya -file {file_path}")
                    elif houdini_user:
                        self.mX
                    elif nuke_user:
                        os.system(f"nuke {file_path}")
                        self.run_nuke_nknc(file_path)

    def run_nuke_nknc(self, file_path):
        nuke_path = "source /home/rapa/env/nuke.env && /opt/Nuke/Nuke15.1v1/Nuke15.1 --nc"
        command = f"{nuke_path}'{file_path}'"
        subprocess.run (command, shell=True, check=True)

    """
    에러 메세지
    """
    def msg_box(self, message_type): # 알림 메세지 띄우는 함수..
    
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