# Shot Upload
import sys
import os
import re
import subprocess
import datetime
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
from pprint import pprint
from capture import capturecode

from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi

sys.path.append("/home/rapa/git/pipeline/api_scripts")
sys.path.append("/usr/local/lib/python3.6/site-packages")



class ShotUpload(QWidget):

    def __init__(self):
        super().__init__()
        self.sg_api = ShotgunApi()
        self.maya_api = MayaApi()
        self.get_env_info()
        self.connect_sg()
        self.make_ui()
        self.set_text_label()
        self.event_func()

    def input_path(self):


        ex_path = cmds.file(q=True, sn=True)
        # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/scene/v001/AFT_0010_v001_w001.mb

        open_file_name = os.path.basename(ex_path)  # AFT_0010_v001_w001.mb
        open_file_path = os.path.dirname(ex_path)   # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/scene/v001
        return open_file_name,open_file_path

    def set_text_label(self):
        file_name,file_path = self.input_path()
        
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

        # Moomin_path = "/home/rapa/test_image/Moomin.jpg"
        # Moomin_path = self.file_path + "/sourceimages/Moomin.jpg"
        # pixmap = QPixmap(Moomin_path)
        # scaled_pixmap = pixmap.scaled(80, 80)
        # self.ui.label_Moomin.setPixmap(scaled_pixmap)

        self.ui.label_project.setText(project)
        self.ui.label_seq_num.setText(seq_num)
        self.ui.label_version.setText(version)
        self.ui.label_ext.setText(ext)

        start_frame = cmds.playbackOptions(query=True, min=True)
        end_frame = cmds.playbackOptions(query=True, max=True)
        start_frame = int(float(start_frame))
        end_frame = int(float(end_frame))
        frame_range = f"{start_frame}-{end_frame}"
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
        self.ui.pushButton_render.clicked.connect(self.push_render_button)
        self.ui.pushButton_capture.clicked.connect(self.push_capture_image_button)
        self.table.cellDoubleClicked.connect(self.double_click_table_widget)
        
        self.ui.pushButton_upload.clicked.connect(self.sg_status_update)
        self.ui.pushButton_upload.clicked.connect(self.sg_thumbnail_upload)
        self.ui.pushButton_upload.clicked.connect(self.sg_mov_upload)

    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv()  # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"


    def push_render_button(self):   # 카메라가 생성되고 오브젝트 그룹이 잡히면서 키만 들어가야한다.
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

        render_icon_path = "/home/rapa/git/pipeline/sourceimages/mov.png"
        selected_objects = cmds.ls(selection=True)                                                                  # 선택한 오브젝트가 없으면 돌아가라.
        if not selected_objects:
            self.msg_box("NoneSelectCamera")
            return

        cmds.playbackOptions(min=start_frame, max=end_frame)                                                  # 현재 마야의 프레임 가져오기.    
        selected_objects = cmds.ls(selection=True, type='camera')

        if selected_objects:                                                # 선택된 아이템 중 카메라를 반환합니다.
            self.camera = selected_objects[0]
        file_format = "jpg"

        cmds.playblast(
        startTime=start_frame,              # 시작프레임
        endTime=end_frame,                  # 끝프레임
        format="image",                     # 포맷을 image로 설정
        filename=image_file_path,           # 이미지 이름이 포함된 총 파일 경로.
        widthHeight=(1920, 1080),           # 이미지 해상도 설정.        # 동영상이 왜 깨지는지 모르겠음
        sequenceTime=False,
        clearCache=True,
        viewer=False,                       # 플레이블라스트 후 바로 재생하지 않음
        showOrnaments=False,                # UI 요소 숨김
        fp=4,                               # 프레임 패딩 ex) _0001
        percent=100,                        # 해상도 백분율
        compression=file_format,            # 코덱 설정
        quality=100,                        # 품질 설정
        )

        self.add_row_to_table("Rendering",render_icon_path)
        print(os.listdir(render_file_path))
        self.msg_box("ImageRenderComplete")

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


    # @Slot
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

    def connect_sg(self):
        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"

        self.sg = self.sg_api.Shotgun(URL,
                                SCRIPT_NAME,
                                API_KEY)

    def get_artist_name(self):
        filter = [["id", "is", self.user_id]]
        field = ["name"]
        artist_info = self.sg.find_one("HumanUser", filters=filter, fields=field)
        # print(artist_info) # {'type': 'HumanUser', 'id': 105, 'name': 'Dami Kim'}
        artist_name = artist_info["name"]
        # print(artist_name)

        return artist_name


# Backend : upload 버튼 누르면 샷그리드에 썸네일과 mov 올리고, status업데이트
    def sg_status_update(self): # seq_num_id, task id 찾는 과정 포함
        print("sg_status_update 함수 실행")

        # seq id 구하기
        seq_filter = [["code", "is", self.selected_seq_num]] # 현재 작업 중인 시퀀스 넘버 ex.OPN_0010
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        self.selected_seq_num_id = seq_info["id"]

        # task id 구하기 (ly, ani, lgt)
        step = self.sg.find_one("Step",[["code", "is", self.task]], ["id"])
        step_id = step["id"] # 277 (ly의 step)

        # seq_id, task_id 조건에 맞는 status 필드 찾기
        filter =[
            ["entity", "is", {"type": "Shot", "id": self.selected_seq_num_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                 ] 
        field = ["id"]
        task_info = self.sg.find_one("Task", filters=filter, fields=field)
        print(task_info)
        self.task_id = task_info["id"]

        self.sg.update("Task", self.task_id, {"sg_status_list": "pub"})
        print(f"Asset 엔티티에서 {self.task_id}의 status를 pub으로 업데이트합니다.") # publish에서는 fin으로 바꾸기

    def sg_thumbnail_upload(self): # task id에 맞는 이미지 필드에 썸네일 jpg 업로드
        print("sg에 썸네일 이미지와 컨펌용 mov를 업로드합니다.")
        self.sg.upload("Task", self.task_id, self.capture_path, "image")

    def sg_mov_upload(self):
        print("sg에 컨펌용 mov를 업로드합니다.")

        # 프로젝트 id 찾기
        filter = [["name", "is", self.project]]
        field = ["id"]
        project_info = self.sg.find_one("Project", filters=filter, fields=field)
        project_id = project_info["id"]

        comment = self.ui.plainTextEdit_comment.toPlainText()
        print(f"올릴 코멘트 내용 확인 :{comment}")

        # print(self.seq_name) # AFT
        # print(self.selected_seq_num) # AFT_0010
        # print(self.selected_seq_num_id) # 1353
        # print(self.task_id) # 6328

        # Version Entity
        version_data = {
            "project":{"type" : "Project", "id" : project_id},
            "code" : self.version,
            "description" : comment,
            "entity" : {"type": "Shot", "id": self.selected_seq_num_id}, # Entity에 연결 (시퀀스 이름)#################################
            "sg_task" : {"type": "Task", "id": self.task_id},  # sg_task (시퀀스 넘버)
            "sg_status_list" : "pub"
        }
        new_version = self.sg.create("Version", version_data) # Add Version 생성
        version_id = new_version["id"]

        self.sg.update("Version", version_id, {"user" : {"type" : "HumanUser", "id" : self.user_id}}) # artist 업로드
        self.sg.upload("Version", version_id, self.mov_full_path, "sg_uploaded_movie") # mov 업로드



if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = ShotUpload()
    win.show()
    app.exec()