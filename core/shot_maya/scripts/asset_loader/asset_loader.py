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

        self.get_env_info()
        self.sg_api = ShotgunApi
        self.maya_api = MayaApi

        self.make_ui()
        self.event_func() # Event Function Collection

        self.get_shot_info_from_current_directory() # Extract data from the current working file path.
        self.current_dict = self.maya_api.get_reference_assets() # reference asset name, path in the current scene.
        self.classify_task() # Pass tasks to classyfy_task functions so that different functions can be executed by task.
        self.compare_assets()

        self.get_linked_cam_link_info()
        self.set_undistortion_size() # render resolution setting
        self.set_frame_range() # frame range setting

    def event_func(self):
        self.ui.tableWidget.itemSelectionChanged.connect(self.selected_asset_thumbnail) # Click on the table widget item to see the thumbnail.
        self.label_img.doubleClicked.connect(self.open_thumbnail) # If you double-click on the thumbnail, open the image.

        self.ui.pushButton_import.clicked.connect(self.get_checked_row) # If you click the Import button, import the asset of the selected list.
        self.ui.pushButton_refresh.clicked.connect(self.refresh_sg) # Refresh shot grid interworking by pressing the Refresh button.

    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv()  # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"

    def get_user_name(self):
        # Find user_name with user_id
        user_datas = self.sg_api.get_datas_by_user_id(self.user_id)
        self.user_name = user_datas["name"]

    def get_shot_info_from_current_directory(self): # Extract project, seq_name, seq_num, task, version, shot_id.

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
        print(f"Current Task Shot Number : {self.seq_num} (id : {self.shot_id})")



# Task(ly, any, lgt) Run another function that separates and creates ini.
    def classify_task(self):
        print(f"Current Task : {self.task}")

        if self.task == "ly":
            print("Start the layout task.\nLoad rig or lookdev assets and render cam")
            self.get_ly_assigned_assets() # Find the information of the assets assigned to sequence number and make ini.
            self.make_table_ui_for_ly() # Get ini and put it in UI.

        elif self.task == "ani":
            print("Start the animation task.\nLoad layout assets and render cam.")
            self.get_lgt_assgined_assets() # Find the information of the ly, ani, and fx tasks with the same sequence number and make ini.
            self.make_table_ui_for_ani()

        elif self.task == "lgt":
            print("Start the lighting task.\nLoad layout, animation, fx assets and render cam.")
            self.get_lgt_assgined_assets()
            self.make_table_ui_for_lgt()

        else: # Prevent working if you are not a Shot Maya worker
            print("You are not in a working status to load an asset from Maya.")
            QMessageBox.about(self, "Warning", "'Load Assets' can only be run on Shot jobs using Maya.\nPlease check the task you are working on.")



# Layout : Find information about assets tagged in shot number (mod.mb or rig.mb)
    def get_ly_assigned_assets(self): # Get the asset ids tagged in shot, make them a list, and hand them over to the next function.
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

        self.make_asset_ini_for_ly(asset_id_list) # Hand over the asset id list assigned to shot.

    def make_asset_ini_for_ly(self, asset_id_list): # Put the information found based on asset id into "self.asset.ini".
        self.asset_ini_for_ly = ConfigParser()

        # Add Rendercam section first.
        linked_cam_info_dict = self.get_linked_cam_link_info()
        self.asset_ini_for_ly["rendercam"] = {}
        self.asset_ini_for_ly["rendercam"]["asset status"] = linked_cam_info_dict["asset status"]
        self.asset_ini_for_ly["rendercam"]["asset pub directory"] = linked_cam_info_dict["asset pub directory"]
        self.asset_ini_for_ly["rendercam"]["asset artist"] = linked_cam_info_dict["asset artist"]
        self.asset_ini_for_ly["rendercam"]["asset task"] = linked_cam_info_dict["asset task"]
        self.asset_ini_for_ly["rendercam"]["asset file ext"] = linked_cam_info_dict["asset file ext"]
        self.asset_ini_for_ly["rendercam"]["asset version"] = linked_cam_info_dict["asset veresion"]
        self.asset_ini_for_ly["rendercam"]["asset pub date"] = linked_cam_info_dict["asset pub date"]

        # Add the modeling, lookdev assets to the next section of the camera.
        # Importing from SG Asset Entities: Name, Status, Task for each asset
        for asset_id in asset_id_list:
            # print (asset_id)
            # [1546, 1479, 1547]
            asset_info = self.sg_api.get_asset_info(asset_id)

            asset_info = asset_info[0]
            asset_name = asset_info["code"] # joker
            self.asset_ini_for_ly[asset_name] = {} # Use asset name as section.


            # Get Artist, step information with task ID (lkd, mod, rig alphabetical order).
            # Extract the ID of all tasks associated with Asset.
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


                # File directory, Published Date
                path_info, date_info = self.sg_api.get_path_info(task_id)

                path_description = str(path_info["sg_description"]) # Published file directory
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

        print("*"*20,"\nini Output for debugging", "*"*20)
        for section in self.asset_ini_for_ly.sections():
            for k, v in self.asset_ini_for_ly[section].items():
                print(f"{section}, {k}: {v}")
            #     # bat, asset status: wip
            #     # bat, asset pub directory: /home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v001/bat_v001.mb
            #     # bat, asset artist: junghyun yeom
            #     # bat, asset task: rig
            #     # bat, asset file ext: .mb
            #     # bat, asset version: v001
            #     # bat, asset pub date: 2024-08-23 17:21:08
            #     # joker, asset status: pub
            #     # joker, asset pub directory: /home/rapa/pub/Moomins/asset/character/joker/rig/pub/scenes/v001/joker_v001.mb
            #     # joker, asset artist: junghyun yeom
            #     # joker, asset task: rig
            #     # joker, asset file ext: .mb
            #     # joker, asset version: v001
            #     # joker, asset pub date: 2024-08-23 17:21:08


