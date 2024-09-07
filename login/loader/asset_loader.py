import sys
import os
import subprocess
import re
import shutil
import time
import threading
from configparser import ConfigParser
from PySide6.QtWidgets import QWidget,QApplication,QTreeWidgetItem
from PySide6.QtWidgets import QMenu,QWidgetAction,QGridLayout
from PySide6.QtWidgets import QPushButton,QTableWidget,QMessageBox
from PySide6.QtWidgets import QLabel

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QEvent,QPoint
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices,QPixmap,QGuiApplication
from datetime import datetime
from pprint import pprint

sys.path.append("/home/rapa/git/pipeline/api_scripts")

from shotgun_api import ShotgunApi

class AssetLoader(QWidget):

    def __init__(self, user_id):
        
        super().__init__()
        
        self.user_id = user_id
        
        self.sg_cls = ShotgunApi()

        self.get_assgined_user_project_by_task()
        self.installEventFilter(self)
        self.make_ui()
        self.import_ini_file()
        self._event_col()



    def make_ui(self): # ui 만드는 함수들을 모은 함수.
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/loader.ui"
        ui_file = QFile(ui_file_path) 
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.table = self.ui.findChild(QTableWidget, "tableWidget")
        self.initialize_table_data()
        self.set_tree_widget()                  # 변경되지 않기때문에 set을 사용했다.
        self.make_list_widget() 
        self.make_ui_center()

    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_assgined_user_project_by_task(self):
        """
        aseet data 정리
        """
        user_tasks_data = self.sg_cls.get_task_data(self.user_id)

        assign_user_project_by_task = {}                # assign 된 데이터를 저장하기 위한 딕셔너리 # 쓰다보니 여러곳에서 사용해서 전역변수로 사용했다. # 나중에 datas라고 선언했음
        # print (user_tasks_data)
        # print(user_tasks_data)
        for task_data in user_tasks_data:

            asset_id = task_data["entity"]["id"]
            asset_data = self.sg_cls.get_assets_data(asset_id)
            task_data["asset_data"] = asset_data
            project = task_data["project"]["name"]
        
            if project not in assign_user_project_by_task:  # 프로젝트가 저장된 딕셔너리 안에 없으면 새로운 리스트를 만든다.
                assign_user_project_by_task[project] = []
        
            assign_user_project_by_task[project].append(task_data)
        pprint(assign_user_project_by_task)
            # pprint (assign_user_project_by_task)

        self.assign_datas = assign_user_project_by_task
        # print (self.assign_datas)
    
            # {'Moomins': [{'asset_data': {'code': 'car',
            #                          'id': 1479,
            #                          'sg_asset_type': 'prop',
            #                          'type': 'Asset'},
            #           'due_date': '2024-08-11',
            #           'entity': {'id': 1479, 'name': 'car', 'type': 'Asset'},
            #           'id': 6195,
            #           'sg_status_list': 'wip',
            #           'start_date': '2024-08-10',
            #           'step': {'id': 16, 'name': 'lkd', 'type': 'Step'},
            #           'type': 'Task'},




    def import_ini_file(self):
        ini_file_path =  os.path.dirname(__file__) +"/status.ini"
        config = ConfigParser()
        config.optionxform = str
        
        config.read(ini_file_path,encoding='utf-8')
        last_click_path = config["Status"]["lastworkpath"]
        close_time = config["Status"]["closetime"]
        click_path = last_click_path.split(" > ")
        # ["Moomins", "Character", "bat"]
        
        current_item = self.tree.invisibleRootItem()        # 최상위 경로
        
        # 아래의 식은 최상위 경로에서부터 click_path 에 있는 순서대로 자식들을 찾아가는 식이다.
        
        for text in click_path:
            item = self.find_item_in_tree(current_item, text)
            if item:
                self.tree.expandItem(item)  # 항목을 확장
                current_item = item
            else:
                return
        if current_item:
            self.tree.setCurrentItem(current_item)  # 현재 항목을 설정하여 선택
            current_item.setSelected(True)
            self.update_table_items(current_item)

    def find_item_in_tree(self,parent,text):
        """
        처음엔 project가 들어와서 root에서 project를 찾고
        찾은 project가 parent가 되어 다시 자식들중에 asset_type이 있는지 찾고 있으면
        asset_type이 parent가 되어 asset_name을 찾는다.
        """
        
        for i in range(parent.childCount()):    
            item = parent.child(i)              
            if item.text(0) == text:            
                return item
            found_item = self.find_item_in_tree(item, text)         
            if found_item:
                return found_item
        return None

    def initialize_table_data(self): # 하드코딩할때 처음에 데이터를 넘겨주어야 해서 적은 함수 # 다른 좋은 방안 있으면 추천 부탁.
        row_idx = 0
        for project, tasks in self.assign_datas.items():
            for field in tasks:
                self.make_table_by_field(project,field, row_idx)
                row_idx += 1        

    def _event_col(self): # 여러 이벤트들을 모은 메써드
        self.tree.itemClicked.connect(self.item_clicked)
        self.tree.itemClicked.connect(self.update_table_items)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellPressed.connect(self.get_index)
        self.table.cellPressed.connect(self.update_list_widget_items)
        self.list.itemDoubleClicked.connect(self.double_click_listWidget)
        self.ui.pushButton.clicked.connect(self.enter_refresh)

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
        config.optionxform = str
        
        ini_file_path = os.path.dirname(__file__) +"/status.ini"
        close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if path : 
            result_path = " > ".join(path)
        else:
            result_path = ""
        config["Status"] = {
            "lastworkpath": result_path,
            "closetime": close_time
        }
        os.makedirs(os.path.dirname(ini_file_path), exist_ok=True)
        with open(ini_file_path,"w") as file:
            config.write(file)

    def item_clicked(self,item): # treewidget에서 클릭할때마다 아이템을 가져와 재귀함수를 돌려 save_status함수에 path를 보내준다.
        self.last_file_path = self.get_item_path(item)
        self.save_status(self.last_file_path)

    def get_item_path(self,item):
        path = []
        while item:
            path.insert(0, item.text(0))
            item = item.parent()
        return path

    def set_tree_widget(self): # 트리위젯을 데이터를 가져와 만드는 함수 # 같은종류의 asset일 경우 중첩되는 폴더를 삭제하기 위해 조건을 한번 걸었다.
        self.tree = self.ui.treeWidget
        self.tree.setHeaderLabel("Projects Name")
        tree_widget_dict = {}
        for project,tasks in self.assign_datas.items():
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

    def make_list_widget(self): # 리스트위젯을 만들기 위한 함수
        self.list = self.ui.listWidget
        self.list.clear()
        self.project = None



    def update_table_items(self, item: QTreeWidgetItem):
        parent = item.parent()
        self.list.clear()
        self.initialize_table()                         # 리스트 위젯을 업데이트 해주기위해 초기함수를 돌려썼다.
        if not parent:                                  # 프로젝트를 클릭했을때 
            self.update_table_for_project(item.text(0))
        else:
            self.update_table_for_asset(item, parent)

    def update_table_for_project(self, project_name):
        row_idx = 0 
        for project, tasks in self.assign_datas.items():
            if project_name == project:
                for field in tasks:     
                    self.make_table_by_field(project,field,row_idx)
                    row_idx += 1

    def update_table_for_asset(self, item, parent):
        row_idx = 0
        for project,tasks in self.assign_datas.items():
                for field in tasks:
                    asset_type = field["asset_data"]["sg_asset_type"]
                    asset_name = field["asset_data"]["code"]
                    if parent.text(0) == project and item.text(0) == asset_type:                # asset_type을 클릭했을때
                        self.project = parent.text(0)
                        self.make_table_by_field(project,field,row_idx)
                        row_idx += 1
                    elif parent.text(0) == asset_type and item.text(0) == asset_name:           # asset_name을 클릭했을때
                        self.project = parent.parent().text(0)
                        self.make_table_by_field(project,field,row_idx)
                        row_idx += 1



    def find_file_version(self,project,asset_name,asset_type,task,version):    # 파일 버전을 찾는 함수.
        
        path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"
        if not os.path.exists(path):                                                                                # 경로가 없으면 v001로 가져온다.
            return version
        version_folders = os.listdir(f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes")  # v001의 폴더가 있으면 그 폴더로 가서 마지막 버전을 가져온다.
        version = sorted(version_folders)[-1] # v004
        
        
        return version

    def update_list_widget_items(self):        # tablewidget을 클릭했을시 리스트 위젯에 업데이트 되는 함수
        self.list.clear()
        for project,field in self.assign_datas.items():
            if self.project == project:
                widget = self.table.cellWidget(self.row,0)
                
                if widget:
                    asset_name_label = widget.findChild(QLabel, "asset_name")
                    version_label = widget.findChild(QLabel, "version")
                    asset_type_label = widget.findChild(QLabel, "asset_type")
                    task_label = widget.findChild(QLabel, "task")

                    asset_type = asset_type_label.text()
                    version = version_label.text()
                    asset_name = asset_name_label.text()
                    task = task_label.text()
                    path = f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"

                files = os.listdir(path)
                if not files:
                    self.list.addItem("No Files")
                    return

                if not os.path.exists(path):
                    self.list.addItem("No Files")
                    return
                
                files = sorted(os.listdir(path))
                
                for file in files:
                    self.list.addItem(file)

                self.current_path = path                                 # 더블클릭시 가져올 패스

    def double_click_listWidget(self,item):    # 더블클릭시 파일 이름을 가져와야하기때문에 item을 매개변수로 가져온다.
        if item.text() == "No Files":
            self.msg_box("NoFile")

        if hasattr(self, 'current_path'):                   # self 객체에 current_path 라는게 있는지 확인하는 메쏘드
            file_name = item.text()
            file_path = os.path.join(self.current_path, file_name)
            self.threading_func(file_path)

    def show_context_menu(self, pos : QPoint): # 우클릭시 PushButton을 생성하고 각 PushButton을 누를 시 실행되는 함수를 연결시키는 함수, 클릭한 row의 index를 return 해준다
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
        retake_button.clicked.connect(self.make_version_up_for_retake)
        retake_action = QWidgetAction(self)
        retake_action.setDefaultWidget(retake_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.enter_refresh)
        refresh_action = QWidgetAction(self)
        refresh_action.setDefaultWidget(refresh_button)
        
        # QAction을 컨텍스트 메뉴에 추가
        context_menu.addAction(new_scene_action)
        context_menu.addAction(version_up_action)
        context_menu.addAction(sg_site_action)
        context_menu.addAction(my_path_action)
        context_menu.addAction(retake_action)
        context_menu.addAction(refresh_action)

 
        # 우클릭시 화면에 표시할수 있게 하는 코드
        context_menu.exec(self.table.viewport().mapToGlobal(pos))  #g선생
        
    def get_index(self,row,_):                 # 선택한 셀의 row를 가져오기위해 만든함수
        self.row = row
            
    def click_right_button_import_data(self):  # 우클릭시 그 포지션에따라 인덱스를 가져오고 그 인덱스에 해당하는 정보의 리스트를 리턴한다.
        if self.row is None:
            return

        for project,_field in self.assign_datas.items(): 
            if self.project == project:
                widget = self.table.cellWidget(self.row,0)
                if widget:
                    asset_name_label = widget.findChild(QLabel, "asset_name")
                    version_label = widget.findChild(QLabel, "version")
                    asset_type_label = widget.findChild(QLabel, "asset_type")
                    task_label = widget.findChild(QLabel, "task")

                    asset_type = asset_type_label.text()
                    version = version_label.text()
                    asset_name = asset_name_label.text()
                    task = task_label.text()
                    path = f"/home/rapa/wip/{self.project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"
                click_list = [asset_type,version,asset_name,task,path]
                return click_list
        return None


    def import_new_scene(self):                # 파일이 없으면 새로운 마야 파일을 열어주는 시스템 ################# status update
        right_click_info = self.click_right_button_import_data()      

        if not right_click_info:                        
            return
        asset_type,version,asset_name,task,path = right_click_info          # path = scene까지 포함되어있다.
        base_path = path.replace(f"/scenes/{version}","")                   # 파일을 생성할때는 폴더가 생성되어있지 않기때문에 scene을 지워서 다시 만들어준다.
        common_list = ["cache","images","scenes","sourceimages"]   
        file_name = f"{asset_name}_{version}_w001.mb"

        for common_item in common_list:
            create_path = f"{base_path}/{common_item}/{version}"
            os.makedirs(create_path, exist_ok=True)

        mypath = os.path.dirname(__file__)

        
        empty_file_path = f"{mypath}/.emptymaya.mb"
        pub_path = path.replace("wip","pub")

        mod_pub_path = pub_path.replace(task,"mod")
        lkd_pub_path = pub_path.replace(task,"lkd")
         
        result_file_path = empty_file_path

        if task == "lkd":
            if os.path.exists(mod_pub_path):
                mod_file = os.listdir(mod_pub_path)[-1]
                mod_pub_file_path = os.path.join(mod_pub_path,mod_file)      
                result_file_path = mod_pub_file_path  
        if task == "rig":
            if os.path.exists(lkd_pub_path): # 룩뎁 작업이있으면
                lkd_file = sorted(os.listdir(lkd_pub_path))[-1]
                lkd_pub_file_path = os.path.join(lkd_pub_path,lkd_file)
                result_file_path = lkd_pub_file_path   
                if os.path.exists(mod_pub_path):    # 모델링 작업이 있으면
                    mod_file = sorted(os.listdir(mod_pub_path))[-1]
                    mod_pub_file_path = os.path.join(mod_pub_path,mod_file)     
                    result_file_path = mod_pub_file_path   
            else: 
                result_file_path = empty_file_path

        
        add_file_path = os.path.join(path, file_name)
        if os.path.exists(add_file_path):
            self.msg_box("YesFile")
            return
        shutil.copy2(result_file_path,add_file_path) # version_path에 emptyfile을 복사해 파일이름을 작성된 파일을 복사하는 코드
            
        if result_file_path == empty_file_path:
            self.msg_box("NoFile")
        self.sg_cls.sg_status_update(asset_name,task) ### Backend
        self.threading_func(add_file_path)

    def threading_func(self,add_file_path):
        maya_thread = threading.Thread(target=self.run_maya,args=(add_file_path,))       # 한개의 튜플을 보내주기위해 ,을 붙혔다.
        maya_thread.daemon = True
        maya_thread.start()
        self.sg_cls.sg_status_update() ############################################################ status update
        
    def run_maya(self,add_file_path):
        process = subprocess.Popen(["/bin/bash", "-i", "-c", f'asset_maya {add_file_path}'],start_new_session=True)
        try:
            process.wait()  # Maya가 종료될 때까지 대기
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Maya가 정상적으로 종료되지 않았으면 강제 종료 시도
            if process.poll() is None:
                print("마야를 종료합")
                process.terminate()
                process.wait()
                if process.poll() is None:
                    print("마야를 강제 종료합니다.")
                    process.kill()
                    process.wait()

    def save_wip_version_up(self):        # 마지막 wip버전을 버전업해서 파일을 복사하는 함수
        last_file_name,version_up_name,path = self.make_version_up_filename()
        if not last_file_name:
            return
        last_file_path = f"{path}/{last_file_name}"
        version_up_file_path = f"{path}/{version_up_name}"
        
        shutil.copy2(last_file_path,version_up_file_path)
        self.msg_box("WipVersionUp")
        self.update_list_widget_items()
         
    def make_version_up_filename(self):   # version_up_name 을 만들기위해 쓴 함수 
        
        right_click_info = self.click_right_button_import_data()
        if not right_click_info:
            return None
        
        _asset_type,_version,_asset_name,_task,path = right_click_info     # 우클릭한 파일의 정보들을 가져온다.
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

    def enter_Sg_site(self):              # Shotgrid url 접속하는 함수
        url = "https://4thacademy.shotgrid.autodesk.com/" 
        QDesktopServices.openUrl(QUrl(url))
        
    def enter_my_path(self):              # subprocess에 명령어를 보내 path에 있는 경로를 여는 함수
        right_click_info = self.click_right_button_import_data() 
        if not right_click_info:
            return
        _,_,_,_,path = right_click_info
        real_path = os.path.realpath(path)              
        os.path.exists(real_path)
        if os.path.exists(real_path):
            subprocess.run(['xdg-open', real_path])
        else:
            self.msg_box("Path_Error")

    def make_version_up_for_retake(self): # retake에서 status를 확인후 버전업되는 함수 ################# status update
        widget = self.table.cellWidget(self.row,0)


        if widget:
            label_status = widget.findChild(QLabel, "current_status")
            if label_status:
                status = label_status.property("current_status")        # 현재 라벨에는 이미지가 들어가있어서 Property를 넣었다.

    
        if not status == "re":                                          # retake 상태가 아니면 에러메세지 띄우고 리턴한다.
            self.msg_box("Status_Error")
            return
        
        right_click_info = self.click_right_button_import_data()
        if not right_click_info:                                         # 우클릭한 정보가 없으면 리턴되는게 없다.
            return None
        
        asset_type,version,asset_name,task,path = right_click_info      # 우클릭한 파일의 정보들을 가져온다.

        base_path = path.replace(f"/scenes/{version}","")               # 파일을 생성할때는 폴더가 생성되어있지 않기때문에 scene을 지워서 다시 만들어준다.

        if not os.path.exists(path):                                    #  path가 실제 경로에 없으면 리턴되는게 없다.
            return None
        pub_path = path.replace("wip","pub")
        files = os.listdir(pub_path)

        for file in files:
            file_path = f"{pub_path}/{file}"
            if os.path.isfile(file_path):
                last_file_path = file_path
                pub_file_name = file
                version = pub_file_name.split("_")[-1].replace(".mb","")
        # 마지막 Pub한 파일 이름


        
        file_name,ext = os.path.splitext(pub_file_name)                                                             
        # teapot_lkd_v003 , .mb

        version_int = version.replace("v","")
        # ex) 003

        only_version_up = int(version_int) + 1
        # ex) 4

        version_up = "v%03d" % only_version_up
        # ex) v004

        file_name = file_name.replace(version,version_up)
        # ex) teapot_lkd_v003 => teapot_lkd_v004

        new_file_name = f"{file_name}_w001{ext}"
        # ex) teapot_v004_w001.mb

        version_up_wip_path = path.replace(version,version_up)
        # ex) /home/rapa/wip/Moomins/asset/character/mat/lkd/wip/scenes/v002

        common_list = ["cache","images","scenes","sourceimages"]   
        for common_item in common_list:
            create_path = f"{base_path}/{common_item}/{version_up}"
            os.makedirs(create_path, exist_ok=True)

        os.makedirs(version_up_wip_path,exist_ok=True)
        copy_wip_path = f"{version_up_wip_path}/{new_file_name}"
        self.msg_box("RetakeVersionUp")
        shutil.copy2(last_file_path,copy_wip_path)
        self.sg_cls.sg_status_update(asset_name,task)
        self.reload_data()
        self.import_ini_file()

        
        


    def enter_refresh(self):
        self.widgets_clear()
        self.reload_data()
        self.set_tree_widget()
        self.make_list_widget()
        self.import_ini_file()
        
    def widgets_clear(self):
        self.table.clear()
        self.list.clear()
        self.tree.clearSelection()
        self.tree.clear()
        
    def reload_data(self):
        self.assign_datas = {}
        self.get_assgined_user_project_by_task()
        print(self.assign_datas)
        
    def msg_box(self, message_type): # 경고메세지를 띄우는 함수 
        messages = {
            "Path_Error": ("Error", "경로가 없습니다. New scene을 눌러 작업을 시작해주세요.", QMessageBox.Critical),
            "Status_Error": ("Error", "Retake 상태가 아닙니다. Status를 확인해주세요.", QMessageBox.Critical),
            "NoFile": ("Error", "작업된 파일이 없습니다. 빈 파일이 열립니다.", QMessageBox.Critical),
            "YesFile":("Error","이미 파일이 있습니다.",QMessageBox.Critical),
            "WipVersionUp": ("WipVersionUp", "WipVersionUp 된 파일이 생성 되었습니다.", QMessageBox.Information),
            "RetakeVersionUp": ("RetakeVersionUp", "RetakeVersionUp 된 파일이 생성 되었습니다.", QMessageBox.Information)
        }

        title, message, icon = messages.get(message_type, ("Info", " ", QMessageBox.Information))
        QMessageBox(icon, title, message, QMessageBox.Yes).exec_()
        
        
    def initialize_table(self):    # 버튼 누를때마다 초기화 되는 함수
        
        self.ui.tableWidget.setRowCount(0)
        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)  
        
    def find_image_icon(self,file_type):    # file_type을 받아서 sourceimages.ini에서 image path를 받아오는 함수
        
        current_dir = os.path.dirname(__file__)
        path = os.path.dirname(current_dir)
        sourceimages_ini_file_path = os.path.join(current_dir,"sourceimages.ini")
        config = ConfigParser()
        config.optionxform = str
        if not os.path.exists(sourceimages_ini_file_path):
            raise FileNotFoundError(f"{sourceimages_ini_file_path} is None File")
        config.read(sourceimages_ini_file_path,encoding='utf-8')
        icon_name = f"{file_type}_icon"
        
        if icon_name not in config["icons"]:
            raise KeyError(f"{icon_name} is None Key")
        image_path = config["icons"][icon_name]  
        
        return image_path
    
    
    
    def make_table_by_field(self,project,field,row_idx): # 하드코딩
        """
        하드 코딩으로 ui 만들기...!
        """

        start_date = field["start_date"]
        due_date = field["due_date"]

        if start_date is None:
            start_date = "2099-99-99"
        if due_date is None:
            due_date = "2099-99-99"
        due_date = due_date[-10:]
        task = field["step"]["name"].lower()
        asset_name = field["asset_data"]["code"]

        asset_type = field["asset_data"]["sg_asset_type"]
        date_range = f"{start_date} - {due_date}"
        version = self.find_file_version(project,asset_name,asset_type,task,"v001")

        current_status = field["sg_status_list"]                                              
        file_type = "mb"

        container_widget = QWidget()
        grid_layout = QGridLayout()
        container_widget.setLayout(grid_layout)

        if row_idx >= self.table.rowCount():
            self.table.insertRow(row_idx)

        self.table.setRowHeight(row_idx, 80)
        self.table.setColumnWidth(row_idx, 300)

        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget)

    
        #   하드코딩....

        # 프로그램 이미지 (0.0)
        label_icon_image = QLabel()
        image_path = self.find_image_icon(file_type)
        # print(image_path)
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_icon_image.setPixmap(scaled_pixmap)
        label_icon_image.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_icon_image.setFixedSize(80,80)
        label_icon_image.setContentsMargins(0, 0, 15, 0)

        # 어셋 네임 (0.1)
        label_asset_name = QLabel()
        label_asset_name.setText(asset_name)
        label_asset_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_name.setObjectName("asset_name")
        label_asset_name.setStyleSheet("font-size: 12px;")
        label_asset_name.setFixedSize(100, 20)

        # 버전 (0.2)
        label_version = QLabel()
        label_version.setText(version)
        label_version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_version.setObjectName("version")
        label_version.setStyleSheet("font-size: 12px;")
        label_version.setFixedSize(100, 20)

        # 테스크 (0.3)
        label_task = QLabel()
        label_task.setText(task)
        label_task.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_task.setObjectName("task")
        label_task.setStyleSheet("font-size: 12px;")
        label_task.setFixedSize(100, 20)   

        # 기간 (1.1-1.3)
        label_date_range = QLabel()
        label_date_range.setText(date_range)
        label_date_range.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_date_range.setObjectName("date_range")
        label_date_range.setStyleSheet("font-size: 12px;")
        label_date_range.setFixedSize(250, 20)


        # 어셋 타입 (2.1)
        label_asset_type = QLabel()
        label_asset_type.setText(asset_type)
        label_asset_type.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_type.setObjectName("asset_type")
        label_asset_type.setStyleSheet("font-size: 12px;")
        label_asset_type.setFixedSize(100, 20)    

        label_status = QLabel()
        label_status.setObjectName("current_status")
        image_path = self.find_image_icon(current_status)
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(30, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_status.setPixmap(scaled_pixmap)
        label_status.setProperty("current_status",current_status)
        label_status.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        label_status.setFixedSize(100, 20)

        grid_layout.addWidget(label_icon_image, 0, 0) # 프로그램 이미지 (0.0)
        grid_layout.addWidget(label_asset_name, 0, 1) # 어셋 네임 (0.1)
        grid_layout.addWidget(label_version, 0, 2) # 버전 (0.2)
        grid_layout.addWidget(label_task, 0, 3) # 테스크 (0.3)
        grid_layout.addWidget(label_date_range, 1,1,1, 3) # 기간 (1.1-1.3)
        grid_layout.addWidget(label_asset_type, 2, 1) # 어셋 타입 (2.1)
        grid_layout.addWidget(label_status, 2, 3) # status (2.3)
       
       
       
        



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AssetLoader()
    win.show()
    app.exec() 