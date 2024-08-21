# 박주석 asset loader
import sys
import os
import subprocess
import re
import shutil
from configparser import ConfigParser
from PySide6.QtWidgets import QWidget,QApplication,QTreeWidgetItem
from PySide6.QtWidgets import QTableWidgetItem,QMenu,QWidgetAction
from PySide6.QtWidgets import QPushButton

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QEvent,QPoint
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices
from shotgun_api3 import shotgun
from datetime import datetime
from pprint import pprint


class AssetLoader(QWidget):

    def __init__(self, user_id):
        super().__init__()
        # print("에셋 로더 연결")

        self.installEventFilter(self)
        self.connect_sg()

        self.user_id = user_id # login.py에서 user_id를 받아서 전역 변수로 선언
        self.get_user_datas()
        self.get_assgined_user_project_by_task()

        self.make_ui()
        self._event_col()

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/asset_loader.ui"

        ui_file = QFile(ui_file_path) 
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)

        self.make_treewidget()
        self.make_tablewidget()

    def connect_sg(self): # 샷그리드를 연결하는 메쏘드

        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"
    
        self.sg = shotgun.Shotgun(URL,
                                SCRIPT_NAME,
                                API_KEY)
        
    def _event_col(self): # 여러 이벤트들을 모은 메써드
        self.tree.itemClicked.connect(self.item_clicked)
        self.tree.itemClicked.connect(self.update_table_items)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.set_context_menu)
        
    def eventFilter(self,obj,event):  # event.type()이 close 일때 close Event 함수를 발동시켜 status ini를 저장하는 함수
        if event.type() == QEvent.Close and obj is self:
            self.closeEvent(event)

    def closeEvent(self,event): # 마지막 파일 경로를 save_status함수에 넣어 ini파일에 저장한다.
        self.save_status(self.last_file_path)
        event.accept()
        
    def save_status(self,path): # ini파일로 저장하는 함수.(json은 무거우기때문에)
        config = ConfigParser()
        ini_file_path = "/home/rapa/Moomins/status.ini"
        close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if path : 
            result_path = " > ".join(path)
        else:
            return ""
        config["Status"] = {
            '마지막 작업 경로': result_path,
            '종료 한 날짜': close_time
        }
        os.makedirs(os.path.dirname(ini_file_path), exist_ok=True)
        with open(ini_file_path,"w") as file:
            config.write(file)
                
    def item_clicked(self,item): # treewidget에서 클릭할때마다 아이템을 가져와 재귀함수를 돌려 save_status함수에 path를 보내준다.
        self.last_file_path = self.get_item_path(item)
        self.save_status(self.last_file_path)
        
    def get_item_path(self,item): # 아이템 찾는 재귀 함수
        path = []
        while item:
            path.insert(0, item.text(0))
            item = item.parent()
        return path
        
    def make_treewidget(self): # 트리위젯을 데이터를 가져와 만드는 함수 # 같은종류의 asset일 경우 중첩되는 폴더를 삭제하기 위해 조건을 한번 걸었다.
        self.tree = self.ui.treeWidget
        self.tree.setHeaderLabel("Projects Name")
        asset_type_items = {}
        for project,tasks in self.datas.items():
            project_item = QTreeWidgetItem(self.tree,[project])
            for task in tasks:
                data = task["asset_data"]
                asset_type =  data["sg_asset_type"]
                asset_name = data["code"]
                if asset_type not in asset_type_items:
                    asset_type_item = QTreeWidgetItem(project_item, [asset_type])
                    asset_type_items[asset_type] = asset_type_item
                else:
                    asset_type_item = asset_type_items[asset_type]
                    
                asset_name_item = QTreeWidgetItem(asset_type_item, [asset_name])
                
    def make_tablewidget(self): # 테이블 위젯에 데이터를 가져와 만드는 함수
        self.table = self.ui.tableWidget
        self.table_header_list = ["AssetType","Version","AssetName","Status","Task","FileType","Date"]
        self.table.setColumnCount(len(self.table_header_list))
        self.table.setHorizontalHeaderLabels(self.table_header_list)
        self.table.setRowCount(0)
        self.table.setColumnWidth(5,80)
        header = self.table.horizontalHeader()              # 테이블 헤더 정리 코드
        header.setStretchLastSection(True)
    
    def update_table_items(self,item): # 리스트위젯을 클릭할때 테이블위젯이 업데이트 되는 메써드
        self.table.clear()                                              # set만하면 누를때 1,2,3 >>> 바뀌어서 계속 세팅을 해주어야 한다.
        self.table.setRowCount(0)
        self.table.setColumnCount(len(self.table_header_list))
        self.table.setHorizontalHeaderLabels(self.table_header_list)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        parent = item.parent()
        row_idx = 0
        # print(self.datas)
        if not parent:                  # 프로젝트를 클릭 했을때 
            for project,tasks in self.datas.items():
                if item.text(0) == project:
                    for field in tasks: # for문이 돌때마나 row_idx가 는다.
                        task = field["step"]["name"]
                        asset_name = field["asset_data"]["code"]
                        asset_type = field["asset_data"]["sg_asset_type"]
                        date_range = field["start_date"] + " ~ " + field["due_date"]
                        version = "v001"                                                    # 파일버전을 가져오는 식이 필요함 
                        current_status = field["sg_status_list"]                            # Status를 가져와야함
                        file_type = ".mb"                                                   # 파일의 마지막 확장자 가져오는 식이 필요함

                        self.table.insertRow(row_idx)
                        self.table.setItem(row_idx, 0, QTableWidgetItem(asset_type))
                        self.table.setItem(row_idx, 1, QTableWidgetItem(version))
                        self.table.setItem(row_idx, 2, QTableWidgetItem(asset_name))
                        self.table.setItem(row_idx, 3, QTableWidgetItem(current_status))
                        self.table.setItem(row_idx, 4, QTableWidgetItem(task))
                        self.table.setItem(row_idx, 5, QTableWidgetItem(file_type))
                        self.table.setItem(row_idx, 6, QTableWidgetItem(date_range))

                        row_idx += 1

        else:                                          # asset_type 이나 asset_name을 클릭 했을 때                              
            for project,tasks in self.datas.items():
                for field in tasks:                                      # for문이 돌때마나 row_idx가 는다.
                    task = field["step"]["name"]
                    asset_name = field["asset_data"]["code"]
                    asset_type = field["asset_data"]["sg_asset_type"]
                    date_range = field["start_date"] + " ~ " + field["due_date"]
                    version = "v001"                                                        # 파일버전을 가져오는 식이 필요함 
                    current_status = field["sg_status_list"]                                # Status를 가져와야함
                    file_type = ".mb"                                  
                    if parent.text(0) == project and item.text(0) == asset_type:            # asset_type을 눌렀을 때.
                        self.table.insertRow(row_idx)

                        self.table.setItem(row_idx, 0, QTableWidgetItem(asset_type))
                        self.table.setItem(row_idx, 1, QTableWidgetItem(version))
                        self.table.setItem(row_idx, 2, QTableWidgetItem(asset_name))
                        self.table.setItem(row_idx, 3, QTableWidgetItem(current_status))
                        self.table.setItem(row_idx, 4, QTableWidgetItem(task))
                        self.table.setItem(row_idx, 5, QTableWidgetItem(file_type))
                        self.table.setItem(row_idx, 6, QTableWidgetItem(date_range))
                        row_idx += 1

                    elif parent.text(0) == asset_type and item.text(0) == asset_name and parent.parent().text(0) == project:   # asset_name을 눌렀을때           # 오류발생시 해결 
                            self.table.insertRow(row_idx)
                                             
                            self.table.setItem(row_idx, 0, QTableWidgetItem(asset_type))
                            self.table.setItem(row_idx, 1, QTableWidgetItem(version))
                            self.table.setItem(row_idx, 2, QTableWidgetItem(asset_name))
                            self.table.setItem(row_idx, 3, QTableWidgetItem(current_status))
                            self.table.setItem(row_idx, 4, QTableWidgetItem(task))
                            self.table.setItem(row_idx, 5, QTableWidgetItem(file_type))
                            self.table.setItem(row_idx, 6, QTableWidgetItem(date_range))
                            row_idx += 1
                    
    def set_context_menu(self, pos : QPoint): # 우클릭시 PushButton을 생성하고각 PushButton을 누를시 실행되는 함수를 연결 시키는 함수
        context_menu = QMenu(self)

        new_scene_button = QPushButton("New Scene")
        new_scene_button.clicked.connect(self.import_new_scene)            
        new_scene_action = QWidgetAction(self)
        new_scene_action.setDefaultWidget(new_scene_button)
        
        
        version_up_button = QPushButton("Wip Version Up")
        version_up_button.clicked.connect(self.save_wip_version_up)
        version_up_action = QWidgetAction(self)
        version_up_action.setDefaultWidget(version_up_button)

        sg_site_button = QPushButton("Shotgun Site")
        sg_site_button.clicked.connect(self.enter_Sg_site)
        sg_site_action = QWidgetAction(self)
        sg_site_action.setDefaultWidget(sg_site_button)

        my_path_button = QPushButton("Current Path")
        my_path_button.clicked.connect(self.enter_my_path)
        my_path_action = QWidgetAction(self)
        my_path_action.setDefaultWidget(my_path_button)

        # QAction을 컨텍스트 메뉴에 추가
        context_menu.addAction(new_scene_action)
        context_menu.addAction(version_up_action)
        context_menu.addAction(sg_site_action)
        context_menu.addAction(my_path_action)

 
        # 우클릭시 화면에 표시할수 있게 하는 코드
        context_menu.exec_(self.table.viewport().mapToGlobal(pos))  #g선생
        
        
    def import_new_scene(self): # 파일이 없으면 새로운 마야 파일을 열어주는 시스템
        # 열리자마자 이름 세팅하는 함수가 필요함.
        # 빈 파일을 아무대나 저장해놓고 이름만 바꿔서 열리게 하면된다.
        # text.mb => 이름만바꿔서 복사한뒤 그걸 실행시켜라.
        # 폴더까지 해버려라.
        path = "/home/rapa/wip/Moomins/Moomins/wip/mod/test/scene"
        
        subprocess.Popen("maya", cwd=os.path.realpath(path))
        
    def save_wip_version_up(self): # 마지막 wip버전을 버전업해서 파일을 복사하는 함수
        last_file_name,version_up_name,path = self.make_version_up_filename()
        last_file_path = path + "/" + last_file_name
        version_up_file_path = path + "/" + version_up_name
        shutil.copy2(last_file_path,version_up_file_path)
        
    def enter_Sg_site(self): # url에 접속하는 함수
        url = "https://4thacademy.shotgrid.autodesk.com/" 
        QDesktopServices.openUrl(QUrl(url))
        
    def enter_my_path(self): # subprocess에 명령어를 보내 path에 있는 경로를 여는 함수
        
        path = "/home/rapa/Moomins/Moomins/wip/mod/test/scene"
        subprocess.run(['xdg-open', os.path.realpath(path)])  

        
    def make_version_up_filename(self): # version_up_name을 만들기위해 쓴 함수
        
        path = "/home/rapa/Moomins/Moomins/wip/mod/test/scene"
        last_version_file = sorted(os.listdir(path))[-1]    # test_v001_w002.mb
        p = re.compile("[w]\d{2,4}")                        # w로 시작하고 뒤에 숫자 2~4자리를 찾는다.
        p_data = p.search(last_version_file)                # file_name 에 패턴이 있는지.
        if p_data:
            wip_version = p_data.group()                    # ex) w002
            version = wip_version.split("w")[-1]            # ex) 002 # replace 왜 안되지 ...??
        version_up = int(version) + 1
        wip_version_up = "w%03d" % version_up                # ex) 3 > w003
        update_version_file_name = last_version_file.replace(wip_version,wip_version_up)
        
        return last_version_file,update_version_file_name,path