# Animation, Lighting: Find the information of ly, any, and fx corresponding to the same shot number.
    def get_lgt_assgined_assets(self): # Find the abc file path of ly, ani, fx corresponding to task id.
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

    def make_asset_ini_for_lgt(self, shot_asset_dict): # Create ini with information from files published by ly, ani, fx.
        self.asset_ini_for_lgt = ConfigParser()

        # Add Rendercam section first.
        linked_cam_info_dict = self.get_linked_cam_link_info()
        self.asset_ini_for_lgt["rendercam"] = {}
        self.asset_ini_for_lgt["rendercam"]["asset status"] = linked_cam_info_dict["asset status"]
        self.asset_ini_for_lgt["rendercam"]["asset pub directory"] = linked_cam_info_dict["asset pub directory"]
        self.asset_ini_for_lgt["rendercam"]["asset artist"] = linked_cam_info_dict["asset artist"]
        self.asset_ini_for_lgt["rendercam"]["asset task"] = linked_cam_info_dict["asset task"]
        self.asset_ini_for_lgt["rendercam"]["asset file ext"] = linked_cam_info_dict["asset file ext"]
        self.asset_ini_for_lgt["rendercam"]["asset version"] = linked_cam_info_dict["asset veresion"]
        self.asset_ini_for_lgt["rendercam"]["asset pub date"] = linked_cam_info_dict["asset pub date"]

        # Add the layout, animation, fx assets to the next section of the camera.
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

            # Parsing what you need on the ani path.
            self.asset_ini_for_lgt[asset_name] = {}
            self.asset_ini_for_lgt[asset_name]["asset pub directory"] = asset_directory # File directory
            self.asset_ini_for_lgt[asset_name]["asset task"] = asset_task # the asset's task
            self.asset_ini_for_lgt[asset_name]["asset file ext"] = file_ext # .abc
            self.asset_ini_for_lgt[asset_name]["asset version"] = self.version # v001
            self.asset_ini_for_lgt[asset_name]["asset artist"] = asset_artist # hyoeun seol
            self.asset_ini_for_lgt[asset_name]["asset status"] = asset_status # pub
            self.asset_ini_for_lgt[asset_name]["asset pub date"] = asset_pub_date # 2024-08-28 14:42:12

        # Check the output of self.asset_ini_for_lgt.
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
            # AFT_0010_ani, asset artist: hanbyeol park
            # AFT_0010_ani, asset status: wtg
            # AFT_0010_ani, asset pub date: 2024-08-28 14:42:06
            # AFT_0010_fx, asset pub directory: /home/rapa/pub/Moomins/seq/AFT/AFT_0010/fx/pub/scenes/v001/AFT_0010_fx_v001.abc
            # AFT_0010_fx, asset task: ly
            # AFT_0010_fx, asset file ext: .abc
            # AFT_0010_fx, asset version: v001
            # AFT_0010_fx, asset artist: seonil hong
            # AFT_0010_fx, asset status: wtg
            # AFT_0010_fx, asset pub date: 2024-08-28 14:42:12



