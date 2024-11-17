from moomins.api_scripts.nuke_api import NukeApi
import os
import nuke

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

class NukePublish(QWidget):

    def __init__(self):
        super().__init__()
        self.nuke_api = NukeApi()
        self.dir_path = os.path.dirname(__file__)
        ui_file_name = "nuke_publish.ui"
        ui_file_path = f"{self.dir_path}/{ui_file_name}"
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()                                      
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.set_ui_center()
        # Button Events
        self.ui.pushButton_shotpub.clicked.connect(self.nuke_api.export_nuke_file)
        self.ui.pushButton_shotpub.clicked.connect(self.submit_render)
        self.setWindowTitle("Nuke Publish")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.node_info()
        self.shot_info()

    def set_ui_center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def node_info(self):
        nodes = self.nuke_api.get_selected_nodes()
        if len(nodes) is not 1:
            return nuke.message("Select one node")
        node = nodes[0]
        root_node = nuke.root()
        node_name = node["name"].value()
        first_frame = int(root_node["first_frame"].value())
        str_first_frame = str(first_frame)
        last_frame = int(root_node["last_frame"].value())
        str_last_frame = str(last_frame)
        color_space = node["colorspace"].value()

        self.ui.node_name_text.setText(node_name)
        self.ui.frist_frame_text.setText(str_first_frame)
        self.ui.last_frame_text.setText(str_last_frame)
        self.ui.color_space_text.setText(color_space)
        self.nuke_api.shot_pub_func(node_name)
        return node_name,first_frame,last_frame

    def shot_info(self):
        split_name = self.nuke_api.nuke_path.split("/")
        self.project_name = split_name[4]
        self.sequence_name = split_name[6]
        self.seq_number = split_name[7]
        self.version = split_name[-2]
        status = "pub"

        self.ui.label_project.setText(self.project_name)
        self.ui.label_seq_name.setText(self.sequence_name)
        self.ui.label_seq_number.setText(self.seq_number)
        self.ui.label_version.setText(self.version)
        self.ui.label_status.setText(status)

    def submit_render(self):
        """
        Render execute and pop up message box
        """
        node, first_frame, last_frame = self.node_info()
        nuke.execute(node, first_frame, last_frame)
        last_frame_number = int(last_frame)
        highest_exr_number = self.nuke_api.get_last_exr_num()
        if highest_exr_number  == last_frame_number:
            fin_text = f"{self.ui.label_seq_number.text()}_comp_{self.ui.label_version.text()}_{self.ui.node_name_text.text()}.exr이 publish 되었습니다."
            self.ui.pub_finsh_text.setText(fin_text)
            status = "fin"
            self.ui.label_status.setText(status)



          


if __name__ == "__main__":
    app = QApplication()
    win = NukePublish()
    win.show()
    app.exec()
