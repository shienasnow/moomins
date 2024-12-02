# Asset Uploader (Shot)
import sys
import os
import re
import subprocess
import datetime
from pprint import pprint

try:
    from PySide6.QtWidgets import QWidget,QApplication,QLabel
    from PySide6.QtWidgets import QGridLayout,QTableWidget,QMessageBox
    from PySide6.QtWidgets import QApplication,QAbstractItemView, QVBoxLayout
    from PySide6.QtWidgets import QHBoxLayout
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile,Qt,QTimer
    from PySide6.QtGui import QPixmap, QGuiApplication
    from shiboken6 import wrapInstance
except:
    from PySide2.QtWidgets import QWidget,QApplication,QLabel
    from PySide2.QtWidgets import QGridLayout,QTableWidget,QMessageBox
    from PySide2.QtWidgets import QApplication,QAbstractItemView, QVBoxLayout
    from PySide2.QtWidgets import QHBoxLayout
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtCore import QFile,Qt,QTimer
    from PySide2.QtGui import QPixmap, QGuiApplication
    from shiboken2 import wrapInstance

from moomins.api_scripts import capturecode
from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi

sys.path.append("/home/rapa/git/pipeline/api_scripts")
sys.path.append("/usr/local/lib/python3.6/site-packages")



class AssetUpload(QWidget):

    def __init__(self,parent=None):
        super(AssetUpload, self).__init__(parent)

        self.sg_api = ShotgunApi()
        self.maya_api = MayaApi()

        self.get_env_info()
        self.connect_sg()
        self.make_ui()
        self.set_input_path()
        self.set_text_label()
        self.event_func()

    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv() # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"

    def set_input_path(self):

        current_file_path = self.maya_api.get_current_maya_file_path()
        # /home/rapa/wip/Moomins/asset/character/jane/mod/wip/scenes/v002/jane_v002_w001.mb

        artist_name = self.sg_api.get_artist_name(self.user_id)
        split_path = current_file_path.split("/")
        project = split_path[4]
        asset_type = split_path[6]
        asset_name = split_path[7]
        task = split_path[8]
        open_file_name = os.path.basename(current_file_path)               # dami_v001_w001.mb
        open_file_path = os.path.dirname(current_file_path)                # /home/rapa/wip/Marvelous/asset/Character/dami/modeling/wip/scenes/v001
        only_file_name,_=  os.path.splitext(open_file_name) # dami_v001_w001, .mb
        version = only_file_name.split("_")[1]    # v001

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"
        self.render_data_list = [render_file_path, only_file_name]
        self.file_data_list = [project, only_file_name, task, artist_name, asset_name, asset_type]

    def make_ui(self):

        self.file_path = os.path.dirname(__file__)
        ui_file_path = self.file_path + "/asset_uploader.ui"

        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Asset Uploader")
        ui_file.close()

        self.table = self.ui.findChild(QTableWidget, "tableWidget")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout = QGridLayout(self)
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.setMinimumSize(400, 550)
        self.make_ui_center()

    def set_text_label(self):
        project, only_file_name, task, artist_name, asset_name, asset_type = self.file_data_list
        version = only_file_name.split("_")[1]    # v001
        self.task = task
        self.version = version
        self.project = project

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"
        pattern = re.compile(f"asset/([^/]+?)/{asset_name}") # Gets the filetype between asset/ and /asset_name.
        match = pattern.search(render_file_path)
        if not match:
            return
        asset_type = match.group(1)

        self.ui.label_asset_name.setText(asset_name)
        self.ui.label_asset_type.setText(asset_type)
        self.ui.label_version.setText(version)
        self.ui.label_ext.setText("mb")

    def event_func(self):
        self.ui.pushButton_set.clicked.connect(self.push_set_turn_table_button)
        self.ui.pushButton_render.clicked.connect(self.playblast_render)
        self.ui.pushButton_capture.clicked.connect(self.push_capture_image_button)
        self.table.cellDoubleClicked.connect(self.double_click_table_widget)

        # Backend
        self.ui.pushButton_upload.clicked.connect(self.sg_status_update)
        self.ui.pushButton_upload.clicked.connect(self.sg_thumbnail_upload)
        self.ui.pushButton_upload.clicked.connect(self.sg_mov_upload)



    def push_set_turn_table_button(self):

        selected_objects = self.maya_api.get_selected_object()
        if not selected_objects:
            self.raise_message_box("None Select Object")
            return

        self.maya_api.get_camera_transform

    def playblast_render(self):
        """
        An object group is selected, a camera is created, and a key is given.
        """

        project,only_file_name,task,artist_name,asset_name,asset_type = self.file_data_list
        version = only_file_name.split("_")[1]    # v001

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"
        render_icon_path = self.image_path + "mov.png"
        
        start_frame = 1
        end_frame = 100  
        image_file_path = f"{render_file_path}/{only_file_name}"
        camera_transform = self.maya_api.get_camera_transform()

        # Execute Playblast Render for Asset.
        self.maya_api.render_asset_playblast(start_frame, end_frame, image_file_path, camera_transform)

        self.add_row_to_table("Rendering", render_icon_path)
        self.raise_message_box("*"*10, "Render Complete")
        self.make_mov_use_ffmpeg()

    def make_mov_use_ffmpeg(self):
        project,only_file_name,task,artist_name,asset_name,asset_type = self.file_data_list
        version = only_file_name.split("_")[1] # v001

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"

        input_file = sorted(os.listdir(render_file_path))[0] # dami_v001_w001.0001.jpg
        print(input_file)
        replace_file = input_file.replace("0001","%04d") # dami_v001_w001.%04d.jpg
        command_file = f"{render_file_path}/{replace_file}"

        project,asset_type,asset_name,task,version,artist_name = self.file_data_list
        resolution = "scale=1920:1080"
        font_path = "/home/rapa/문서/font/CourierPrime-Regular.ttf"
        padding = "drawbox=x=0:y=0:w=iw:h=ih*0.07:color=black:t=fill,drawbox=x=0:y=ih*0.93:w=iw:h=ih*0.07:color=black:t=fill"
        gamma = "-gamma 2.2"
        framerate = "-framerate 24"
        codec = "-c:v prores_ks"
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        left_top_text = f"drawtext=fontfile={font_path}:text={asset_name}:x=10:y=10:fontsize=50:fontcolor=white@0.7"
        mid_top_text = f"drawtext=fontfile={font_path}:text={project}:x=(1920-text_w)/2:y=10:fontsize=50:fontcolor=white@0.7"
        right_top_text = f"drawtext=fontfile={font_path}:text={date}:x=(1920-text_w)-10:y=10:fontsize=50:fontcolor=white@0.7"
        left_bot_text = f"drawtext=fontfile={font_path}:text={task}:x=10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        mid_bot_text = f"drawtext=fontfile={font_path}:text={only_file_name}:x=(1920-text_w)/2:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        right_bot_text = f"drawtext=fontfile={font_path}:text={artist_name}:x=(1920-text_w)-10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"

        command_list = [
            "ffmpeg",
            gamma,
            framerate,
            f"-i {command_file}",
            f"-vf '{padding},{resolution},{left_top_text},{mid_top_text},{right_top_text},{left_bot_text},{mid_bot_text},{right_bot_text}'",
            codec,
            f"{self.full_path}",
            "-y"
        ]

        command = " ".join(command_list) # Combine lists separated by spaces

        process = subprocess.Popen(command, 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               shell=True
                               )

        for line in process.stdout:
            print(line, end='')

        # Delete jpg made with playblast by using a pattern with .%04d.jpg.
        pattern = re.compile(r'\.\d{4}\.jpg$')
        for filename in os.listdir(render_file_path):
            if pattern.search(filename):
                remove_file_path = f"{render_file_path}/{filename}"
                os.remove(remove_file_path)

        process.wait()



    def call_back_capture(self,value):

        if value == True:
            self.timer = QTimer()
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(lambda: self.add_row_to_table("Capture", self.capture_path))
            self.timer.start(1000)
            print("complete")

    def push_capture_image_button(self):

        project,only_file_name,task,artist_name,asset_name,asset_type = self.file_data_list
        version = only_file_name.split("_")[1] # v001

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"

        capture_name =  only_file_name + ".jpg"
        self.capture_path = f"{render_file_path}/{capture_name}"
        print(self.capture_path) # /home/rapa/wip/Moomins/asset/character/jane/mod/wip/images/v002/jane_v002_w001.jpg

        self.capture = capturecode.Capture(self.capture_path)   
        self.capture.SIGNAL_CAPTURE.connect(self.call_back_capture)  
        self.capture.show()

    def raise_message_box(self,message_type):

        if message_type == "NoneSelectObject":
            QMessageBox.critical(self, "Error", "None Selected objectgroup", QMessageBox.Yes)
        if message_type == "ImageRenderComplete":
            QMessageBox.information(self, "Complete", "Image Render Complete", QMessageBox.Ok)
        if message_type == "NoneFile":
            QMessageBox.critical(self, "Error", "No File.", QMessageBox.Yes)

    def double_click_table_widget(self):
        select_index = self.table.currentRow()
        if select_index == 0:
            try:
                subprocess.Popen(["vlc", self.full_path])
            except FileNotFoundError:
                self.raise_message_box("NoneFile")
        else:
            try:
                subprocess.Popen(['xdg-open', self.capture_path])
            except FileNotFoundError:
                self.raise_message_box("NoneFile")

    def add_row_to_table(self,type,icon_path):

        project,only_file_name,task,artist_name,asset_name,asset_type = self.file_data_list
        version = only_file_name.split("_")[1] # v001

        render_file_path = f"/home/rapa/wip/{project}/asset/{asset_type}/{asset_name}/{task}/wip/images/{version}"
        self.full_path = f"{render_file_path}/{only_file_name}.mov"

        if type == "Rendering":
            path = self.full_path
            row_idx = 0
            ext = "mov"
        else:
            path = icon_path
            row_idx = 1
            ext = "jpg"
        thumbnail_image_path = icon_path
        row_count = self.table.rowCount()
        if row_idx >= row_count:
            self.table.setRowCount(row_idx + 1)

        self.make_table_hard_coding(row_idx, thumbnail_image_path, task, asset_name, version, ext, path)
        self.selected_asset_name = asset_name
        print(asset_name)
        print(self.selected_asset_name)

    def make_ui_center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def make_table_hard_coding(self, row_idx, thumbnail_image_path, task, asset_name, version, ext, path):
        self.table.setRowCount(2) 
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 400)
        self.table.setRowHeight(0, 100)
        self.table.setRowHeight(1, 100)

        container_widget = QWidget()
        final_layout = QHBoxLayout(container_widget)

        label_icon_image = QLabel()
        pixmap = QPixmap(thumbnail_image_path)
        if pixmap.isNull():
            print(f"Failed to retrieve the image : {thumbnail_image_path}")
        else:
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label_icon_image.setPixmap(scaled_pixmap)
            label_icon_image.setAlignment(Qt.AlignLeft)
            label_icon_image.setFixedSize(90, 80)
        
        label_task = QLabel(f"Task: {task}")
        label_asset_name = QLabel(f"Asset: {asset_name}")
        label_version = QLabel(f"Version: {version}")
        label_ext = QLabel(f"ext: {ext}")

        # Layout Settings
        info_layout = QGridLayout()
        info_layout.addWidget(label_task, 0, 0)
        info_layout.addWidget(label_asset_name, 0, 1)
        info_layout.addWidget(label_version, 1, 0)
        info_layout.addWidget(label_ext, 1, 1)

        # Add to final layout.
        final_layout.addWidget(label_icon_image)
        final_layout.addLayout(info_layout)

        # Set up a container widget in the table.
        self.table.setRowHeight(row_idx, 100)
        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget)




# Backend (Run by pressing the upload button)
    def sg_status_update(self):
        """
        Find the status field that meets the two conditions by finding the asset id, task id,
        and change the status to 'pub'.
        """
        self.sg_api.sg_asset_status_update_pub(self.selected_asset_name, self.task)

    def sg_thumbnail_upload(self):
        """
        Upload thumbnail image in the image field that fits the task id.
        """
        png_path = self.capture_path
        self.sg_api.sg_upload_image(png_path)

    def sg_mov_upload(self):
        """
        Upload the confirmation mov to the shot grid.
        """
        project_id = self.sg_api.get_project_id_by_name(self.project)

        comment = self.ui.plainTextEdit_comment.toPlainText()
        print(f"Check the comments to be posted :{comment}")

        self.sg_api.sg_asset_upload_mov(project_id, self.version, comment, self.user_id, self.full_path)



if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = AssetUpload()
    win.show()
    app.exec()