# UI (Import required ini according to the current task and put it in the UI)
    def make_ui(self): # Floating ui and adding parts that need hard coding (icon, thumbnail).
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/asset_loader.ui"

        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.ui.show()
        self.setWindowTitle("Asset Loader")
        ui_file.close()

        # Create a double-clickable label and place it at the top of vereticalLayout_2.
        self.label_img = DoubleClickableLabel("THUMBNAIL")
        self.label_img.setFixedSize(320, 180) # 16:9 ratio fixed
        self.label_img.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.ui.verticalLayout_2.insertWidget(2, self.label_img)
        self.ui.label_artist.setText(self.user_name)

    def make_table_ui_for_ly(self): # Create as many containers as an asset and put ini information into the container.

        # Create one container as many as the number of assets (lkd, rig).
        row_count = len(self.asset_ini_for_ly.sections())
        self.ui.tableWidget.setRowCount(row_count)

        # Put the asset information collected in self.asset_ini_for_ly into each container.
        row_idx = 0
        for section in self.asset_ini_for_ly.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1

    def make_table_ui_for_ani(self): # Create a new configParser by extracting only ly from lgt ini.

        self.asset_ini_for_ani = ConfigParser()
        for section in self.asset_ini_for_lgt.sections():
            # if self.asset_ini_for_lgt.has_option(section, "asset task") and self.asset_ini_for_lgt.get(section, "asset task" == "ly"):
            if self.asset_ini_for_lgt.get(section, "asset task") == "ly":
                self.asset_ini_for_ani.add_section(section)
                for k, v in self.asset_ini_for_lgt.items(section):
                    self.asset_ini_for_ani.set(section, k, v)

        # Create a container for the number of assets.
        row_count = len(self.asset_ini_for_ani.sections())
        self.ui.tableWidget.setRowCount(row_count)

        # Put the asset information collected in self.asset_ini_for_ani into each container.
        row_idx = 0
        for section in self.asset_ini_for_ani.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1

    def make_table_ui_for_lgt(self): # Create a container as many as the number of assets (ly, ani, fx) and place ini information into the container.

        # Create one container for each asset(ly, any, fx)
        row_count = len(self.asset_ini_for_lgt.sections())
        self.ui.tableWidget.setRowCount(row_count)
        
        # Put the asset information collected in self.asset_ini_for_lgt into each container.
        row_idx = 0
        for section in self.asset_ini_for_lgt.sections():
            self.table_ui_contents(section, row_idx)
            row_idx += 1


# Return the dictionary containing the camera information of the last task linked to the rendercam.
    def get_linked_cam_link_info(self):

        shot_camera_directory = self.sg_api.get_link_camera_directory(self.shot_id)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/rendercam/AFT_0010_cam.abc

        if not os.path.islink(shot_camera_directory):
            print(f"{shot_camera_directory}is not a symbolic link.\nPlease check if rendercam exists and if it is linked.")
        linked_directory = os.readlink(shot_camera_directory)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/mm/pub/cache/v001/AFT_0010_mm_cam.abc
        linked_file_info = os.stat(linked_directory)

        # Last modification time of linked file
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

    def table_ui_contents(self, section, row_idx): # Hard coding what to put in UI container
        self.ui.tableWidget.setRowHeight(row_idx, 60)
        self.ui.tableWidget.setColumnCount(1)

        container_widget = QWidget()
        checkbox_layout = QVBoxLayout()

        # Create a check box and put it in checkbox_layout.
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("checkbox_import_asset")
        self.checkbox.setChecked(True) # By default, an asset that is not imported is checked by the check box.
        self.checkbox.setFixedWidth(20)

        checkbox_layout.addWidget(self.checkbox)

        # Select the ini file to use
        if self.task == "ly":
            ini = self.asset_ini_for_ly
        elif self.task == "ani":
            ini = self.asset_ini_for_ani
        elif self.task == "lgt":
            ini = self.asset_ini_for_lgt


        # Create grid layout and put it in h_ly.

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
        if ini[section]["asset artist"]: # Artist for last task
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

        # asset file ext
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

        # Add PushButton to the right of h_ly.
        update_layout = QHBoxLayout()
        pushButton_update = QPushButton("")
        pushButton_update.setMinimumWidth(45)
        pushButton_update.setMaximumWidth(45)
        pushButton_update.setText("Update") # Putting text in a button
        update_layout.addWidget(pushButton_update)
        
        current_asset_list = self.compare_assets() # Asset name imported into the current scene
        ref_node, current_version = self.get_version(section) # Asset version imported into the current scene

        # Compare Asset Versions
        if section in current_asset_list: # If it's imported (if it's in the Outliner)
            pushButton_update.setEnabled(False) # Disable the button
            self.checkbox.setChecked(False)     #  Uncheck

            print("*"*20, "Compare Versions")
            print(ini[section]["asset version"]) # AFT_0010_v001_w001.mb
            print(current_version) # v001

            if not ini[section]["asset version"] == current_version: # If it is updated after the import,
                # When the version extracted from the path ini (the path of the most recently published asset
                # called from shotgrid when the importer is turned on in the shotgrid)
                # and the version of the asset I already imported in the dictionary are the same,
                pushButton_update.setEnabled(True) # Activate the button

        else: # If it's not imported,
            pushButton_update.setEnabled(False) # Disable the button
            pushButton_update.setStyleSheet("QPushButton { background-color: transparent; border: none; }") # Hide the Update button transparently so that you don't see it.

        new_path = ini[section]["asset pub directory"]
        pushButton_update.clicked.connect(lambda: self.maya_api.update_reference_file_path(ref_node, new_path, pushButton_update))

        # Set h_ly in the container widget.
        layout = QHBoxLayout()
        layout.addLayout(checkbox_layout)
        layout.addLayout(assetname_artist_layout)
        layout.addLayout(asset_pub_date_layout)
        layout.addLayout(asset_version_task_layout)

        layout.addLayout(asset_status_fileext_layout)
        layout.addLayout(asset_pub_directory_layout)
        layout.addLayout(update_layout)

        container_widget.setLayout(layout)
        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget) # Insert container_widget in row "row_idx" and column 0 of the table widget



