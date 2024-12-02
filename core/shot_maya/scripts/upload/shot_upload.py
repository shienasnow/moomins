# Shot Upload
import sys
import os
import re
import subprocess
import datetime
from pprint import pprint

try:
    from PySide6.QtWidgets import QWidget,QApplication,QLabel
    from PySide6.QtWidgets import QGridLayout,QTableWidget,QMessageBox
    from PySide6.QtWidgets import QAbstractItemView
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile,Qt,QTimer
    from PySide6.QtGui import QPixmap
    from shiboken6 import wrapInstance
except:
    from PySide2.QtWidgets import QWidget,QApplication,QLabel
    from PySide2.QtWidgets import QGridLayout,QTableWidget,QMessageBox
    from PySide2.QtWidgets import QAbstractItemView
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtCore import QFile,Qt,QTimer
    from PySide2.QtGui import QPixmap
    from shiboken2 import wrapInstance

from moomins.api_scripts import capturecode
from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi

sys.path.append("/home/rapa/git/pipeline/api_scripts")
sys.path.append("/usr/local/lib/python3.6/site-packages")



class ShotUpload(QWidget):

    def __init__(self):
        super().__init__()

        self.sg_api = ShotgunApi()
        self.maya_api = MayaApi()

        self.connect_sg()
        self.make_ui()
        self.set_text_label()
        self.event_func()

    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv()  # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"

    def get_current_file_path(self):

        current_file_path = self.maya_api.get_current_maya_file_path()

        open_file_name = os.path.basename(current_file_path)  # AFT_0010_v001_w001.mb
        open_file_path = os.path.dirname(current_file_path)   # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/scene/v001

        return open_file_name,open_file_path

    def set_text_label(self):
        file_name,file_path = self.get_current_file_path()
        
        only_file_name,_ext = os.path.splitext(file_name)               # AFT_0010_v001_w001,.mb
        split_file_name = only_file_name.split("_")
        seq = split_file_name[0]
        seq_num = split_file_name[0] + "_" + split_file_name[1]         # AFT_0010
        version = split_file_name[2]                                    # v001
        ext = _ext.replace(".","")                                      # .mb => mb
        split_path = file_path.split("/")                               # Moomins
        project = split_path[4]
        task = split_path[8]

        artist_name = self.get_artist_name()

        self.ui.label_project.setText(project)
        self.ui.label_seq_num.setText(seq_num)
        self.ui.label_version.setText(version)
        self.ui.label_ext.setText(ext)

        frame_range =  self.maya_api.get_maya_frame_range()

        file_data_list = [project, only_file_name, task, artist_name, frame_range, seq, seq_num]
        
        self.project = project
        self.selected_seq_num = seq_num
        self.version = version
        self.task = task
        self.seq_name = seq
        
        return file_data_list

    def make_ui(self):
        self.file_path = os.path.dirname(__file__)
        ui_file_path = self.file_path + "/shot_uploader.ui"

        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Shot Uploader")
        ui_file.close()

        self.table = self.ui.findChild(QTableWidget, "tableWidget")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout = QGridLayout(self)
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.setMinimumSize(400, 550)

    def event_func(self):
        self.ui.pushButton_render.clicked.connect(self.playblast_render)
        self.ui.pushButton_capture.clicked.connect(self.push_capture_image_button)
        self.table.cellDoubleClicked.connect(self.double_click_table_widget)

        # Backend
        self.ui.pushButton_upload.clicked.connect(self.sg_status_update)
        self.ui.pushButton_upload.clicked.connect(self.sg_thumbnail_upload)
        self.ui.pushButton_upload.clicked.connect(self.sg_mov_upload)



    def playblast_render(self):
        """
        An object group is selected, a camera is created, and a key is given.
        """
        file_data_list = self.set_text_label()
        project,only_file_name,task,artist_name,frame_range,seq,seq_num = file_data_list

        render_file_path = f"/home/rapa/wip/{project}/seq/{seq}/{seq_num}/{task}/wip/images/{self.version}"
        image_file_path =  f"{render_file_path}/{only_file_name}"

        start_frame_str= frame_range.split("-")[0]
        end_frame_str = frame_range.split("-")[1]
        start_frame = int(float(start_frame_str))
        end_frame = int(float(end_frame_str))

        if start_frame <=1000:
            start_frame += 1000
        if end_frame <=1000:
            start_frame += 1000

        self.mov_full_path = f"{render_file_path}/{only_file_name}.mov"

        # Execute Playblast Render for Shot.
        self.maya_api.render_shot_playblast(start_frame, end_frame, image_file_path)

        render_icon_path = self.image_path + "mov.png"
        self.add_row_to_table("Rendering", render_icon_path)

        print(os.listdir(render_file_path))
        self.msg_box("*"*10, "Render Complete!")

        self.make_mov_use_ffmpeg()

    def make_mov_use_ffmpeg(self):
        file_data_list = self.set_text_label()
        project,only_file_name,task,artist_name,frame_range,seq,seq_num = file_data_list

        render_file_path = f"/home/rapa/wip/{project}/seq/{seq}/{seq_num}/{task}/wip/images/{self.version}"

        input_file = sorted(os.listdir(render_file_path))[0] # AFT_0010_v001_0001.jpg
        replace_file = input_file.replace("1001","%04d")     # AFT_0010_v001_%04d.jpg
        command_file = f"{render_file_path}/{replace_file}"

        startnumber = "-start_number 1001"

        resolution = "scale=1920:1080"
        font_path = "/home/rapa/문서/font/CourierPrime-Regular.ttf"
        padding = "drawbox=x=0:y=0:w=iw:h=ih*0.07:color=black:t=fill,drawbox=x=0:y=ih*0.93:w=iw:h=ih*0.07:color=black:t=fill"
        gamma = "-gamma 2.2"
        framerate = "-framerate 24"
        codec = "-c:v prores_ks"
        date = datetime.datetime.now().strftime("%Y-%m-%d") # Render Date

        frame_data = f"%{{n}}/{frame_range}:start_number=1001"

        left_top_text = f"drawtext=fontfile={font_path}:text={only_file_name}:x=10:y=10:fontsize=50:fontcolor=white@0.7"
        mid_top_text = f"drawtext=fontfile={font_path}:text={project}:x=(1920-text_w)/2:y=10:fontsize=50:fontcolor=white@0.7"
        right_top_text = f"drawtext=fontfile={font_path}:text={date}:x=(1920-text_w)-10:y=10:fontsize=50:fontcolor=white@0.7"
        left_bot_text = f"drawtext=fontfile={font_path}:text={artist_name}:x=10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        mid_bot_text = f"drawtext=fontfile={font_path}:text={task}:x=(1920-text_w)/2:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        right_bot_text = f"drawtext=fontfile={font_path}:text={frame_data}:x=(1920-text_w)-10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"

        command_list = [
            "ffmpeg",
            gamma,
            framerate,
            startnumber,
            f"-i {command_file}",
            f"-vf '{padding},{resolution},{left_top_text},{mid_top_text},{right_top_text},{left_bot_text},{mid_bot_text},{right_bot_text}'",
            codec,
            f"{self.mov_full_path}",
            "-y"
        ]

        # Combine lists separated by spaces
        command = " ".join(command_list)
        process = subprocess.Popen(command, 
                               stdout=subprocess.PIPE,   # code that allows python code to be read
                               stderr=subprocess.STDOUT, # Error Message Standard Output
                               universal_newlines=True,  # Automatic line modulation
                               shell=True
                               )


        for line in process.stdout:
            print(line, end='')

        pattern = re.compile(r'\.\d{4}\.jpg$') # Delete a pattern made of playblast by catching a pattern with .%04d.jpg
        for filename in os.listdir(render_file_path):
            if pattern.search(filename):
                remove_file_path = f"{render_file_path}/{filename}"
                print(remove_file_path)
                os.remove(remove_file_path)

        process.wait()



    def call_back_capture(self,value):
        
        if value == True:
            self.timer = QTimer()
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(lambda: self.add_row_to_table("Capture", self.capture_path))     # 두개의 인자를 전달하기위해 lambda를 썼다. # partial이 안되서 다른방법을 찾아봤음.
            self.timer.start(1000)
            print("complete")

    def push_capture_image_button(self):

        file_data_list = self.set_text_label()
        project, only_file_name, task, artist_name, frame_range, seq, seq_num = file_data_list
        render_file_path = f"/home/rapa/wip/{project}/seq/{seq}/{seq_num}/{task}/wip/images/{self.version}"
        print(f"Check Render Path : {render_file_path}")

        capture_name = only_file_name + ".jpg"

        self.capture_path = f"{render_file_path}/{capture_name}"
        print(self.capture_path) # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/images/v001/AFT_0010_v001.jpg

        self.capture = capturecode.Capture(self.capture_path)   
        self.capture.SIGNAL_CAPTURE.connect(self.call_back_capture)  
        self.capture.show()

    def msg_box(self,message_type): # Raise the message
    
        if message_type == "NoneSelectCamera":
            QMessageBox.critical(self, "Error", "None Selected Camera", QMessageBox.Yes)
        if message_type == "ImageRenderComplete":
            QMessageBox.information(self, "Complete", "Image Render Complete", QMessageBox.Ok)
        if message_type == "NoneFile":
            QMessageBox.critical(self, "Error", "File Not Found", QMessageBox.Yes)

    def double_click_table_widget(self):
        select_index = self.table.currentRow()
        if select_index == 0:
            try:
                subprocess.run(["vlc", self.mov_full_path])
            except FileNotFoundError:
                self.msg_box("NoneFile")
        else:
            try:
                print("Open FIle.")
                subprocess.Popen(['xdg-open', self.capture_path])
            except FileNotFoundError:
                self.msg_box("NoneFile")

    def add_row_to_table(self,type,icon_path):
        file_data_list = self.set_text_label()
        
        project,only_file_name,task,artist_name,frame_range,seq,seq_num = file_data_list
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        version = only_file_name.split("_")[2]
        
        if type == "Rendering":
            path = self.mov_full_path
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

        # seq_num ,version , task, ext , artistname , date
        self.make_table_hard_coding(row_idx, thumbnail_image_path,seq_num ,version , task, ext , artist_name , date)

    def make_table_hard_coding(self,row_idx, thumbnail_image_path,seq_num ,version , task, ext , artist_name , date): # 하드코딩한 함수...
        """
        Make UI hard
        """

        print(row_idx, thumbnail_image_path,seq_num ,version , task, ext , artist_name , date)

        self.table.setRowCount(2) 
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 420)
        

        container_widget = QWidget()
        grid_layout = QGridLayout()
        container_widget.setLayout(grid_layout)
        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget)

        for i in range(2):
            self.table.setRowHeight(i, 100)

        label_icon_image = QLabel() 
        pixmap = QPixmap(thumbnail_image_path)
        scaled_pixmap = pixmap.scaled(80, 80)
        label_icon_image.setAlignment(Qt.AlignCenter)
        label_icon_image.setPixmap(scaled_pixmap)
        label_icon_image.setFixedSize(100,80)

        label_seq_num = QLabel()                                                                    
        label_seq_num.setText(seq_num)
        label_seq_num.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_seq_num.setObjectName("seq_num")
        label_seq_num.setStyleSheet("font-size: 12px;")
        label_seq_num.setFixedSize(90, 20)       
        
        label_task = QLabel()
        label_task.setText(task)
        label_task.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_task.setObjectName("task")
        label_task.setStyleSheet("font-size: 12px;")
        label_task.setFixedSize(90, 20)
              
        label_version = QLabel()
        label_version.setText(version)
        label_version.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_version.setObjectName("version")
        label_version.setStyleSheet("font-size: 12px;")
        label_version.setFixedSize(90, 20)
        
        label_ext = QLabel()
        label_ext.setText(ext)
        label_ext.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label_ext.setObjectName("ext")
        label_ext.setStyleSheet("font-size: 12px;")
        label_ext.setFixedSize(90, 20)       
        
        label_artist_name = QLabel()
        label_artist_name.setText(artist_name)
        label_artist_name.setAlignment(Qt.AlignCenter)
        label_artist_name.setObjectName("artist_name")
        label_artist_name.setStyleSheet("font-size: 12px;")
        label_artist_name.setFixedSize(90, 20)       
        
        label_date = QLabel()
        label_date.setText(f"Pub date : {date}")
        label_date.setAlignment(Qt.AlignCenter)
        label_date.setObjectName("date")
        label_date.setStyleSheet("font-size: 12px;")
        label_date.setFixedSize(180, 20)       
        
        grid_layout.addWidget(label_icon_image, 0, 0)
        grid_layout.addWidget(label_seq_num, 0, 1)
        grid_layout.addWidget(label_version, 0, 2)
        grid_layout.addWidget(label_task, 0, 3)
        grid_layout.addWidget(label_ext, 0, 4)
        grid_layout.addWidget(label_artist_name, 1, 1)
        grid_layout.addWidget(label_date, 1, 2, 1, 3)



# Backend (Run by pressing the upload button)
    def sg_status_update(self):
        """
        Find the status field that meets the two conditions by finding the seq id, task id,
        and change the status to 'pub'.
        """
        self.sg_api.sg_shot_status_update_pub(self.selected_seq_num, self.task)

    def sg_thumbnail_upload(self):
        """
        Upload thumbnail image in the image field that fits the task id
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

        self.sg_api.sg_shot_upload_mov(project_id, self.version, comment, self.user_id, self.mov_full_path)


if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = ShotUpload()
    win.show()
    app.exec()