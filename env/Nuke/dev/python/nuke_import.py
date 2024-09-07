# Maya Asset Importer (ly, ani, lgt)
import sys
import os
import subprocess
import glob
import nuke
from configparser import ConfigParser 
from datetime import datetime
from pprint import pprint
from shotgun_api import ShotgunApi
try:
    from PySide6.QtWidgets import QApplication, QWidget, QGridLayout
    from PySide6.QtWidgets import QLabel, QCheckBox, QHBoxLayout
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtGui import QPixmap, QIcon,QGuiApplication
    from PySide6.QtCore import QFile, QSize, Qt
    from PySide6.QtCore import Signal
except:
    from PySide2.QtWidgets import QApplication, QWidget, QGridLayout
    from PySide2.QtWidgets import QLabel, QCheckBox, QHBoxLayout
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtGui import QPixmap, QIcon,QGuiApplication
    from PySide2.QtCore import QFile, QSize, Qt
    from PySide2.QtCore import Signal


class NukeImport(QWidget):

    def __init__(self):
        super().__init__()
        self.sg_cls = ShotgunApi()
        self.make_ui()
        # self.user_id = 94 # 임시
        # __init__(user_id) 받아서 self.user_id = user_id
        self.current_shot_info()
        self.make_table_ui() # ini 파일 받아서 ui에 넣기

        self.row = None
        self.event_func()

    def event_func(self):
        self.ui.tableWidget.cellClicked.connect(self.get_row_idx)
        self.ui.tableWidget.cellClicked.connect(self.show_current_asset_info) # 테이블 위젯 아이템 클릭할 때마다 썸네일 보이게
        self.ui.pushButton_reload.clicked.connect(self.reload_sg)
        self.ui.pushButton_import.clicked.connect(self.import_assets)


    def make_ui(self): 
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path + "/nuke_import.ui"
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.ui.show()
        self.setWindowTitle("Nuke Importer")
        ui_file.close()
        self.make_ui_center()
        
    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        
    def current_shot_info(self):
        my_path = nuke.scriptName()
        # my_path = "/home/rapa/wip/Moomins/seq/BRK/BRK_0010/cmp/wip/scenes/v001/BRK_0010_v001_w001.nknc"
        file_path = os.path.dirname(my_path)
        # file_path = "/home/rapa/wip/Moomins/seq/BRK/BRK_0010/cmp/wip/scenes/v001
        project = file_path.split("/")[4]
        seq_name = file_path.split("/")[6]
        seq_num = file_path.split("/")[7]

        self.ui.label_project.setText(project)
        self.ui.label_sq.setText(seq_name)
        self.ui.label_sqnum.setText(seq_num)

        lgt_pub_scenes_path = f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_num}/lgt/pub/scenes"
        if not os.path.exists(lgt_pub_scenes_path):         # lgt작업을 완료하지않았으면
            return
        lgt_pub_version = sorted(os.listdir(lgt_pub_scenes_path))  # v001
        lgt_pub_nuke_file_path = f"{lgt_pub_scenes_path}/{lgt_pub_version[0]}"
        
        self.pub_nuke_data = [lgt_pub_nuke_file_path,lgt_pub_version]
        project_res_data = self.sg_cls.get_project_res_to_project_name(project)
        project_res_width = project_res_data["sg_resolutin_width"]
        project_res_height = project_res_data["sg_resolution_height"]
        project_res = f"{project_res_width} x {project_res_height}"
        project_res_str = f"Project Resolution : {project_res}"
        
        
        un_size_data = self.sg_cls.get_shot_undistortion_size_to_seq_num(seq_num)
        un_size_width = un_size_data["sg_undistortion_width"]
        un_size_height = un_size_data["sg_undistortion_height"]
        un_size = f"{un_size_width} x {un_size_height}"
        un_size_str = f"Undistortion Size : {un_size}"
        
        
        
        frame_range_data = self.sg_cls.get_shot_frame_range_to_seq_num(seq_num)
        first_frame = int(frame_range_data["sg_cut_in"]) + 1000
        last_frame = int(frame_range_data["sg_cut_out"]) + 1000
        frame_range = f"{first_frame} - {last_frame}"
        frame_range_str = f"Frame range : {frame_range}"
        
        
        # user_id = 
        due_date = self.sg_cls.get_shot_due_date_to_seq_num(94,seq_num)
        
        due_date_str = f"Due Date : {due_date}"

        self.ui.label_project_res.setText(project_res_str)
        self.ui.label_un_size.setText(un_size_str)
        self.ui.label_frame_range.setText(frame_range_str)
        self.ui.label_due_date.setText(due_date_str)
        
        self.add_row_datas(seq_num)
        



    def get_row_idx(self,row,_):
        self.row = row

    def make_table_ui(self):
        my_path = os.path.dirname(__file__) # /home/rapa/env/maya/2023/scripts
        img_path = my_path + "/sourceimages/refresh.png"
        icon = QIcon(img_path)
        icon_size = QSize(20, 20)
        self.ui.pushButton_reload.setIcon(icon)
        self.ui.pushButton_reload.setIconSize(icon_size)

    def add_row_datas(self,seq_num):
        seq_frame_list,datas_list = self.sg_cls.get_assigned_Shot_num_lgt_task(seq_num)
        seq_frame = seq_frame_list[0]
        for key,value in seq_frame.items():
            if key == "sg_cut_in":
                first_frame = value
            elif key == "sg_cut_out":
                end_frame = value
        for key,value in datas_list[0].items():
            if key == "task_assignees":  #  value = [{'id': 94, 'name': '주석 박', 'type': 'HumanUser'}]
                for i,j in value[0].items():
                    if i == "name":
                        name = j                # "주석 박"
            elif key == "updated_at":
                date = value.strftime("%Y-%m-%d")
            elif key == "sg_status_list":
                status = value
        row_idx = 0
        # 카메라 경로 찾기
        camera_path = self.sg_cls.find_camera_path_to_seq_num(seq_num)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/rendercam/AFT_0010_cam.abc
        if not camera_path:
            return
        linked_directory = os.readlink(camera_path)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/mm/pub/cache/v001/AFT_0010_mm_cam.abc
        cam_dir = os.path.dirname(linked_directory)
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/mm/pub/cache/v001
        split_cam_path = cam_dir.split("/")
        cam_version = split_cam_path[-1]
        cam_task = split_cam_path[-4]
        cam_file_name = os.path.basename(linked_directory) 
        linked_file_info = os.stat(linked_directory)
        modified_timess = linked_file_info.st_mtime
        modified_times = datetime.fromtimestamp(modified_timess)
        modified_time = modified_times.strftime("%Y-%m-%d")
        
        cam_name,cam_ext = os.path.splitext(cam_file_name)
        cam_ext = cam_ext.replace(".","")
        cam_ = ""
        frame_range = ""
        cam_status = "fin"
        self.table_ui_contents(row_idx,cam_name,cam_version,cam_task,cam_ext,cam_,modified_time,frame_range,cam_status,camera_path)
        row_idx += 1
        
        
        
        # 누크파일 찾기
        nuke_file_path = self.find_nuke_file()
        print(nuke_file_path)
        if os.path.isfile(nuke_file_path): 
            lgt_version = nuke_file_path.split("/")[-2]
            nuke_full_file_name = os.path.basename(nuke_file_path)
            nuke_file_name,ext = os.path.splitext(nuke_full_file_name)
            ext = ext.replace(".","")
            exr_folder_path = os.path.dirname(nuke_file_path.replace("scenes","images"))
            # /home/rapa/pub/Moomins/seq/BRK/BRK_0010/lgt/pub/images/v001/
            task = "lgt"
            frame_range = f"{first_frame}-{end_frame}"
            self.table_ui_contents(row_idx,nuke_file_name,lgt_version,task,ext,name,date,frame_range,status,nuke_file_path)
            row_idx += 1
        else:
            exr_folder_path = nuke_file_path.replace("scenes","images")
            lgt_version = nuke_file_path.split("/")[-1]
            task = "lgt"
            frame_range = f"{first_frame}-{end_frame}"
        files = os.listdir(exr_folder_path)
        if not files:
            return
        for file in files:
            check_path = os.path.join(exr_folder_path,file)
            if os.path.isdir(check_path):
                file_name = os.path.basename(check_path)
                ext = "exr"
                self.table_ui_contents(row_idx,file_name,lgt_version,task,ext,name,date,frame_range,status,check_path)
                row_idx += 1

    
    def find_nuke_file(self): # 누크파일이 있는지 찾는 함수.
        lgt_pub_nuke_file_path,_ = self.pub_nuke_data
        # lgt_pub_nuke_file_path = "/home/rapa/pub/Moomins/seq/BRK/BRK_0010/lgt/pub/scenes/v001/"
        # seq_num = BRK_0010
        files = os.listdir(lgt_pub_nuke_file_path)
        nuke_file_path = ""
        for file in files:
            check_path = f"{lgt_pub_nuke_file_path}/{file}"
            if os.path.isfile(check_path):
                _,ext = os.path.splitext(file)
                ext = ext.replace(".","")
                if ext in ["nk","nknc"]:
                    nuke_file_path = check_path # /home/rapa/pub/Moomins/seq/BRK/BRK_0010/lgt/pub/scenes/v001/tttt.nknc
                else:
                    nuke_file_path = lgt_pub_nuke_file_path 
        print(nuke_file_path)
        return nuke_file_path                        
    def find_image_icon(self,file_type):    # file_type을 받아서 이미지path를 받아오는 함수

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
        image_path = config["icons"][icon_name]                # f"{path}/sourceimages/icon_name"

        return image_path
    def table_ui_contents(self,row_idx,file_name,version,task,ext,name,date,frame_range,status,full_path): # 하드 코딩

        container_widget = QWidget()
        h_layout = QHBoxLayout()
        grid_layout = QGridLayout()

        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.insertRow(row_idx)
        self.ui.tableWidget.setColumnWidth(row_idx, 400)
        self.ui.tableWidget.setRowHeight(row_idx, 70)
        
        
        
        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(20)
        self.checkbox.setFixedHeight(20)
        h_layout.addWidget(self.checkbox, alignment=Qt.AlignLeft) # 왼쪽에 체크박스 추가
        self.checkbox.toggled.connect(self.get_checked_row) # 체크박스 상태 변경 시 함수 호출

        
        
        label_icon_image = QLabel()
        image_path = self.find_image_icon(ext)
        logo_pixmap = QPixmap(image_path)
        scaled_pixmap = logo_pixmap.scaled(40, 40,Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_icon_image.setPixmap(scaled_pixmap)
        label_icon_image.setAlignment(Qt.AlignVCenter|Qt.AlignLeft)
        label_icon_image.setFixedSize(50,55)

        label_lgt_status = QLabel()
        status_image_path = self.find_image_icon(status)
        status_pixmap = QPixmap(status_image_path)
        scaled_pixmap = status_pixmap.scaled(30, 30,Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label_lgt_status.setPixmap(scaled_pixmap)
        label_lgt_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_status.setFixedSize(50, 30)
        # status에 따라서 아이콘으로 변경 필요

        label_lgt_artist = QLabel()
        label_lgt_artist.setObjectName("label_lgt_artist")
        label_lgt_artist.setText(name)
        label_lgt_artist.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_artist.setStyleSheet("font-size: 10px;")
        label_lgt_artist.setFixedSize(50, 30)

        label_lgt_task = QLabel()
        label_lgt_task.setObjectName("label_lgt_task")
        label_lgt_task.setText(task)
        label_lgt_task.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_task.setStyleSheet("font-size: 10px;")
        label_lgt_task.setFixedSize(50, 30)

        label_lgt_file_ext = QLabel()
        label_lgt_file_ext.setObjectName("label_lgt_file_ext")
        label_lgt_file_ext.setText(ext)
        label_lgt_file_ext.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_file_ext.setStyleSheet("font-size: 10px;")
        label_lgt_file_ext.setFixedSize(50, 30)

        label_lgt_version = QLabel()
        label_lgt_version.setObjectName("label_lgt_version")
        label_lgt_version.setText(version)
        label_lgt_version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_version.setStyleSheet("font-size: 10px;")
        label_lgt_version.setFixedSize(60, 30)

        label_lgt_pub_date = QLabel()
        label_lgt_pub_date.setObjectName("label_lgt_pub_date")
        label_lgt_pub_date.setText(f"Pub date : {date}")
        label_lgt_pub_date.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_lgt_pub_date.setStyleSheet("font-size: 10px;")
        label_lgt_pub_date.setFixedSize(150, 30)
        
        label_shot_num = QLabel()
        label_shot_num.setObjectName("label_shot_num")
        label_shot_num.setText(file_name)
        label_shot_num.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_shot_num.setStyleSheet("font-size: 10px;")
        label_shot_num.setFixedSize(150, 30)

        label_lgt_pub_path = QLabel()
        label_lgt_pub_path.setObjectName("label_lgt_pub_path")
        label_lgt_pub_path.setText(full_path)
        label_lgt_pub_path.setFixedSize(0, 0)
        label_lgt_pub_path.hide()
        

        grid_layout.addWidget(label_icon_image, 0, 0,2,1)  
        grid_layout.addWidget(label_shot_num, 0, 1)      
        grid_layout.addWidget(label_lgt_version, 0, 2)    
        grid_layout.addWidget(label_lgt_task, 0, 3)        
        grid_layout.addWidget(label_lgt_file_ext, 0, 4)     

        grid_layout.addWidget(label_lgt_pub_date, 1, 1, 2, 1)  
        grid_layout.addWidget(label_lgt_artist, 1, 3,3,1)      
        grid_layout.addWidget(label_lgt_status, 1, 4)      
        grid_layout.addWidget(label_lgt_pub_path, 1,2)

        h_layout.addLayout(grid_layout)
        h_layout.setStretch(1, 1)   
        
        container_widget.setLayout(h_layout)
        self.ui.tableWidget.setCellWidget(row_idx, 0, container_widget) # 테이블 위젯의 row_idx 행과 0열에 container_widget을 삽입

    def convert_jpg_to_exr_for_firstframe_use_ffmpeg(self,exr_path):
        """
        exr파일을 썸네일로 가져오기 어려워서
        누를때마다 exr 첫번째파일을 가져와서 jpg로 변환 시킨 후
        썸네일에 띄워주는 함수.
        """
        files = sorted(os.listdir(exr_path))
        if not files:
            return
        first_file = files[0]
        exr_file_path = os.path.join(exr_path,first_file)
        jpg_file_path = exr_file_path.replace(".exr", ".jpg")
        
        if os.path.exists(jpg_file_path):
            return jpg_file_path
        
        if not os.path.exists(exr_path):
            return ""
        command = [
            "ffmpeg",
            "-i", exr_file_path,
            "-vf", "eq=gamma=1.5,scale=iw:ih",
            "-q:v", "2",
            jpg_file_path
        ]
        try:
            subprocess.run(command, check=True)
            print(f"Successfully converted {exr_path} to {jpg_file_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to convert {exr_path} to {jpg_file_path}: {e}")
                
        return jpg_file_path
    
    def show_current_asset_info(self): 
        """
        선택한 row의 info를 가져와 path를 가져오는 함수.
        """
        
        image_path = None
        container = self.ui.tableWidget.cellWidget(self.row, 0)
        if container:
            path_label = container.findChild(QLabel, "label_lgt_pub_path")
            
            if not path_label:
                return
            path = path_label.text()
            if os.path.isdir(path):              #exr 폴더일때
                image_path = self.convert_jpg_to_exr_for_firstframe_use_ffmpeg(path)
            else:
                if path.split(".")[-1] == "abc":
                    print(path)
                    image_path = self.find_image_icon("mov")
                    print(image_path)
                    
                elif path.split(".")[-1] in ["nknc","nk"]:
                    print(path)
                    image_path = self.find_image_icon("none")
                    print(image_path)
                    
                
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(320, 180)
            self.ui.label_thumbnail.setPixmap(scaled_pixmap)
            self.ui.label_thumbnail.setGeometry(420,60, 320, 180)
            
            

                
    def get_checked_row(self):
        checked_row_list = []
        for row in range(self.ui.tableWidget.rowCount()):
            container = self.ui.tableWidget.cellWidget(row, 0)
            if container:
                h_layout = container.layout()
                checkbox = None
                for i in range(h_layout.count()):
                    widget = h_layout.itemAt(i).widget()
                    if isinstance(widget, QCheckBox):
                        checkbox = widget
                        break

                if checkbox and checkbox.isChecked():  # 체크박스가 존재하고 체크되어 있다면
                    checked_row_list.append(row)  # 행 번호를 리스트에 추가
        return checked_row_list

# 버튼 누르면
    def import_assets(self):

            row_list = self.get_checked_row()
            for row in row_list:
                container = self.ui.tableWidget.cellWidget(row, 0)
                if container:
                    path_label = container.findChild(QLabel, "label_lgt_pub_path")
                text = path_label.text()
                if os.path.exists(text):
                    if os.path.isdir(text):
                        exr_first_file = sorted(os.listdir(text))[0]
                        exr_last_file = sorted(os.listdir(text))[-1]
                        first_frame_str = exr_first_file.split(".")[1]
                        last_frame_str = exr_last_file.split(".")[1]
                        first_frame = int(first_frame_str)
                        last_frame = int(last_frame_str)
                        nuke.root()['first_frame'].setValue(first_frame)
                        nuke.root()['last_frame'].setValue(last_frame)
                        none_frame_name = exr_first_file.split(".")[0]
                        result_name = none_frame_name + ".####.exr"
                        result_exr_file_path = f"{text}/{result_name}"
                        node = nuke.nodes.Read(file=result_exr_file_path)
                        node["first"].setValue(first_frame)
                        node["last"].setValue(last_frame)
                        
                    elif os.path.isfile(text): # abc파일이나 nk 파일일때
                        if text.split(".")[-1] == "abc":
                            readgeo_node = nuke.createNode("ReadGeo")
                            readgeo_node["file"].setValue(text)
                            pass
                        elif text.split(".")[-1] in ["nknc","nk"]:
                            nuke.nodePaste(text)
                            for node in nuke.allNodes("Viewer"):
                                if node.name() != "Viewer1":
                                    nuke.delete(node)
                    else: 
                        return

    def reload_sg(self):
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(0)
        self.current_shot_info()
        
    

if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = NukeImport()
    win.show()
    app.exec()
    
    
# icon color white
# Project res => v
# frame range => 
# un size
# Due date
# 뭐 넣으면 좋을까
# Slate에 데이터넣는 api 있으면 좋을거같음.(ffmpeg) 