# Returns the asset path imported into the current scene as a reference.
    def get_version(self, asset_name):
        for k, v in self.current_dict.items():
            if v["asset_name"] == asset_name:
                return k, v["version"]
        return None, None

# Returns the asset name imported into the current scene as a reference to the list.
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
        
        # Assets to import
        # print(asset_name_list) # ['bat', 'car', 'joker', 'rock']

        # Imported assets
        current_asset_list = []
        for k, v in self.current_dict.items(): # The dictionary containing the asset name and path brought to the current scene as reference.
            asset_name_in_scene = v["asset_name"]

            # Include only the name of the asset that you imported into the current scene among the assets you need to import.
            if asset_name_in_scene in asset_name_list:
                current_asset_list.append(asset_name_in_scene)

        return current_asset_list



# Thumbnail ("No thumbnail" when it's not there yet)
    def selected_asset_thumbnail(self): # Extract and show the thumbnail (capture image) path of the selected asset.
        indexes = self.ui.tableWidget.selectedIndexes() # Use Indexes because it's multiple choices.

        for index in indexes:
            # Replace the path published by asset with the path with thumbnail images.
            widget = self.ui.tableWidget.cellWidget(index.row(), 0)   # Widgets for cells in rows "index.row()"" and 0 of the table widget
            a = widget.findChild(QLabel, "label_asset_pub_directory") # Text of QLabel corresponding to label_asset_pub_directory in asset ini.
            original_path = a.text()

            # Replace the path of the published file with the same path as the capture path of the shot uploader.
            # (It can be multiple, so use the last w version)
            if self.task == "ly":
                # Capture image path of the asset uploader : /home/rapa/wip/Moomins/asset/character/jane/mod/wip/images/v002/jane_v002_w001.jpg
                folder_path = original_path.replace("scenes", "images").replace(".mb", ".jpg").replace("pub", "wip")
                directory_path = os.path.dirname(folder_path)
                image_path_list  = glob(os.path.join(directory_path, "*.jpg"))
                print(f"Thumbnail image path : {image_path_list}")

                if len(image_path_list) == 0:
                    my_path = os.path.dirname(__file__)
                    self.image_path = my_path + "/sourceimages/no_thumbnail.jpg"
                else:
                    self.image_path = sorted(image_path_list)[-1]

            elif self.task in ["ani", "lgt"]:
                # Capture image path of the asset uploader  : /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/images/v001/AFT_0010_v001_w001.jpg
                folder_path = original_path.replace("cache", "images").replace(".abc", ".jpg").replace("pub", "wip")
                directory_path = os.path.dirname(folder_path)
                image_path_list = glob(os.path.join(directory_path, "*.jpg"))   
                print(f"Thumbnail image path : {image_path_list}")

                if len(image_path_list) == 0:
                    my_path = os.path.dirname(__file__)
                    self.image_path = my_path + "/sourceimages/no_thumbnail.jpg"
                else:
                    self.image_path = sorted(image_path_list)[-1]

            pixmap = QPixmap(self.image_path)
            sclaed_pixmap = pixmap.scaled(364, 216)
            self.label_img.setPixmap(sclaed_pixmap)

    def open_thumbnail(self): # If you double-click, open the thumbnail.
        my_path = os.path.dirname(__file__)
        no_thumbnail_path = my_path + "/sourceimages/no_thumbnail.jpg"

        if not self.image_path == no_thumbnail_path:
            subprocess.Popen(['xdg-open', self.image_path])



