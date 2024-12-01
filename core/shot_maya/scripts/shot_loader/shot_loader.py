# Maya Shot Loader  (ly, ani, lgt)
import sys
import os
import shutil
import re
import webbrowser
import subprocess
from pprint import pprint
from importlib import reload

try:
    from PySide6.QtWidgets import QApplication, QWidget, QTreeWidgetItem
    from PySide6.QtWidgets import QLabel, QMenu, QMessageBox
    from PySide6.QtWidgets import QGridLayout
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile, Qt
    from PySide6.QtGui import QPixmap, QAction,QGuiApplication
except:
    from PySide2.QtWidgets import QApplication, QWidget, QTreeWidgetItem
    from PySide2.QtWidgets import QLabel, QMenu, QMessageBox
    from PySide2.QtWidgets import QGridLayout
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtCore import QFile, Qt
    from PySide2.QtGui import QPixmap, QAction,QGuiApplication

from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi


class ShotLoader (QWidget):

    def __init__(self, ):
        super().__init__()

        self.sg_api = ShotgunApi()
        self.maya_api = MayaApi()

        self.make_ui()

        self.get_task_data()
        self.set_treewidget()
        self.make_tablewidget()
        self.events_func()
        

    def make_ui(self):
        """
        Create a UI.
        """
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/shot_loader.ui"
        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self) 
        self.setWindowTitle("Shot loader")
        ui_file.close() 
        self.make_ui_center()

    def make_ui_center(self):
        """
        Place UI in the center of the screen
        """
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def events_func (self):
        """
        Event Collection
        """
        self.tree.itemClicked.connect(self.click_treewiget_event) # Tree Widget Click
        self.table.cellPressed.connect(self.get_click_data) # Table Widget Click
        self.table.setContextMenuPolicy(Qt.CustomContextMenu) # Table Widget Right-Click
        self.table.customContextMenuRequested.connect(self.click_right_menu) # Table Widget Right-Click
        self.ui.listWidget.itemDoubleClicked.connect(self.double_clicked_item) # List Widget Double-Click
        self.ui.pushButton.clicked.connect(self.refresh) # Refresh Button

    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv()  # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"



    def get_task_data(self):
        """
        Get data from the task and organize it into the dictionary
        """
        self.datas_list = self.sg_cls.get_task_data(self.user_id)
        self.projects_data_dict = {}
        
        for data_dict in self.datas_list:
            project_name = data_dict["project"]["name"]                  # Project Name (eg. Moomins)
            seq_name_part = data_dict["entity"]["name"].split("_")[0]    # Sequence Name (eg. AFT)
            seq = data_dict["entity"]["name"]                            # Sequence Number (eg. AFT_0010)
            task = data_dict["step"]["name"]                             # Department (eg. ani)
            start_date = data_dict["start_date"]                         # Start Date (format : YYYY-MM-DD)
            due_date = data_dict["due_date"]                             # Publish Date (format : YYYY-MM-DD)
            status = data_dict["sg_status_list"]                         # Status (eg. wip)


            # for task in task_list:
            # Organize versions
            ver_path = f"/home/rapa/wip/{project_name}/seq/{seq_name_part}/{seq}/{task}/wip/scene"
            if not os.path.exists(ver_path):
                version = "v001"
            else:
                ver_folders = os.listdir(ver_path)
                if not ver_folders:
                    version = "v001"
                else:
                    version = sorted(ver_folders)[-1]
            

            # Organize data into a dictionary
            if project_name not in self.projects_data_dict:
                self.projects_data_dict[project_name] = {}

            if seq not in self.projects_data_dict[project_name]:
                self.projects_data_dict[project_name][seq] = {}

            self.projects_data_dict[project_name][seq]["task"] = task
            self.projects_data_dict[project_name][seq]["start_date"] = start_date
            self.projects_data_dict[project_name][seq]["due_date"] = due_date
            self.projects_data_dict[project_name][seq]["status"] = status
            self.projects_data_dict[project_name][seq]["version"] = version
        
        pprint(self.projects_data_dict)

    # trewidget related methods
    def set_treewidget(self):
        """
        Floating information in tree widgets
        """
        self.tree = self.ui.treeWidget
        self.tree.clear()

        # Put only the project and seq-named alphabetic parts in the dictionary to be displayed in the tree
        treewiget_project_dict = {}
        for project_name, seq_dict in self.projects_data_dict.items():

            for seq_name in seq_dict.keys():
                seq_name_parts = seq_name.split("_")[0]
                
                if project_name not in treewiget_project_dict:
                    treewiget_project_dict[project_name] = []

                if seq_name_parts not in treewiget_project_dict[project_name]:
                    treewiget_project_dict[project_name].append(seq_name_parts)

        # Adding to the Tree Widget
        for project, seq_name_parts in treewiget_project_dict.items():
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, project)

            for seq_name_part in sorted(seq_name_parts):
                seq_item = QTreeWidgetItem(project_item)
                seq_item.setText(0, seq_name_part)

    def click_treewiget_event(self, item):
        """
        Find the data that matches when clicked in the tree widget
        """
        self.table.clear()
        self.ui.listWidget.clear()

        if item.childCount() > 0: # Project (Parenet)
            selected_project = item.text(0)
            for project_name, seq_data_dict in self.projects_data_dict.items():
                if project_name == selected_project:
                    matching_project_dict = self.projects_data_dict[selected_project]
                    if matching_project_dict:
                        self.update_table_items(matching_project_dict, None)

        else: # Sequence (Child)
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


    # Methods related to tablewidget
    def make_tablewidget(self):
        """
        Table Widget Default Settings
        """
        self.table = self.ui.tableWidget
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 300)


    def update_table_items(self, matching_project_dict=None, matching_seq_dict=None):
        """
        Add row to tableWidget to match the number of data
        """
        if matching_project_dict:
            data_dict = matching_project_dict
        elif matching_seq_dict:
            data_dict = matching_seq_dict
        else:
            return  # When there is no matching task
        
        self.table.setRowCount(len(data_dict)) 
        row = 0
        for row, seq_name in enumerate(data_dict):
            self.make_table_hard_coding(row, data_dict, seq_name)
            # print (row, data_dict, seq_name)
            row += 1

    def make_table_hard_coding(self, row, data_dict, seq_name):
        """
        Create tableWidget with hard coding
        """
        # Organize data {'BRK_0010': {'task': 'ani', 'start_date': '2024-08-26', 'due_date': '2024-08-28', 'status': 're', 'version': 'v001'}}
        task = data_dict[seq_name]["task"]
        version = data_dict[seq_name]["version"]
        start_date = data_dict[seq_name]["start_date"]
        due_date = data_dict[seq_name]["due_date"]
        date_range = f"{start_date} - {due_date}"
        status = data_dict[seq_name]["status"]

        container_widget = QWidget() # Create a Container Widget
        grid_layout = QGridLayout() # Create Grid Layout
        container_widget.setLayout(grid_layout) # Set layout to container

        self.table.setRowHeight(row, 80) # Adjusting the height of the row

        self.table.setCellWidget(row, 0, container_widget) # Add a Container to the Table Widget
        

        # Logo images by DCC
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

        # Sequence Name
        label_node_name2 = QLabel()
        label_node_name2.setText(seq_name)
        label_node_name2.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_node_name2.setObjectName("seq_name")
        label_node_name2.setStyleSheet("font-size: 12px;")
        label_node_name2.setFixedSize(80, 20)

        # Version
        label_node_name3 = QLabel()
        label_node_name3.setText(version)
        label_node_name3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_node_name3.setObjectName("version")
        label_node_name3.setStyleSheet("font-size: 12px;")
        label_node_name3.setFixedSize(70, 20)    
        
        # User Task
        label_node_name4 = QLabel()
        label_node_name4.setText(task)
        label_node_name4.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_node_name4.setObjectName("task")
        label_node_name4.setStyleSheet("font-size: 12px;")
        label_node_name4.setFixedSize(80, 20)   
        
        # Publish Date
        label_node_name5 = QLabel()
        label_node_name5.setText(date_range)
        label_node_name5.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_node_name5.setStyleSheet("font-size: 12px;")
        label_node_name5.setFixedSize(145, 20)       

        # Status labels
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
        
        # Place labels in layout
        grid_layout.addWidget(label_node_name1, 0, 0) # Logo images by DCC
        grid_layout.addWidget(label_node_name2, 0, 1) # Sequence Name
        grid_layout.addWidget(label_node_name3, 0, 2) # Versioin
        grid_layout.addWidget(label_node_name4, 0, 3) # User Task
        grid_layout.addWidget(label_node_name5, 1, 1, 1, 2) # Publish Date
        grid_layout.addWidget(label_node_name6, 1, 3) # Status

        

    def get_click_data(self, row,_):
        """
        Method to declare the row selected in the table widget as a global variable
        """
        self.click_row = row
        self.set_listwidget()

