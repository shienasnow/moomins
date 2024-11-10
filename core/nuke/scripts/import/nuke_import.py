# Maya Asset Importer (ly, ani, lgt)
import sys
import os
import subprocess
import nuke
from configparser import ConfigParser 
from datetime import datetime
from shotgun_api import ShotgunApi
from moomins.api_scripts.nuke_api import NukeApi
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
        self.nuke_api = NukeApi()
        self.make_ui()
        # self.user_id = 94 # 임시
        # __init__(user_id) 받아서 self.user_id = user_id
        self.current_shot_info()
        self.make_table_ui() # ini 파일 받아서 ui에 넣기

        self.row = None
        self.event_func()

        self.file_path = os.path.dirname(nuke.scriptName())
        self.dir_path = os.path.dirname(__file__)
        self.project = self.file_path.split("/")[4]
        self.seq_name = self.file_path.split("/")[6]
        self.seq_num = self.file_path.split("/")[7]

        self.row_idx = 0


    def event_func(self):
        self.ui.tableWidget.cellClicked.connect(self.get_row_idx)
        self.ui.tableWidget.cellClicked.connect(self.show_current_asset_info) # 테이블 위젯 아이템 클릭할 때마다 썸네일 보이게
        self.ui.pushButton_reload.clicked.connect(self.reload_sg)
        self.ui.pushButton_import.clicked.connect(self.import_assets)

    def make_ui(self):
        ui_file_path = self.dir_path + "/nuke_import.ui"
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


        self.ui.label_project.setText(self.project)
        self.ui.label_sq.setText(self.seq_name)
        self.ui.label_sqnum.setText(self.seq_num)

        lgt_pub_scenes_path = f"/home/rapa/pub/{self.project}/seq/{self.seq_name}/{self.seq_num}/lgt/pub/scenes"
        if not os.path.exists(lgt_pub_scenes_path):         # lgt task have not result
            return
        lgt_pub_version = sorted(os.listdir(lgt_pub_scenes_path))
        lgt_pub_nuke_file_path = f"{lgt_pub_scenes_path}/{lgt_pub_version[0]}"
        self.pub_nuke_data = [lgt_pub_nuke_file_path,lgt_pub_version]

    def set_resolution(self):
        project_res_data = self.sg_cls.get_project_res_to_project_name(self.project)
        project_res_width = project_res_data["sg_resolutin_width"]
        project_res_height = project_res_data["sg_resolution_height"]
        project_res = f"{project_res_width} x {project_res_height}"
        project_res_str = f"Project Resolution : {project_res}"
        self.ui.label_project_res.setText(project_res_str)

    def set_undistortion(self):
        un_size_data = self.sg_cls.get_shot_undistortion_size_to_seq_num(self.seq_num)
        un_size_width = un_size_data["sg_undistortion_width"]
        un_size_height = un_size_data["sg_undistortion_height"]
        un_size = f"{un_size_width} x {un_size_height}"
        un_size_str = f"Undistortion Size : {un_size}"
        self.ui.label_un_size.setText(un_size_str)

    def set_framerange(self):
        frame_range_data = self.sg_cls.get_shot_frame_range_to_seq_num(self.seq_num)
        first_frame = int(frame_range_data["sg_cut_in"]) + 1000
        last_frame = int(frame_range_data["sg_cut_out"]) + 1000
        frame_range = f"{first_frame} - {last_frame}"
        frame_range_str = f"Frame range : {frame_range}"
        self.ui.label_frame_range.setText(frame_range_str)

    def set_duedate(self):
        due_date = self.sg_cls.get_shot_due_date_to_seq_num(94,self.seq_num)
        due_date_str = f"Due Date : {due_date}"
        self.ui.label_due_date.setText(due_date_str)
        self.add_row_datas()

    def get_row_idx(self,row,_):
        self.row = row

    def make_table_ui(self):
        img_path = self.dir_path + "/sourceimages/refresh.png"
        icon = QIcon(img_path)
        icon_size = QSize(20, 20)
        self.ui.pushButton_reload.setIcon(icon)
        self.ui.pushButton_reload.setIconSize(icon_size)

    def get_camera_data(self):
        camera_path = self.sg_cls.find_camera_path_to_seq_num(self.seq_num)
        if not camera_path:
            return
        linked_directory = os.readlink(camera_path)
        cam_dir = os.path.dirname(linked_directory)
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
        self.table_ui_contents(self.row_idx,cam_name,cam_version,cam_task,cam_ext,cam_,modified_time,frame_range,cam_status,camera_path)
        self.row_idx += 1

    def add_row_datas(self):
        self.get_camera_data()
        seq_frame_list,datas_list = self.sg_cls.get_assigned_Shot_num_lgt_task(self.seq_num)
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
                        name = j
            elif key == "updated_at":
                date = value.strftime("%Y-%m-%d")
            elif key == "sg_status_list":
                status = value
                nuke_file_path = self.nuke_api.find_nuke_file(self.pub_nuke_data)
                if os.path.isfile(nuke_file_path):
                    lgt_version = nuke_file_path.split("/")[-2]
                    nuke_full_file_name = os.path.basename(nuke_file_path)
                    nuke_file_name, ext = os.path.splitext(nuke_full_file_name)
                    ext = ext.replace(".", "")
                    exr_folder_path = os.path.dirname(nuke_file_path.replace("scenes", "images"))

                    task = "lgt"
                    frame_range = f"{first_frame}-{end_frame}"
                    self.table_ui_contents(nuke_file_name, lgt_version, task, ext, name, date, frame_range,
                                           status, nuke_file_path)
                    self.row_idx += 1
                else:
                    exr_folder_path = nuke_file_path.replace("scenes", "images")
                    lgt_version = nuke_file_path.split("/")[-1]
                    task = "lgt"
                    frame_range = f"{first_frame}-{end_frame}"
                files = os.listdir(exr_folder_path)
                if not files:
                    return
                for file in files:
                    check_path = os.path.join(exr_folder_path, file)
                    if os.path.isdir(check_path):
                        file_name = os.path.basename(check_path)
                        ext = "exr"
                        self.table_ui_contents(file_name, lgt_version, task, ext, name, date, frame_range,
                                               status, check_path)
                        self.row_idx += 1



    def find_image_icon(self,file_type):
        '''
        if get file type return file type image path
        '''
        sourceimages_ini_file_path = os.path.join(self.dir_path,"sourceimages.ini")
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


    def table_ui_contents(self,file_name,version,task,ext,name,date,frame_range,status,full_path):
        '''
        if get datas import datas in ui...
        '''

        container_widget = QWidget()
        h_layout = QHBoxLayout()
        grid_layout = QGridLayout()

        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.insertRow(self.row_idx)
        self.ui.tableWidget.setColumnWidth(self.row_idx, 400)
        self.ui.tableWidget.setRowHeight(self.row_idx, 70)



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
        self.ui.tableWidget.setCellWidget(self.row_idx, 0, container_widget) # 테이블 위젯의 row_idx 행과 0열에 container_widget을 삽입



    def show_current_asset_info(self):
        """
        get select row info
        """

        image_path = None
        container = self.ui.tableWidget.cellWidget(self.row, 0)
        if container:
            path_label = container.findChild(QLabel, "label_lgt_pub_path")

            if not path_label:
                return
            path = path_label.text()
            if os.path.isdir(path):              #exr 폴더일때
                image_path = self.nuke_api.convert_jpg_to_exr(path)
            else:
                if path.split(".")[-1] == "abc":
                    image_path = self.find_image_icon("mov")

                elif path.split(".")[-1] in ["nknc","nk"]:
                    image_path = self.find_image_icon("none")


        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(320, 180)
            self.ui.label_thumbnail.setPixmap(scaled_pixmap)
            self.ui.label_thumbnail.setGeometry(420,60, 320, 180)


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

                if checkbox and checkbox.isChecked():
                    checked_row_list.append(row)
        return checked_row_list

    # 버튼 누르면

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
