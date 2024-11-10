import sys
import os
import re
import subprocess    
import datetime
import threading
from functools import partial
import nuke
from shotgun_api3 import Shotgun
from shotgun_api import ShotgunApi
from nuke_api import NukeApi

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
        # self.user_id = os.environ["USER_ID"] 

        self.sg_cls = ShotgunApi()
        self.nk_cls = NukeApi()

        self.make_ui()
        
        self.get_selected_nodes()
        self.set_table_result_widget()

        self.event_func()


    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/nuke_upload.ui"
        self.ui_file = QFile(ui_file_path)
        self.make_ui_center()

    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        
    def get_selected_nodes(self):   # 선택한 노드가 있는지 확인
        selected_nodes = nuke.selectedNodes()
        if not selected_nodes:
            nuke.message("선택한 노드가 없습니다.")
            return
        self.check_node_count(selected_nodes)
        
    def check_node_count(self,selected_nodes): # 선택한 노드가 하나인지 확인
        selected_nodes = nuke.selectedNodes()
        if not len(selected_nodes) == 1:
            nuke.message("하나의 노드만 선택해주세요")
            return
        selected_node = selected_nodes[0]
        
        self.check_node_class(selected_node)

    def check_node_class(self,selected_node): # 선택한 노드가 Write 노드인지 , Write노드면 Read노드가 연결되어있는지 확인
        if not selected_node.Class() == "Write":
            nuke.message("Write노드를 선택해주세요")
            return
        node_name = selected_node.name()
        if not self.nk_cls.check_read_node_connection(node_name):
            nuke.message("Write 노드가 연결된 Read 노드가 없습니다.")
            return
        self.show_ui_with_node_name(node_name)
        
    def show_ui_with_node_name(self,node_name): # 위에 과정을 다 거치면 ui를 띄우기
        self.ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(self.ui_file, self)
        self.ui.label_node_name.setText(node_name)
        self.setWindowTitle("Nuke Uploader")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint) # UI 최상단 고정
        self.ui_file.close()     


    def event_func(self):
        self.ui.pushButton_render.clicked.connect(self.push_render_button)
        self.table_result.cellDoubleClicked.connect(self.double_click_result_table_widget)

        self.ui.pushButton_upload.clicked.connect(self.sg_status_update)
        self.ui.pushButton_upload.clicked.connect(self.sg_thumbnail_upload)
        self.ui.pushButton_upload.clicked.connect(self.sg_mov_upload)



    def get_index(self,row,_):
        self.row = row

    def set_table_result_widget(self):
        self.table_result = self.ui.tableWidget_result
        self.table_result.setRowCount(1) 
        self.table_result.setColumnCount(1)
        self.table_result.setColumnWidth(0, 470)
        self.table_result.setRowHeight(0, 50)
        self.table_result.setEnabled(False)
        self.table_result.setEditTriggers(QTableWidget.NoEditTriggers)

    def push_render_button(self):

        render_path = nuke.root().name().replace("scenes","images")
        if not render_path:
            os.makedirs(render_path)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001
        file_name = render_path.split("/")[-1]
        
        # BRK_0010_v001_w001.nknc
        render_file_name = file_name.replace(".nknc",".%04d.jpg")
        # BRK_0010_v001_w001.%04d.jpg
        full_render_path = render_path.replace(file_name,render_file_name)
        print(full_render_path)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.%04d.jpg
        
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
        print(render_file_path)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.%04d.jpg
        
        split_path = render_file_path.split("/")
        project = split_path[4]                               # Moomins
        task = split_path[8]                              # cmp
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001
        mov_file_path = render_file_path.replace(".%04d.jpg",".mov")

        mov_file_name = os.path.basename(mov_file_path)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.mov
        artist_name = "juseok"                                         # user_id 를 임포트 받아서 해야한다.
        frame_range = f"{start_frame}-{end_frame}"                  # 1001-1050 
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
                               stdout=subprocess.PIPE,   # python 코드를 읽을수 있게 하는 코드
                               stderr=subprocess.STDOUT, # 오류메세지 표준출력s
                               universal_newlines=True,  # 줄바꿈 자동
                               shell=True
                               )
        print(mov_file_path)
        # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/cmp/wip/images/v001

        self.mov_file_path = mov_file_path
        nuke.message("Render Complete")

        self.make_table_widget_result(mov_file_path)
        # self.delete_jpg_file(mov_file_path)



        
    def delete_jpg_file(self,mov_file_path):
        """
        mov와 jpg가 있는 폴더에 jpg 첫번째파일(썸네일)을 제외하고
        나머지 jpg 파일들을 삭제하고 테이블위젯에 데이터를 보내는 함수        
        """
        render_path = os.path.dirname(mov_file_path)
        pattern = re.compile(r'(\d{4})\.jpg$')              # %04d.jpg 로 패턴을 잡는다.
        result_image_path = None
        for filename in os.listdir(render_path):
            match = pattern.search(filename)
            if match:
                frame_number = match.group(1)               # (\d{4}) 4자리 숫자를 반환.
                if frame_number != "1001":
                    remove_file_path = os.path.join(render_path, filename)
                    os.remove(remove_file_path)
        files = os.listdir(render_path)
        for file in files:
            print(file)
            _,ext = os.path.splitext(file)
            if ext == ".jpg":
                result_image_path = os.path.join(render_path,file)
                break

        if not result_image_path:
            return None
        
        self.thumbnail_path = result_image_path
        
        self.make_table_widget_result(mov_file_path)

    def double_click_result_table_widget(self): # 더블클릭시 동영상 재생
        try:
            process = subprocess.Popen(["vlc", self.mov_file_path])
        except:
            nuke.message("파일이 없습니다.")

    def make_table_widget_result(self,path):
        self.table_result.setEnabled(True)
        # /home/rapa/wib/Moomins/seq/BRK/BRK_0010/cmp/wib/images/v001/BRK_0010_v001_w001.mov
        container_widget = QWidget()
        grid_layout = QGridLayout()
        container_widget.setLayout(grid_layout)
        self.ui.tableWidget_result.setCellWidget(0, 0, container_widget)

        file_name = os.path.basename(path)    
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