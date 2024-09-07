
try:
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile
    from PySide6.QtGui import  Qt, QGuiApplication

except:
    from PySide2.QtWidgets import QApplication, QWidget
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtCore import QFile
    from PySide2.QtGui import  Qt, QGuiApplication

import os
import nuke
import shutil
import re


class NukePublish(QWidget):

    def __init__(self):
        super().__init__()


        path = os.path.dirname(__file__)
        ui_file_name = "nuke_publish.ui"
        ui_file_path = f"{path}/{ui_file_name}"   
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()                                      
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        self.center()


        #버튼 연결
        
        self.ui.pushButton_shotpub.clicked.connect(self.export_nuke_file)
        self.ui.pushButton_shotpub.clicked.connect(self.submit_render)
        self.setWindowTitle("Nuke Publish")

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        

        self.node_info()
        self.shot_info()


    def center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    
    def selected_nodes(self):
        
        selected_nodes = nuke.selectedNodes()

        # 선택된 노드가 없으면 경고 출력    
        if not selected_nodes:
            nuke.message("경고: 노드를 선택하세요!")
            return None
        else:
            # 선택된 노드가 'Write' 노드인지 확인
            for node in selected_nodes:
                if node.Class() != 'Write':
                    nuke.message("경고: 선택한 노드가 Write 노드가 아닙니다!")
                    return None
        return selected_nodes

    def node_info(self):
        
        nodes = self.selected_nodes()
             
        root_node = nuke.root()
        node = nodes[0]
        node_name = node["name"].value()
        # str_name = str(node_name)
        self.ui.node_name_text.setText(node_name)
        
        
        first_frame = int(root_node["first_frame"].value())
        str_first_frame = str(first_frame)
        self.ui.frist_frame_text.setText(str_first_frame)
        
        last_frame = int(root_node["last_frame"].value())
        str_last_frame = str(last_frame)
        self.ui.last_frame_text.setText(str_last_frame)
        
        color_space = node["colorspace"].value()
        self.ui.color_space_text.setText(color_space)
        
        self.shot_pub_func(node_name)
        return node_name , first_frame, last_frame
        
        
        
    def shot_info(self):
    
        file_path = nuke.scriptName()
        # print(file_path)
        split_name = file_path.split("/")
        project_name = split_name[4]
        self.ui.label_project.setText(project_name)
        
        
        sequence_name = split_name[6]
        self.ui.label_seq_name.setText(sequence_name)
        
        seq_number = split_name[7]
        self.ui.label_seq_number.setText(seq_number)
        
        version = split_name[-2]
        self.ui.label_version.setText(version)
        

        status = "pub"
        self.ui.label_status.setText(status)
        



    def file_path(self):
        """
        파일 경로를 생성하고, 버전 폴더를 포함하여 버전 폴더가 없으면 생성합니다.
        """
        # 현재 열려있는 누크 파일의 경로 가져오기
        file_path = nuke.scriptName()
        pub_change_path = file_path.replace("wip", "pub")
        images_change_path = pub_change_path.replace("scenes", "images")
        
        # 이미지 폴더 경로
        split_name = images_change_path.split("/")[:-1]
        join_path = "/".join(split_name)
        version = split_name[-1]
        #version = v002
        if not os.path.exists(join_path):
            os.makedirs(join_path)

        file_name_nknc = os.path.basename(pub_change_path)
        file_name = file_name_nknc.split('.')[0]
        wip_name_list = file_name.split('_')[:-1]
        pub_file_name = '_'.join(wip_name_list)

        pub_path = os.path.join(join_path, pub_file_name)

        return pub_path


    def shot_pub_func(self, node_name):
        if not node_name:
            return
        pub_path = self.file_path()
        nk_path = f"{pub_path}.nknc"

        file_path = nk_path.replace(".nknc", f"_{node_name}.####.exr")

        # 이미지 파일 경로 설정
        node = nuke.toNode(node_name)
        node["file"].setValue(file_path)

        
    def get_highest_write_numbered_exr(self):
        """
        지정된 버전 폴더에서 'Write' 뒤의 가장 높은 번호를 가진 .exr 파일을 가져옵니다.
        
        :return: 가장 높은 번호의 .exr 파일의 네 자리 숫자 또는 None
        """
        # 파일 패스
        file_path = nuke.scriptName()
        pub_change_path = file_path.replace("wip", "pub")
        images_change_path = pub_change_path.replace("scenes", "images")
        
        # 이미지 폴더 경로
        split_name = images_change_path.split("/")[:-1]
        join_path = "/".join(split_name)
        
        # 모든 파일 목록을 담을 빈 리스트를 초기화합니다.
        files = []

        # 주어진 경로의 모든 항목을 순회합니다.
        for f in os.listdir(join_path):
            # 각 항목이 파일인지 확인합니다.
            if os.path.isfile(os.path.join(join_path, f)):
                # 파일일 경우 리스트에 추가합니다.
                files.append(f)

        # exr 이미지 파일만을 담을 빈 리스트를 초기화합니다.
        image_files = []

        # 모든 파일을 순회합니다.
        for f in files:
            # 파일 확장자가 .exr인지 확인합니다.
            if f.lower().endswith('.exr'):
                # .exr 파일일 경우 리스트에 추가합니다.
                image_files.append(f)
        
        # 숫자 추출을 위한 정규식 패턴
        def extract_write_number(file_name):
            """
            파일명에서 'Write' 뒤에 오는 숫자를 추출합니다.
            숫자가 없을 경우 0을 반환합니다.
            """
            match = re.search(r'Write\d+\.(\d{4})', file_name)
            if match:
                return int(match.group(1))  # 네 자리 숫자를 반환
            return -1
        
        # exr 파일들을 번호를 기준으로 정렬하고 가장 높은 번호의 파일 선택
        image_files.sort(key=extract_write_number, reverse=True)
        
        if image_files:
            highest_write_number = extract_write_number(image_files[0])
            return highest_write_number
        return None

    def submit_render(self):
        """
        렌더를 실행하고 마지막 프레임이 렌더링 완료되었는지 확인합니다.
        """
        node, first_frame, last_frame = self.node_info()
        # 렌더 실행
        nuke.execute(node, first_frame, last_frame)
        
        # 마지막 프레임을 숫자로 변환
        last_frame_number = int(last_frame)
        
        # 가장 높은 번호의 EXR 파일 번호를 가져옵니다.
        highest_exr_number = self.get_highest_write_numbered_exr()

        # 확인 후 메시지 설정
        if highest_exr_number  == last_frame_number:
            fin_text = f"{self.ui.label_seq_number.text()}_comp_{self.ui.label_version.text()}_{self.ui.node_name_text.text()}.exr이 publish 되었습니다."
            self.ui.pub_finsh_text.setText(fin_text)
            status = "fin"
            self.ui.label_status.setText(status)


    def export_nuke_file(self):
        """
        누크파일을 pub경로로 복사.
        w00없애기
        """
        file_path = nuke.scriptName()
        pub_change_path = file_path.replace("wip", "pub")
        pub_folder = os.path.dirname(pub_change_path)

        file_name_nknc = os.path.basename(pub_change_path)
        file_name = file_name_nknc.split('.')[0]
        wip_name_list = file_name.split('_')[:-1]
        pub_file_name = '_'.join(wip_name_list)

        pub_path = os.path.join(pub_folder, pub_file_name)
        shutil.copy2(file_path, pub_path)
        
        # self.set_shotgrid_fin()
        
        
          


if __name__ == "__main__":
    app = QApplication()
    win = NukePublish()
    win.show()
    app.exec()
