import sys
import os
import re
import subprocess    
import datetime
import nuke
from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.nuke_api import NukeApi


try:
    from PySide6.QtWidgets import QApplication, QWidget, QTableWidget
    from PySide6.QtWidgets import QGridLayout,QLabel
    from PySide6.QtGui import Qt
    from PySide6.QtCore import QFile
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtGui import QGuiApplication
except:
    from PySide2.QtWidgets import QApplication, QWidget, QTableWidget
    from PySide2.QtWidgets import QGridLayout,QLabel
    from PySide2.QtGui import Qt
    from PySide2.QtCore import QFile
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtGui import QGuiApplication



class NukeUpload(QWidget):

    def __init__(self):
        super().__init__()
        self.user_id = os.environ["USER_ID"]
        self.sg_api = ShotgunApi()
        self.nuke_api = NukeApi()

        # Make UI
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/nuke_upload.ui"
        self.ui_file = QFile(ui_file_path)
        self.make_ui_center()

        self.table = self.ui.tableWidget_result
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setColumnWidth(0, 470)
        self.table.setRowHeight(0, 50)
        self.table.setEnabled(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.make_ui()

        self.check_before_open_ui()
        self.set_table_result_widget()

        # Event Function
        self.ui.pushButton_render.clicked.connect(self.push_render_button)
        self.table.cellDoubleClicked.connect(self.double_click_result_table_widget)
        self.ui.pushButton_upload.clicked.connect(self.sg_status_update)
        self.ui.pushButton_upload.clicked.connect(self.sg_thumbnail_upload)
        self.ui.pushButton_upload.clicked.connect(self.sg_mov_upload)


    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def check_before_open_ui(self):
        nodes = self.nuke_api.get_selected_nodes()
        if not nodes:
            return nuke.message("None Selected")
        if len(nodes) is not 1:
            return nuke.message("Select One Node")
        if self.nuke_api.get_node_class(nodes[0]) is not "Write":
            return nuke.message("Select Write Node")
        node_name = nodes[0].name()
        if not self.nuke_api.check_read_node_connection(node_name):
            return nuke.message("Connect Read Node")

        self.show_ui(node_name)


        
    def show_ui(self,node_name): # 위에 과정을 다 거치면 ui를 띄우기
        self.ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(self.ui_file, self)
        self.ui.label_node_name.setText(node_name)
        self.setWindowTitle("Nuke Uploader")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint) # UI 최상단 고정
        self.ui_file.close()     

    def get_index(self,row,_):
        self.row = row


    def push_render_button(self):

        render_path = nuke.root().name().replace("scenes","images")
        if not render_path:
            # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001
            os.makedirs(render_path)

        # BRK_0010_v001_w001.nknc
        file_name = render_path.split("/")[-1]

        # BRK_0010_v001_w001.%04d.jpg
        render_file_name = file_name.replace(".nknc",".%04d.jpg")

        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.%04d.jpg
        full_render_path = render_path.replace(file_name,render_file_name)

        start_frame = nuke.root().firstFrame()
        end_frame = nuke.root().lastFrame()
        node_name = self.ui.label_node_name.text().strip()
        write_node = nuke.toNode(node_name)
        write_node_path = write_node.knob("file").value()
        
        write_node.knob("file").setValue(full_render_path)
        write_node.knob("file_type").setValue("jpeg")
        
        nuke.execute(write_node, start_frame, end_frame)
        
        write_node.knob("file").setValue(write_node_path)

        self.make_mov_use_ffmpeg(full_render_path,start_frame,end_frame)

    def make_mov_use_ffmpeg(self,render_file_path,start_frame,end_frame):
        """
        jpg로 렌더한 파일들을 ffmpeg을 이용해 slate를 넣은
        mov로 변환시키는 함수.
        """
        split_path = render_file_path.split("/")
        project = split_path[4]                               # Moomins
        task = split_path[8]                              # cmp
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001
        mov_file_path = render_file_path.replace(".%04d.jpg",".mov")

        mov_file_name = os.path.basename(mov_file_path)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.mov
        artist_name = self.sg_api.get_name_by_id(user_id=self.user_id)
        frame_range = f"{start_frame}-{end_frame}"
        frame_data = f"%{{n}}/{frame_range}:start_number={start_frame}"
        

        resolution = "scale=1920:1080"
        font_path = "/home/rapa/문서/font/CourierPrime-Regular.ttf"
        padding = "drawbox=x=0:y=0:w=iw:h=ih*0.07:color=black:t=fill,drawbox=x=0:y=ih*0.93:w=iw:h=ih*0.07:color=black:t=fill"
        framerate = "-framerate 24"
        codec = "-c:v prores_ks"
        date = datetime.datetime.now().strftime("%Y-%m-%d") # 렌더링하는 날짜.
        start_number = "-start_number 1001"

        left_top_text = f"drawtext=fontfile={font_path}:text={mov_file_name}:x=10:y=10:fontsize=50:fontcolor=white@0.7"
        mid_top_text = f"drawtext=fontfile={font_path}:text={project}:x=(1920-text_w)/2:y=10:fontsize=50:fontcolor=white@0.7"
        right_top_text = f"drawtext=fontfile={font_path}:text={date}:x=(1920-text_w)-10:y=10:fontsize=50:fontcolor=white@0.7"
        left_bot_text = f"drawtext=fontfile={font_path}:text={artist_name}:x=10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        mid_bot_text = f"drawtext=fontfile={font_path}:text={task}:x=(1920-text_w)/2:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"
        right_bot_text = f"drawtext=fontfile={font_path}:text={frame_data}:x=(1920-text_w)-10:y=(1080-text_h)-10:fontsize=50:fontcolor=white@0.7"

        command_list = [
            "ffmpeg",
            framerate,
            start_number,
            f"-i {render_file_path}",
            f"-vf '{padding},{resolution},{left_top_text},{mid_top_text},{right_top_text},{left_bot_text},{mid_bot_text},{right_bot_text}'",
            codec,
            f"{mov_file_path}",
            "-y"
        ]

        # 리스트를 공백으로 구분하여 결합
        command = " ".join(command_list)
        process = subprocess.Popen(command, 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, # print Error message
                               universal_newlines=True,  # line change automatic
                               shell=True
                               )
        self.mov_file_path = mov_file_path
        nuke.message("Render Complete")

        self.make_table_widget_result(mov_file_path)

        # delete image option
        # self.delete_jpg_file(mov_file_path)



        
    def delete_jpg_file(self,mov_file_path):
        """
        This function delete jpg files.(remain thumnail image)
        if you don't want delete files, cancle this function
        """
        render_path = os.path.dirname(mov_file_path)
        pattern = re.compile(r'(\d{4})\.jpg$')              # %04d.jpg 로 패턴을 잡는다.
        result_image_path = None
        for filename in os.listdir(render_path):
            match = pattern.search(filename)
            if match:
                frame_number = match.group(1)               # (\d{4}) 4자리 숫자를 반환.
                if frame_number is not "1001":
                    remove_file_path = os.path.join(render_path, filename)
                    os.remove(remove_file_path)
        files = os.listdir(render_path)

        for file in files:
            _,ext = os.path.splitext(file)
            if ext is ".jpg":
                result_image_path = os.path.join(render_path,file)
                break

        if not result_image_path:
            return
        self.thumbnail_path = result_image_path
        
        self.make_mov_table(mov_file_path)

    def double_click_result_table_widget(self):
        '''
        if double Click, play mov file
        '''
        try:
            process = subprocess.Popen(["vlc", self.mov_file_path])
        except:
            nuke.message("None File.")

    def make_mov_table(self,mov_path):
        self.table.setEnabled(True)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.mov
        container_widget = QWidget()
        grid_layout = QGridLayout()
        container_widget.setLayout(grid_layout)
        self.ui.tableWidget_result.setCellWidget(0, 0, container_widget)

        file_name = os.path.basename(mov_path)
        label_path = QLabel()
        # label_path.setText(f"File name : {file_name}")
        label_path.setText(file_name)        
        label_path.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_path.setObjectName("path")
        label_path.setStyleSheet("font-size: 10px;")
        label_path.setFixedWidth(470)
        
        
        # grid_layout.addWidget(label_icon_image, 0, 0)
        grid_layout.addWidget(label_path, 0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(0, 1)



# Backend : 업로드 버튼 누르면 샷그리드에 썸네일과 mov, comment 올리고, status 업데이트
    def sg_status_update(self):
        current_file_path = nuke.scriptName() # /home/rapa2/wip/Moomins/seq/AFT/AFT_0010/cmp/wip/scenes/v001/AFT_0010_cmp_v001.nknc
        shot_num = current_file_path.split("/")[7] # AFT_0010
        task = current_file_path.split("/")[8] # cmp

        self.sg_cls.sg_status_update_nuke_upload(shot_num, task)

    def sg_thumbnail_upload(self): # task id에 맞는 이미지 필드에 썸네일 jpg 업로드
        capture_path = self.thumbnail_path

        current_file_path = nuke.scriptName()
        shot_num = current_file_path.split("/")[7] # AFT_0010
        task = current_file_path.split("/")[8] # cmp
        task_id = self.sg_cls.sg_status_update_nuke_upload(shot_num, task)

        self.sg_cls.sg_thumbnail_upload_nuke_upload(capture_path, task_id)

    def sg_mov_upload(self):
        current_file_path = nuke.scriptName()
        project = current_file_path.split("/")[4]
        version = current_file_path.split("/")[11]

        current_file_path = nuke.scriptName()
        shot_num = current_file_path.split("/")[7] # AFT_0010
        task = current_file_path.split("/")[8] # cmp
        task_id = self.sg_cls.sg_status_update_nuke_upload(shot_num, task)

        comment = self.ui.plainTextEdit_comment.toPlainText()
        print(f"올릴 코멘트 내용 확인 :{comment}")

        mov_full_path = self.mov_file_path

        self.sg_cls.sg_mov_upload_nuke_upload(project, comment, mov_full_path, version, task_id)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = NukeUpload()
    win.show()
    app.exec() 