# Asset Import
# Click the Import button to import the asset, shader in the selected list.
    def get_checked_row(self): # Bring the checked rows to the list.
        checked_row_list = []
        row_count = self.ui.tableWidget.rowCount()

        for row in range(row_count):
            container = self.ui.tableWidget.cellWidget(row, 0)
            checkbox = container.findChild(QCheckBox, "checkbox_import_asset") # Find widgets in a container.

            if checkbox.isChecked():
                checked_row_list.append(row)

        self.get_selected_asset_list(checked_row_list)

    def get_selected_asset_list(self, checked_row_list): # Create a list with checked row asset paths.
        if self.task == "ly":
            ini = self.asset_ini_for_ly
        elif self.task == "ani":
            ini = self.asset_ini_for_ani
        elif self.task == "lgt":
            ini = self.asset_ini_for_lgt

        selected_list = []
        sections = ini.sections()
        for idx, section in enumerate(sections):

            if idx in checked_row_list: # Bring only checked sections.
                selected_item = ini[section]["asset pub directory"]
                selected_list.append(selected_item)

        # When the current task is ani
        # ['/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc',
        # '/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc']

        # When the current task is ly
        # ['/home/rapa/pub/Moomins/seq/AFT/AFT_0010/ly/pub/cache/v001/AFT_0010_ly_cam.abc',
        # '/home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v002/bat_v002.mb',...이하 생략]

        self.import_assets(selected_list) # Importing the assets and shades of the selected list into the scene.

    def import_assets(self, selected_list):
        print("Import the selected assets into the current scene.")

        for path in selected_list:
            reference_node = self.maya_api.import_reference_asset(path)
            if not reference_node:
                print (f"{path} Reference import failed.")
                continue

            self.get_link_shader_path(path, reference_node) # Import Shader

# Shader Import
    def get_link_shader_path(self, path, reference_node):
        print("Gets the final shader path linked to shader.ma and shader.json for each asset.")

        # /home/rapa/pub/Moomins/asset/character/bat/rig/pub/scenes/v002/bat_v002.mb - This Maya file path

        # /home/rapa/pub/Moomins/asset/prop/knife/lkd/pub/scenes/knife_lkd_shader_link.ma - Change each one like this
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
        print("Bring up the shader.ma file containing shader and shader.json containing shader assign information and attach shader to object.")
        self.maya_api.import_shader(shader_ma_path, shader_json_path)

    def set_undistortion_size(self): # Setting "Image Size" for render settings
        undistortion_height, undistortion_width = self.sg_api.get_undistortion_size(self.shot_id)

        self.maya_api.set_render_resolution(undistortion_height, undistortion_width)

    def set_frame_range(self): # Setting "Frame Range" for render settings
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
        print("Run a refresh\nClear the table and read the information from the shot grid again and put it in/")

        self.ui.tableWidget.clear() # Empty all rows of tableWidet

        # Recall shotgrid data and put it in the table.
        self.current_dict = self.maya_api.get_reference_assets() # Reference Asset name, path in the current scene
        self.classify_task() # Pass tasks to classyfy_task functions so that different functions can be executed by task.

        self.get_linked_cam_link_info()
        self.set_undistortion_size() # render resolution setting
        self.set_frame_range() # frame range setting




class DoubleClickableLabel(QLabel): # Double-clickable label objects

    doubleClicked = Signal() # Defining a Double Click Signal

    def __init__(self, parent=None):
        super(DoubleClickableLabel, self).__init__(parent)

    def mouseDoubleClickEvent(self, event):
        # It emits a signal when a double-click event occurs.
        super().mouseDoubleClickEvent(event)  # Default Event Processing
        self.doubleClicked.emit()  # Double click signal release



if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = AssetLoader()
    win.show()
    app.exec()