# List Widget
    def set_listwidget (self):
        """
        Show work in process files in the list widget.
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
                    
    def double_clicked_item(self,item):
        """
        Run by double-clicking a file in the list widget
        """
        _, _, _, version, wip_path, _, _ = self.get_tablewidget_data()

        file_name = item.text()
        file_path = f"{wip_path}/scenes/{version}/{file_name}"
        print (file_path)

        # If no file
        if file_name == "No File":
            self.msg_box("NoFile")
            return
        
        # Seperate DCCs running by file extension
        ext = file_name.split(".")[-1]
        if ext == "mb":
            subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {file_path}'],start_new_session=True)
        elif ext == "hip":
            self.msg_box("FX")
        elif ext == "nknc":
            self.run_nuke_nknc(file_path)


    def run_nuke_nknc(self, file_path):
        """
        Method for executing a Nuke (Non-Commercial)
        """
        nuke_path = 'source /home/rapa/git/pipeline/env/nuke.env && /opt/nuke/Nuke15.1v1/Nuke15.1 --nc'
        command = f"{nuke_path} {file_path}" 
        subprocess.Popen(command, shell=True)



    def click_right_menu(self,pos):
        """
        Floating right-click options.
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

    def get_tablewidget_data(self):
        """
        Get datas from the selected table widget.
        """

        # Get sequence name from table widgets.
        widget = self.table.cellWidget(self.click_row, 0)
        if not widget :
            return
        seq_label = widget.findChild(QLabel, "seq_name")
        seq_name_of_table = seq_label.text() 

        # Match the sequence name taken from the data and table widget.
        for project_name, seq_data_dict in self.projects_data_dict.items():
            selected_tree_item = self.tree.currentItem() 
            if selected_tree_item.childCount() > 0: # in the case of parent.
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
                selected_project = selected_tree_item.parent().text(0) # The parent of the selected item in the tree (Project name of the selected sequence)
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


    def make_new_scene(self):
        """
        When "New Scene", a new scene (w001) is created and opened with the correct dcc for each part,
        or if it is already there, a warning window says it is working.
        """
        self.ui.listWidget.clear()

        seq_name, task, _, version, wip_path, _, ver_path = self.get_tablewidget_data()

        self.sg_cls.sg_shot_task_status_update(seq_name, task) # Shotgrid Backend

        # Create Directory
        folder_list = ["scenes", "sourceimages", "cache", "images"]
        for folder in folder_list:
            os.makedirs(f"{wip_path}/{folder}/{version}", exist_ok=True)

        # Empty scene path to copy
        empth_file_path = os.path.dirname(__file__)

        # For Layout, Animation, Lighting Artist, create if you don't have a wip file and run the file.
        if task in ["ly", "ani", "lgt"]: 
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.mb"):
                shutil.copy(os.path.join(empth_file_path, ".emptymaya.mb"), os.path.join(ver_path, ".emptymaya.mb")) # Copy a template file
                os.rename(f"{ver_path}/.emptymaya.mb", f"{ver_path}/{seq_name}_{version}_w001.mb") # Specify File Name
                subprocess.Popen(["/bin/bash", "-i", "-c", f'shot_maya {ver_path}/{seq_name}_{version}_w001.mb'],start_new_session=True) # Execute a file
                return
            self.msg_box("Wip Status Error")

        # For FX Artist, create if you don't have a wip file and run the file.
        elif task == "fx":
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.hip"):
                self.msg_box("FX")
                return
            self.msg_box("Wip Status Error")

        # For Comp Artist, create if you don't have a wip file and run the file.
        elif task  in ["prc", "cmp"]:
            if not os.path.exists(f"{ver_path}/{seq_name}_{version}_w001.nknc"):
                shutil.copy(os.path.join(empth_file_path, ".emptynuke.nknc"), os.path.join(ver_path, ".emptynuke.nknc")) # Copy a template file
                os.rename(f"{ver_path}/.emptynuke.nknc", f"{ver_path}/{seq_name}_{version}_w001.nknc") # Specify File Name
                file_path = f"{ver_path}/{seq_name}_{version}_w001.nknc"
                self.run_nuke_nknc(file_path) # Execute a file
                return
            self.msg_box("Wip Status Error")
        
        else:
            print ("You are not a Artist.")


        self.set_listwidget()

    def make_new_wip_version(self): # Version up the work in process files.

        _, task, _, _, _, _, ver_path = self.get_tablewidget_data()
        
        # Define extension names by step.
        if task in ["ly", "ani", "lgt"]:
            ext = "mb"
        elif task == "fx":
            ext = "hip"
        elif task  in ["prc", "cmp"]:
            ext = "nknc"

        # If you don't have a path or file, raise a message window before you work.
        if not os.path.exists(ver_path):
            self.msg_box("NoFile")
            return
        wip_files = os.listdir(ver_path)
        if not wip_files:
            self.msg_box("NoFile")
            return
        
        # Create a versioned file if you have a work in process file.
        last_wip_file = sorted(wip_files)[-1]
        
        match = re.search(rf'_w(\d+)\.{ext}', last_wip_file)
        wip_num = int(match.group(1))
        wip_ver_up = wip_num + 1
        new_wip_num = f"_w{wip_ver_up:03d}.{ext}"

        new_wip_file = last_wip_file.replace(match.group(0), new_wip_num)
        shutil.copy(os.path.join(ver_path, last_wip_file), os.path.join(ver_path, new_wip_file))

        self.set_listwidget()

    def open_shotgrid_site(self): # Open the Shotgird Site.

        shotgrid_url = "https://4thacademy.shotgrid.autodesk.com/projects/"
        webbrowser.open(shotgrid_url)

    def open_current_path(self):
        """
        Method to open the file of current version.
        """
        _, _, _, _, _, _, ver_path = self.get_tablewidget_data()

        if not os.path.exists (ver_path):
            self.msg_box("No Path")
            return
        subprocess.call(["xdg-open", ver_path]) # Linux

    def version_up_for_retake(self):
        """
        When a published file is retaken, the new ver folder and the method
        by which the file is created on the wipe server.
        """
       
        seq_name, task, status, _, wip_path, pub_path, _ = self.get_tablewidget_data()

        self.sg_cls.sg_shot_task_status_update(seq_name, task) # Shotgrid Backend

        # Define extension names by step.
        if task in ["ly", "ani", "lgt"]:
            ext = "mb"
        elif task == "fx":
            ext = "hip"
        elif task == ["prc", "cmp"]:
            ext = "nknc"

        if status == "re":
            pub_files = os.listdir(pub_path)
            last_pub_file = sorted(pub_files)[-1]

            # Increase the version of the file in pub when retaken.
            match = re.search(rf'_v(\d+)\.{ext}', last_pub_file)
            ver_num = int(match.group(1))
            ver_up_num = ver_num + 1
            new_ver_num = f"v{ver_up_num:03d}"

            # Create a Path.
            folder_list = ["scenes", "sourceimages", "cache", "images"]
            for folder in folder_list:
                os.makedirs(f"{wip_path}/{folder}/{new_ver_num}", exist_ok=True)

            new_ver_path = f"{wip_path}/scene/{new_ver_num}"

            # Copy files to the work in process path.
            shutil.copy(os.path.join(pub_path, last_pub_file), os.path.join(new_ver_path, f"{seq_name}_{new_ver_num}_w001.{ext}"))
            
            # Open new wip files to different programs for each DCCs.
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


    def refresh(self):
        self.clear_ui()
        self.reload_data()

    def clear_ui(self): # Empty the ui, when refreshed.
        self.tree.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.ui.listWidget.clear()

    def reload_data(self): # Reloads the data, when refreshed.
        self.get_task_data()
        self.set_treewidget()
    

    # Raise Error Message
    def msg_box(self, message_type):
    
        if message_type == "WipStatusError":
            QMessageBox.critical(self, "Error", "You are already working on it.", QMessageBox.Yes)
        if message_type == "StatusError":
            QMessageBox.critical(self, "Error", "It is not in the 'Retake' state, please check the status.", QMessageBox.Yes)
        if message_type == "NoFile":
            QMessageBox.critical(self, "Error", "File Not Found", QMessageBox.Yes)
        if message_type == "NoPath":
            QMessageBox.critical(self, "Error", "Path has not been created. Please do 'New Scene' first.", QMessageBox.Yes)
        if message_type == "FX":
            QMessageBox.critical(self, "FX", "Wip file to be worked on.",QMessageBox.Yes)


 

    
if __name__=="__main__": 
    app = QApplication(sys.argv)
    win = ShotLoader()
    win.show()
    app.exec() 