# Login에서 전달한 user_id 받아옴
    def get_user_datas(self): # 로그인된 유저의 데이터를 가져오는 함수  
        # print(self.user_id) # 121
        filters = [["id", "is", self.user_id]]
        fields = ["name", "id", "projects"]
        user_datas = self.sg.find_one("HumanUser", filters=filters, fields=fields)
        if isinstance(user_datas, dict):
            return user_datas

    def get_project_name(self): # login된 사람이 포함된 project를 가져오는 함수
        user_datas = self.get_user_datas()
        project_name_list = []           # 이름 담는 리스트
        project_id_list = []        # 프로젝트 id를 담는 리스트
        if not user_datas:
            return
        print(user_datas) # {'type': 'HumanUser', 'id': 121, 'name': 'hyoeun seol', 'projects': []}
        for key,values in user_datas.items():
            if key == "projects":
                for value in values:    
                    project_name_list.append(value["name"])     # ["Marvelous","Moomins"]
                    project_id_list.append(value["id"])    # [122,188]
        print("*******************************")
        print(project_name_list, project_id_list)
        return project_name_list,project_id_list

    def get_tasks_from_project(self): # 프로젝트별로 테스크의 모든 데이터를 가져오는 함수 # 개어렵다 진짜
        project_task = {}

        project_name_list,project_id_list = self.get_project_name()
        
        for project_name,project_id in zip(project_name_list,project_id_list):          # zip 이라는 모듈은 이게 짝짝쿵을 맞춰준다.
            filters = [["project", "is", {"type": "Project", "id": project_id}]]        # 프로젝트들 [122,188]
            fields = ["content", "entity","task_assignees"]                             # 필드들을 가져와라.
            tasks_data = self.sg.find("Task",filters=filters , fields=fields)
            project_task[project_name] = tasks_data

        return project_task

    def get_assgined_user_project_by_task(self):        # 프로젝트 별 assign된 task를 가져오는 함수

        project_task = self.get_tasks_from_project()    # 프로젝트 별 데이터가 가져온다.
        user_data = self.get_user_datas()               # user 데이터만 가져오기때문에 비교하려고 가져왔음
        self.user_id = user_data["id"]                       # [105]
        assign_user_project_by_task = {}                # assign 된 데이터를 저장하기 위한 딕셔너리 # 쓰다보니 여러곳에서 사용해서 전역변수로 사용했다. # 나중에 datas라고 선언했음
            # mar,moo # tasks
        for project,tasks in project_task.items():
            assign_user_project_by_task[project] = []
            
            for task in tasks:
                if not task.get("task_assignees"):
                    continue

                assign_task = task["task_assignees"][0]  # 리스트를 풀기위해 [0]을 붙혔다. # [다미 김] => "다미 김"
                assign_task_id = assign_task["id"]       # assign된 모든 테스크의 id를 가져온다. # ex) task_assignees': [{'id': 105, 'name': '다미김', 'type': 'HumanUser'}
                
                if self.user_id == assign_task_id:            # user에 할당된 테스크와 id가 같을때 
                    filters = [['id', "is", task["id"]]]
                    fields = ["step", "entity","start_date","due_date","sg_status_list"]
                    user_tasks_data = self.sg.find("Task",filters=filters , fields=fields)
                    for task_data in user_tasks_data:
                        asset_id = task_data["entity"]["id"]
                        asset_data = self.get_assets_data(asset_id)
                        task_data["asset_data"] = asset_data
                    if project not in assign_user_project_by_task:                  # 잘 모르겠음 code review 요망
                        assign_user_project_by_task[project] = []
                    assign_user_project_by_task[project].append(task_data)
                    
        self.datas = assign_user_project_by_task
                
    def get_assets_data(self, asset_id): # 할당된 데이터중 asset_id를 받아 assets의 데이터를 찾는 함수

        filters = [["id", "is", asset_id]]
        fields = ["code","sg_asset_type"] 
        if asset_id:
            assets_datas = self.sg.find_one("Asset",filters=filters,fields=fields)
        if isinstance(assets_datas, dict):
            return assets_datas

