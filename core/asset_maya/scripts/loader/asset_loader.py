import sys
import os
import subprocess
import re
import shutil
import threading
from configparser import ConfigParser
from PySide6.QtWidgets import (
QWidget,QApplication,QTreeWidgetItem,
QMenu,QWidgetAction,QGridLayout,
QPushButton,QTableWidget,QMessageBox,
QLabel
)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QEvent,QPoint
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices,QPixmap,QGuiApplication
from datetime import datetime
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

    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/loader.ui"
        ui_file = QFile(ui_file_path) 
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.table = self.ui.findChild(QTableWidget, "tableWidget")
        self.initialize_table_data()
        self.set_tree_widget()
        self.make_list_widget() 
        self.make_ui_center()

    def make_ui_center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_assgined_user_project_by_task(self):
        user_tasks_data = self.sg_cls.get_task_data(self.user_id)
        assign_user_project_by_task = {}
        for task_data in user_tasks_data:
            asset_id = task_data["entity"]["id"]
            asset_data = self.sg_cls.get_assets_data(asset_id)
            task_data["asset_data"] = asset_data
            project = task_data["project"]["name"]

            if project not in assign_user_project_by_task:
                assign_user_project_by_task[project] = []
            assign_user_project_by_task[project].append(task_data)
        self.assign_datas = assign_user_project_by_task

    def import_ini_file(self):
        ini_file_path =  os.path.dirname(__file__) +"/status.ini"
        config = ConfigParser()
        config.optionxform = str
        config.read(ini_file_path,encoding='utf-8')
        last_click_path = config["Status"]["lastworkpath"]
        close_time = config["Status"]["closetime"]
        click_path = last_click_path.split(" > ")

        current_item = self.tree.invisibleRootItem()
        

        for text in click_path:
            item = self.find_item_in_tree(current_item, text)
            if item:
                self.tree.expandItem(item)
                current_item = item
            else:
                return
        if current_item:
            self.tree.setCurrentItem(current_item)
            current_item.setSelected(True)
            self.update_table_items(current_item)

    def find_item_in_tree(self,parent,text):
        """
        first, last clicked project in root, parent set project
        second, last clicked asset_type in project, parent set asset_type
        last, last clicked asset_name in asset_type, return asset_name
        """
        
        for i in range(parent.childCount()):    
            item = parent.child(i)              
            if item.text(0) == text:            
                return item
            found_item = self.find_item_in_tree(item, text)         
            if found_item:
                return found_item
        return

    def initialize_table_data(self):
        """
        OpenLoader, pass the row,data in tablewidget
        """
        row_idx = 0
        for project, tasks in self.assign_datas.items():
            for field in tasks:
                self.make_table_by_field(project,field, row_idx)
                row_idx += 1        

    def _event_col(self):
        self.tree.itemClicked.connect(self.item_clicked)
        self.tree.itemClicked.connect(self.update_table_items)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellPressed.connect(self.get_index)
        self.table.cellPressed.connect(self.update_list_widget_items)
        self.list.itemDoubleClicked.connect(self.double_click_listWidget)
        self.ui.pushButton.clicked.connect(self.enter_refresh)

    def eventfilter(self,obj,event):
        """
        if close event, save the .ini file by last clicked path
        """
        if event.type() == QEvent.Close and obj is self:
            self.save_status(self.last_file_path)
            return True
        return super().eventfilter(obj,event)

    def close_event(self,event):
        self.save_status(self.last_file_path)
        event.accept()

    def save_status(self,path):
        """
        save the ini file cause .json is more heavy .ini
        """
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

    def item_clicked(self,item):
        self.last_file_path = self.get_item_path(item)
        self.save_status(self.last_file_path)

    def get_item_path(self,item):
        path = []
        while item:
            path.insert(0, item.text(0))
            item = item.parent()
        return path

    def set_tree_widget(self):
        self.tree = self.ui.treeWidget
        self.tree.setHeaderLabel("Projects Name")
        tree_widget_dict = {}
        for project,tasks in self.assign_datas.items():
            project_item = QTreeWidgetItem(self.tree,[project])
            tree_widget_dict[project] = {}
            for task in tasks:
                asset_type =  task["asset_data"]["sg_asset_type"]
                asset_name = task["asset_data"]["code"]
                # asset_type data have duplicate values so this type used set -> set is delete duplicate value
                if asset_type not in tree_widget_dict[project]:
                    asset_type_item = QTreeWidgetItem(project_item, [asset_type])
                    tree_widget_dict[project][asset_type] = set()                       # reset asset_type set()
                if asset_name not in tree_widget_dict[project][asset_type]:
                    asset_name_item = QTreeWidgetItem(asset_type_item, [asset_name])
                    tree_widget_dict[project][asset_type].add(asset_name)

    def make_list_widget(self):
        self.list = self.ui.listWidget
        self.list.clear()
        self.project = None

    def update_table_items(self, item: QTreeWidgetItem):
        parent = item.parent()
        self.list.clear()
        self.initialize_table()
        if not parent:
            self.update_table_for_project(item.text(0))
        else:
            self.update_table_for_asset(item, parent)

    def update_table_for_project(self, project_name):
        row_idx = 0 
        for project, tasks in self.assign_datas.items():
            # clicked project
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
                    # clicked asset_type
                    if parent.text(0) == project and item.text(0) == asset_type:
                        self.project = parent.text(0)
                        self.make_table_by_field(project,field,row_idx)
                        row_idx += 1
                    # clicked asset_name
                    elif parent.text(0) == asset_type and item.text(0) == asset_name:
                        self.project = parent.parent().text(0)
                        self.make_table_by_field(project,field,row_idx)
                        row_idx += 1

    def find_file_version(self,project,asset_name,asset_type,task,version):
        path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes/{version}"
        if not os.path.exists(path):
            # if have not path, return v001
            return version
        # if have folder return lastest file version
        version_folders = os.listdir(f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/scenes")
        version = sorted(version_folders)[-1] # v004
        return version

    def update_list_widget_items(self):
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

                self.current_path = path

    def double_click_listWidget(self,item):
        if item.text() == "No Files":
            self.msg_box("NoFile")

        if hasattr(self, 'current_path'):
            file_name = item.text()
            file_path = os.path.join(self.current_path, file_name)
            self.threading_func(file_path)

    def show_context_menu(self, pos : QPoint):
        # right button clicked functions
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
        my_path_button.clicked.connect(self.enter_file_path)
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
        
        context_menu.addAction(new_scene_action)
        context_menu.addAction(version_up_action)
        context_menu.addAction(sg_site_action)
        context_menu.addAction(my_path_action)
        context_menu.addAction(retake_action)
        context_menu.addAction(refresh_action)

        context_menu.exec(self.table.viewport().mapToGlobal(pos))
        
    def get_index(self,row,_):
        # get clicked row
        self.row = row
            
    def click_right_button_import_data(self):
        # if clicked right button, get pos index and return index data
        if not self.row:
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
            return


    def import_new_scene(self):
        # if not task Mayafile, Open Empty Maya file
        right_click_info = self.click_right_button_import_data()      

        if not right_click_info:                        
            return
        asset_type,version,asset_name,task,path = right_click_info
        base_path = path.replace(f"/scenes/{version}","")
        file_name = f"{asset_name}_{version}_w001.mb"
        common_list = ["cache", "images", "scenes", "sourceimages"]

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
            # Have lookdev task
            if os.path.exists(lkd_pub_path):
                lkd_file = sorted(os.listdir(lkd_pub_path))[-1]
                lkd_pub_file_path = os.path.join(lkd_pub_path,lkd_file)
                result_file_path = lkd_pub_file_path
                # Have Modelling task
                if os.path.exists(mod_pub_path):
                    mod_file = sorted(os.listdir(mod_pub_path))[-1]
                    mod_pub_file_path = os.path.join(mod_pub_path,mod_file)     
                    result_file_path = mod_pub_file_path   
            else: 
                result_file_path = empty_file_path

        add_file_path = os.path.join(path, file_name)
        if os.path.exists(add_file_path):
            return self.msg_box("YesFile")
        shutil.copy2(result_file_path,add_file_path)
        if result_file_path == empty_file_path:
            self.msg_box("NoFile")
        self.sg_cls.sg_status_update(asset_name,task) ### Backend
        self.threading_func(add_file_path)

    def threading_func(self,add_file_path):
        maya_thread = threading.Thread(target=self.run_maya,args=(add_file_path,))
        maya_thread.daemon = True
        maya_thread.start()
        self.sg_cls.sg_status_update()
        
    def run_maya(self,add_file_path):
        process = subprocess.Popen(["/bin/bash", "-i", "-c", f'asset_maya {add_file_path}'],start_new_session=True)
        try:
            # Wait for finished Maya
            process.wait()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Force quit if not terminated
            if not process.poll():
                process.terminate()
                process.wait()
                if not process.poll():
                    process.kill()
                    process.wait()

    def save_wip_version_up(self):
        # if wip version up, copy to lastest wip version file
        last_file_name,version_up_name,path = self.make_version_up_filename()
        if not last_file_name:
            return
        last_file_path = f"{path}/{last_file_name}"
        version_up_file_path = f"{path}/{version_up_name}"
        
        shutil.copy2(last_file_path,version_up_file_path)
        self.msg_box("WipVersionUp")
        self.update_list_widget_items()
         
    def make_version_up_filename(self):
        
        right_click_info = self.click_right_button_import_data()
        if not right_click_info:
            return
        _asset_type,_version,_asset_name,_task,path = right_click_info
        if not os.path.exists(path):
            return
        last_version_file = sorted(os.listdir(path))[-1]
        p = re.compile("w\d{2,4}")
        p_data = p.search(last_version_file)
        if p_data:
            wip_version = p_data.group()
            version = wip_version[1:]
            version_up = int(version) + 1
            wip_version_up = "w%03d" % version_up
            update_version_file_name = last_version_file.replace(wip_version,wip_version_up)
            return last_version_file,update_version_file_name,path

    def enter_Sg_site(self):
        url = "https://4thacademy.shotgrid.autodesk.com/" 
        QDesktopServices.openUrl(QUrl(url))
        
    def enter_file_path(self):
        # open file path in directory
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

    def make_version_up_for_retake(self):
        # if status is retake, version up and copy file
        widget = self.table.cellWidget(self.row,0)

        if widget:
            label_status = widget.findChild(QLabel, "current_status")
            if label_status:
                status = label_status.property("current_status")

    
        if not status == "re":
            return self.msg_box("Status_Error")
        
        right_click_info = self.click_right_button_import_data()
        if not right_click_info:
            return
        
        asset_type,version,asset_name,task,path = right_click_info

        base_path = path.replace(f"/scenes/{version}","")

        if not os.path.exists(path):
            return
        pub_path = path.replace("wip","pub")
        files = os.listdir(pub_path)

        for file in files:
            file_path = f"{pub_path}/{file}"
            if os.path.isfile(file_path):
                last_file_path = file_path
                pub_file_name = file
                version = pub_file_name.split("_")[-1].replace(".mb","")
        file_name,ext = os.path.splitext(pub_file_name)
        version_int = version.replace("v","")
        only_version_up = int(version_int) + 1
        version_up = "v%03d" % only_version_up
        file_name = file_name.replace(version,version_up)
        new_file_name = f"{file_name}_w001{ext}"
        version_up_wip_path = path.replace(version,version_up)
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

    def msg_box(self, message_type):
        messages = {
            "Path_Error": ("Error", "Path is not Exist. Clicked New scene", QMessageBox.Critical),
            "Status_Error": ("Error", "Status is not Retake. Check the status.", QMessageBox.Critical),
            "NoFile": ("Error", "Have not tasks file. Open empty file.", QMessageBox.Critical),
            "YesFile":("Error","Already have task file.",QMessageBox.Critical),
            "WipVersionUp": ("WipVersionUp", "Make wipVersionUp file.", QMessageBox.Information),
            "RetakeVersionUp": ("RetakeVersionUp", "Make retakeVersionUp file.", QMessageBox.Information)
        }
        title, message, icon = messages.get(message_type, ("Info", " ", QMessageBox.Information))
        QMessageBox(icon, title, message, QMessageBox.Yes).exec_()

    def initialize_table(self):
        self.ui.tableWidget.setRowCount(0)
        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)  
        
    def find_image_icon(self,file_type):
        # get icon file path from sourceimages.ini file
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
    
    def make_table_by_field(self,project,field,row_idx):
        start_date = field["start_date"]
        due_date = field["due_date"]
        if not start_date:
            start_date = "2099-99-99"
        if not due_date:
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

        label_icon_image = QLabel()
        image_path = self.find_image_icon(file_type)
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_icon_image.setPixmap(scaled_pixmap)
        label_icon_image.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label_icon_image.setFixedSize(80,80)
        label_icon_image.setContentsMargins(0, 0, 15, 0)

        label_asset_name = QLabel()
        label_asset_name.setText(asset_name)
        label_asset_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_asset_name.setObjectName("asset_name")
        label_asset_name.setStyleSheet("font-size: 12px;")
        label_asset_name.setFixedSize(100, 20)

        label_version = QLabel()
        label_version.setText(version)
        label_version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_version.setObjectName("version")
        label_version.setStyleSheet("font-size: 12px;")
        label_version.setFixedSize(100, 20)

        label_task = QLabel()
        label_task.setText(task)
        label_task.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_task.setObjectName("task")
        label_task.setStyleSheet("font-size: 12px;")
        label_task.setFixedSize(100, 20)   

        label_date_range = QLabel()
        label_date_range.setText(date_range)
        label_date_range.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_date_range.setObjectName("date_range")
        label_date_range.setStyleSheet("font-size: 12px;")
        label_date_range.setFixedSize(250, 20)

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