import sys
import os
import subprocess
import re
import shutil
from functools import partial
from configparser import ConfigParser
from PySide6.QtWidgets import QWidget,QApplication,QTreeWidgetItem
from PySide6.QtWidgets import QTableWidgetItem,QMenu,QWidgetAction
from PySide6.QtWidgets import QPushButton,QTableWidget,QMessageBox
from PySide6.QtWidgets import QLabel,QGridLayout

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QEvent,QPoint
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices,QPixmap
from shotgun_api3 import shotgun
from datetime import datetime
from pprint import pprint

class AssetLoader(QWidget):

    def __init__(self, user_id):
        super().__init__()

        self.installEventFilter(self)
        self.connect_sg()

        self.user_id = user_id
        self.get_assgined_user_project_by_task()

        self.make_ui()
        self._event_col()

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/loader.ui"

        ui_file = QFile(ui_file_path) 
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)

        self.table = self.ui.findChild(QTableWidget, "tableWidget")
        self.initialize_table_data()
        self.set_tree_widget() # 변경되지 않기 때문에 set을 사용했다.
        self.make_list_widget()


    def initialize_table_data(self): # 하드코딩할때 처음에 데이터를 넘겨주어야해서 적은 함수 # 다른 좋은 방안 있으면 추천 부탁.
        row_idx = 0
        for project, tasks in self.datas.items():
            for field in tasks:
                self.make_table_hard_coding(field, row_idx)
                row_idx += 1        

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
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellPressed.connect(self.get_index)
        self.table.cellPressed.connect(self.update_list_widget_items)
        self.list.itemDoubleClicked.connect(self.double_click_listWidget)
        
    def eventFilter(self,obj,event):  # event.type()이 close 일때 close Event 함수를 발동시켜 status ini를 저장하는 함수
        if event.type() == QEvent.Close and obj is self:
            self.save_status(self.last_file_path)
            return True
        return super().eventFilter(obj,event)
    
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
            result_path = ""
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

    def set_tree_widget(self): # 트리위젯을 데이터를 가져와 만드는 함수 # 같은종류의 asset일 경우 중첩되는 폴더를 삭제하기 위해 조건을 한번 걸었다.
        self.tree = self.ui.treeWidget
        self.tree.setHeaderLabel("Projects Name")
        tree_widget_dict = {}
        for project,tasks in self.datas.items():
            project_item = QTreeWidgetItem(self.tree,[project])
            tree_widget_dict[project] = {}
            for task in tasks:
                asset_type =  task["asset_data"]["sg_asset_type"]
                asset_name = task["asset_data"]["code"]
                
                # 파일타입 데이터는 겹치기 때문에 중복된 값을 없애기 위해 value에 set 이라는 집합을 사용했다 -> 중복데이터 삭제.
                
                # project 딕셔너리안에 asset_type이 없으면 실행
                if asset_type not in tree_widget_dict[project]:
                    asset_type_item = QTreeWidgetItem(project_item, [asset_type])
                    tree_widget_dict[project][asset_type] = set()                       # asset_type에 대한 빈 집합 초기화
                    
                    
                # asset_name 이 asset_type 집합에 없으면 실행
                if asset_name not in tree_widget_dict[project][asset_type]:
                    asset_name_item = QTreeWidgetItem(asset_type_item, [asset_name])
                    tree_widget_dict[project][asset_type].add(asset_name)               # asset_name을 집합에 추가        

    def make_list_widget(self):
        self.list = self.ui.listWidget
        self.list.clear()

    def update_table_items(self,item: QTreeWidgetItem): # 리스트위젯을 클릭할때 위젯에 아이템을 업데이트하는 메써드
        self.list.clear()
        self.initialize_table()
        parent = item.parent()
        row_idx = 0

        if not parent:                                                      # 프로젝트를 클릭 했을때 
            for project,tasks in self.datas.items():
                if item.text(0) == project:                                 # Moomins
                    for field in tasks:                                     
                        self.project = item.text(0)
                        self.make_table_hard_coding(field,row_idx)
                        row_idx += 1
                    break
        else:                                                                               # asset_type 이나 asset_name을 클릭 했을 때                           
            for project,tasks in self.datas.items():
                for field in tasks:                                                         # for문이 돌때마나 row_idx가 는다.   
                    asset_type = field["asset_data"]["sg_asset_type"]
                    asset_name = field["asset_data"]["code"]
                    if parent.text(0) == project and item.text(0) == asset_type:            # asset_type을 눌렀을 때.
                        
                        self.project = parent.text(0)   
                        print(self.project)
                        print(field)
                        self.make_table_hard_coding(field,row_idx)
                        row_idx += 1

                    elif parent.text(0) == asset_type and item.text(0) == asset_name:
                            self.project = parent.parent().text(0)
                            print(self.project)
                            print(field)
                            self.make_table_hard_coding(field,row_idx)
                            row_idx += 1

    def find_file_version(self):    # 파일버전을 찾는 함수.

        version = "v001"
        for check_project,tasks in self.datas.items(): # 클릭한 프로젝트를 가져오기위해 매개변수를 사용했다.
            if self.project == check_project:            
                for field in tasks:
                    task = field["step"]["name"].lower()
                    asset_name = field["asset_data"]["code"]
                    asset_type = field["asset_data"]["sg_asset_type"]
        
        path = f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scene/{version}"
        if not os.path.exists(path):                                                                                # 경로가 없으면 v001로 가져온다.
            return version
        version_folders = os.listdir(f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scene")  # v001의 폴더가 있으면 그 폴더로 가서 마지막 버전을 가져온다.
        version = sorted(version_folders)[-1] # v004
        
        
        return version

    def update_list_widget_items(self):                # tablewidget을 클릭했을시 리스트 위젯에 업데이트 되는 함수

        self.list.clear()
        for project,field in self.datas.items(): 
            if self.project == project:
                asset_type = self.label_asset_type.text()
                version = self.label_version.text()
                asset_name = self.label_asset_name.text()
                task = self.label_task.text().lower()
                path = f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"
                if not os.path.exists(path):
                    self.list.addItem("Empty")
                    return
                files = sorted(os.listdir(path))
                
                for file in files:
                    self.list.addItem(file)

                self.current_path = path                                 # 더블클릭시 가져올 패스

    def double_click_listWidget(self,item):                 # 더블클릭시 파일 이름을 가져와야하기때문에 item을 매개변수로 가져온다.
        if hasattr(self, 'current_path'):                   # self 객체에 current_path 라는게 있는지 확인하는 메쏘드
            file_name = item.text()
            file_path = os.path.join(self.current_path, file_name)
            command = ["maya",file_path]
            try:
                # subprocess.Popen을 사용하여 Maya 실행
                process = subprocess.Popen(command)
                process.wait()
            except Exception as e:
                print(f"마야 실행 오류 : {e}")

    def show_context_menu(self, pos : QPoint): # 우클릭시 PushButton을 생성하고각 PushButton을 누를시 실행되는 함수를 연결 시키는 함수, 클릭한 row의 index를 return 해준다
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
        
        retake_button = QPushButton("Retake")
        retake_button.clicked.connect(self.retake_for_version_up)
        retake_action = QWidgetAction(self)
        retake_action.setDefaultWidget(retake_button)

        # QAction을 컨텍스트 메뉴에 추가
        context_menu.addAction(new_scene_action)
        context_menu.addAction(version_up_action)
        context_menu.addAction(sg_site_action)
        context_menu.addAction(my_path_action)
        context_menu.addAction(retake_action)

 
        # 우클릭시 화면에 표시할수 있게 하는 코드
        context_menu.exec(self.table.viewport().mapToGlobal(pos))  #g선생

    def get_index(self,row,_):      # 선택한 셀의 row를 가져오기위해 만든함수
        self.row = row

    def click_right_button_import_data(self): # 우클릭시 그 포지션에따라 인덱스를 가져오고 그 인덱스에 해당하는 정보의 리스트를 리턴한다.
        for project,field in self.datas.items(): 
            if self.project == project:
                
                asset_type = self.label_asset_type.text()
                version = self.label_version.text()
                asset_name = self.label_asset_name.text()
                task = self.label_task.text().lower()
                path = f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"
                click_list = [asset_type,version,asset_name,task,path]
                return click_list
        return None

    def import_new_scene(self): # 파일이 없으면 새로운 마야 파일을 열어주는 시스템

        right_click_info = self.click_right_button_import_data()      # 우클릭한 정보를 가져오고
        if not right_click_info:                        
            return
        asset_type,version,asset_name,task,path = right_click_info  # path = scene까지 포함되어있다.
        base_path = path.replace(f"/scene/{version}","")                     # 파일을 생성할때는 폴더가 생성되어있지 않기때문에 scene을 지워서 다시 만들어준다. # 처음부터 scene을 없앴어야했나?...
        
        common_list = ["cache","images","scenes","source_images"]   
        file_name = f"{asset_name}_{version}_w001.mb"
        empty_file_path = "/home/rapa/.emptymaya.mb"


        for common_item in common_list:
            create_path = f"{base_path}/{common_item}"
            pub_path = create_path.replace("wip","pub")
            
            os.makedirs(create_path, exist_ok=True)
            os.makedirs(pub_path, exist_ok=True)
            
            if common_item == "scenes":
                version_path = f"{create_path}/{version}"
                os.makedirs(version_path, exist_ok=True)
                add_file_path = os.path.join(version_path, file_name)
                shutil.copy2(empty_file_path,add_file_path) # version_path에 emptyfile을 복사해 파일이름을 작성된 파일을 복사하는 코드
                
        subprocess.Popen(['maya', add_file_path])

    def save_wip_version_up(self): # 마지막 wip버전을 버전업해서 파일을 복사하는 함수
        last_file_name,version_up_name,path = self.make_version_up_filename()
        if not last_file_name:
            return
        last_file_path = f"{path}/{last_file_name}"
        version_up_file_path = f"{path}/{version_up_name}"
        shutil.copy2(last_file_path,version_up_file_path)

    def make_version_up_filename(self):    # version_up_name 을 만들기위해 쓴 함수 

        right_click_info = self.click_right_button_import_data()
        if not right_click_info:
            return None
        
        asset_type,_version,asset_name,task,path = right_click_info     # 우클릭한 파일의 정보들을 가져온다.
        if not os.path.exists(path):
            return None
        last_version_file = sorted(os.listdir(path))[-1]                # test_v001_w002.mb
        p = re.compile("[w]\d{2,4}")                                    # w로 시작하고 뒤에 숫자 2~4자리를 찾는다.
        p_data = p.search(last_version_file)                            # file_name 에 패턴이 있는지.
        if p_data:
            wip_version = p_data.group()                                # ex) w002
            version = wip_version[1:]                                   # ex) 002
            version_up = int(version) + 1
            wip_version_up = "w%03d" % version_up                       # ex) 3 > w003
            update_version_file_name = last_version_file.replace(wip_version,wip_version_up)
            
            return last_version_file,update_version_file_name,path

    def enter_Sg_site(self): # url에 접속하는 함수
        url = "https://4thacademy.shotgrid.autodesk.com/" 
        QDesktopServices.openUrl(QUrl(url))

    def enter_my_path(self): # subprocess에 명령어를 보내 path에 있는 경로를 여는 함수
        right_click_info = self.click_right_button_import_data() 
        if not right_click_info:
            return
        asset_type,version,asset_name,task,path = right_click_info
        real_path = os.path.realpath(path) # 실제 경로가 있는지 확인하는 습관이 있으면 좋다고 합니다.
        os.path.exists(real_path)
        # /home/rapa/wip/Marvelous/asset/Character/dami/modeling/wip/scenes/v001
        # /home/rapa/wip/Marvelous/asset/Character/dami/modeling/wip/scene/v001

        if os.path.exists(real_path):
            subprocess.run(['xdg-open', real_path])
        else:
            self.msg_box("Path_Error")

    def retake_for_version_up(self):

        status = self.table.item(self.row,3).text()
        if not status == "re":                  # retake 상태가 아니면 에러메세지 띄운다.
            self.msg_box("Status_Error")
            return
        
        right_click_info = self.click_right_button_import_data()
        if not right_click_info:                    # 우클릭한 정보가 없으면
            return None
        asset_type,version,asset_name,task,path = right_click_info     # 우클릭한 파일의 정보들을 가져온다.
        # path = f"/home/rapa/wip/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scene/{version}"
        
        if not os.path.exists(path):                # 정보에 path가 없으면
            return None
        
        pub_path = path.replace("wip","pub")
        # path = f"/home/rapa/pub/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/pub/scene/{version}"  # 여기는 pub된 v003의 폴더안에 v003파일이있다.
        full_file_name = os.listdir(pub_path)[0]                                                                      # 패스안의 파일이름을 가져온다. teapot_v003.mb
        
        # pub_file_path = f"/home/rapa/pub/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/pub/scene/{version}/{full_file_name}"
        
        
        file_name,ext = full_file_name.splitext()                                                                  
        # teapot_v003 , .mb
        version_path = pub_path.replace(f"/{version}","")
        # path = f"/home/rapa/pub/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/pub/scene             # 새로운 버전의 폴더를 만들기 위해 replace 했다.
        last_version_folder = sorted(os.listdir(version_path))[-1]                                                   # 정렬해서 폴더를 가져왔는데 굳이 해야하나 싶긴 하다.
        # ex) v003               
        version = last_version_folder[1:]     
        # ex) 003
        version_up = int(version) + 1
        # ex) 4
        pub_version_up = "v%03d" % version_up 
        # ex) v004
        file_name = file_name.replace(last_version_folder,pub_version_up) 
        # ex) teapot_v003 > teapot_v004
        new_file_name = f"{file_name}_w001{ext}"
        # ex) teapot_v004_w001.mb
        version_up_pub_path = f"/home/rapa/pub/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/pub/scene/{pub_version_up}"
        version_up_wip_path = version_up_pub_path.replace("pub","wip")
        # os.makedirs(version_up_pub_path,exist_ok=True)
        os.makedirs(version_up_wip_path,exist_ok=True)
        pub_file_path = f"{pub_path}/{full_file_name}"
        copy_wip_path = f"{version_up_wip_path}/{new_file_name}"
        # copy_wip_path = f"/home/rapa/wip/{self.self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scene/{pub_version_up}/{new_file_name}
        shutil.copy2(pub_file_path,copy_wip_path)

    def msg_box(self,message_type):

        if message_type == "Path_Error":
            QMessageBox.critical(self, "Error", "경로가 없습니다. New scene을 눌러 작업을 시작해주세요.", QMessageBox.Yes)
        if message_type == "Status_Error":
            QMessageBox.critical(self, "Error", "Retake 상태가 아닙니다. Status를 확인해주세요.", QMessageBox.Yes)




    def get_user_datas(self): # 로그인된 유저의 데이터를 가져오는 함수  
        print(self.user_id)
        filters = [["id", "is", self.user_id]]
        fields = ["name", "id","projects"]
                                # entity # 조건에맞는 사람의 # 이 필드들을 가져와라.    
        user_datas = self.sg.find_one("HumanUser", filters=filters, fields=fields)
        if isinstance(user_datas, dict):
            return user_datas

    def get_project_name(self): # login된 사람이 포함된 project를 가져오는 함수

        user_datas = self.get_user_datas()
        project_name_list = []           # 이름 담는 리스트
        project_id_list = []        # 프로젝트 id를 담는 리스트
        if not user_datas:
            return
        for key,values in user_datas.items():
            if key == "projects":
                for value in values:    
                    project_name_list.append(value["name"]) # ["Marvelous","Moomins"]
                    project_id_list.append(value["id"])     # [122,188]
        return project_name_list, project_id_list

    def get_tasks_from_project(self): # 프로젝트별로 테스크의 모든 데이터를 가져오는 함수
        project_task = {}
        project_name_list,project_id_list = self.get_project_name()
        
        for self.project,project_id in zip(project_name_list,project_id_list):          # zip 이라는 모듈은 이게 짝짝쿵을 맞춰준다.
            filters = [["project", "is", {"type": "Project", "id": project_id}]]        # 프로젝트들 [122,188]
            fields = ["content", "entity","task_assignees"]                             # 필드들을 가져와라.
            tasks_data = self.sg.find("Task",filters=filters , fields=fields)
            project_task[self.project] = tasks_data

        return project_task

    def get_assgined_user_project_by_task(self):        # 프로젝트 별 assign된 task를 가져오는 함수

        project_task = self.get_tasks_from_project()    # 프로젝트 별 데이터가 가져온다.
        user_data = self.get_user_datas()               # user 데이터만 가져오기때문에 비교하려고 가져왔음
        user_id = user_data["id"]                       # [105]
        assign_user_project_by_task = {}                # assign 된 데이터를 저장하기 위한 딕셔너리 # 쓰다보니 여러곳에서 사용해서 전역변수로 사용했다. # 나중에 datas라고 선언했음
            # mar,moo # tasks
        for project,tasks in project_task.items():
            assign_user_project_by_task[project] = []

            for task in tasks:
                if not task.get("task_assignees"):
                    continue

                assign_task = task["task_assignees"][0]  # 리스트를 풀기위해 [0]을 붙혔다. # [다미 김] => "다미 김"
                assign_task_id = assign_task["id"]       # assign된 모든 테스크의 id를 가져온다. # ex) task_assignees': [{'id': 105, 'name': '다미김', 'type': 'HumanUser'}

                if user_id == assign_task_id:            # user에 할당된 테스크와 id가 같을때 
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

    def get_assets_data(self,asset_id): # 할당된 데이터중 asset_id를 받아 assets의 데이터를 찾는 함수

        filters = [["id", "is", asset_id]]
        fields = ["code","sg_asset_type"] 
        if asset_id:
            assets_datas = self.sg.find_one("Asset",filters=filters,fields=fields)
        if isinstance(assets_datas, dict):
            return assets_datas

    def initialize_table(self):    # 버튼 누를때마다 초기화 되는 함수

        self.ui.tableWidget.setRowCount(0)
        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)

    def make_table_hard_coding(self,field,row_idx):
        """
        하드 코딩으로 ui 만들기...!
        """


        if row_idx >= self.table.rowCount():
            self.table.insertRow(row_idx)
            
            
        
        # 가져온 필드들 정리
        start_date = field["start_date"]
        due_date = field["due_date"]
        
        if start_date is None:
            start_date = "2099-99-99"
        if due_date is None:
            due_date = "99-99"
        due_date = due_date[-5:]
        task = field["step"]["name"].lower()
        asset_name = field["asset_data"]["code"]
        asset_type = field["asset_data"]["sg_asset_type"]
        date_range = f"{start_date}~{due_date}"
        version = self.find_file_version()                                             
        current_status = field["sg_status_list"]                                              
        file_type = "mb"          
        
        #   하드코딩....
        
        label_icon_image = QLabel()
        if file_type == "mb":
            image_path = "/home/rapa/test_image/mayaicon.png"
        elif file_type == "nk" or file_type == "nknc":
            image_path = "/home/rapa/test_image/nukeicon.png"
        else:
            image_path = "/home/rapa/test_image/houdiniicon.png"
            
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(50, 50)
        label_icon_image.setPixmap(scaled_pixmap)
        label_icon_image.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_icon_image.setFixedSize(80,70)

        self.label_asset_name = QLabel()
        self.label_asset_name.setText(asset_name)
        self.label_asset_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_asset_name.setObjectName("asset_name")
        self.label_asset_name.setStyleSheet("font-size: 17px;")
        self.label_asset_name.setFixedSize(90, 30)


        self.label_status = QLabel()
        self.label_status.setText(current_status)
        self.label_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_status.setObjectName("status")
        self.label_status.setStyleSheet("font-size: 17px;")
        self.label_status.setFixedSize(100, 30)       
        
        self.label_version = QLabel()
        self.label_version.setText(version)
        self.label_version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_version.setObjectName("version")
        self.label_version.setStyleSheet("font-size: 17px;")
        self.label_version.setFixedSize(100, 30)
        
        self.label_date_range = QLabel()
        self.label_date_range.setText(date_range)
        self.label_date_range.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_date_range.setObjectName("date_range")
        self.label_date_range.setStyleSheet("font-size: 13px;")
        self.label_date_range.setFixedSize(250, 30)


        
        
        self.label_asset_type = QLabel()
        self.label_asset_type.setText(asset_type)
        self.label_asset_type.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_asset_type.setObjectName("asset_type")
        self.label_asset_type.setStyleSheet("font-size: 17px;")
        self.label_asset_type.setFixedSize(90, 30)       
        
        
        self.label_task = QLabel()
        self.label_task.setText(task)
        self.label_task.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_task.setObjectName("task")
        self.label_task.setStyleSheet("font-size: 17px;")
        self.label_task.setFixedSize(100, 30)       
        
        
        grid_layout = QGridLayout()
        
        
        grid_layout.addWidget(label_icon_image, 0, 0)
        grid_layout.addWidget(self.label_asset_name, 0, 1)
        grid_layout.addWidget(self.label_status, 0, 2)
        grid_layout.addWidget(self.label_version, 0, 3)
        grid_layout.addWidget(self.label_date_range, 1, 2)
        grid_layout.addWidget(self.label_asset_type, 1, 1)
        grid_layout.addWidget(self.label_task, 1, 3)

        container_widget = QWidget()
        container_widget.setLayout(grid_layout)

        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget)
        
        self.table.setRowHeight(row_idx, 70)
        self.table.setColumnWidth(row_idx, 450)







if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AssetLoader()
    win.show()
    app.exec()