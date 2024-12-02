# Shot Publish
import os
import sys
import re
import shutil
import subprocess
from shiboken2 import wrapInstance

try:
    from PySide6.QtWidgets import QApplication, QLabel, QTextEdit
    from PySide6.QtWidgets import QWidget, QPushButton, QMessageBox
    from PySide6.QtGui import *
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile
except:
    from PySide2.QtWidgets import QApplication, QLabel, QTextEdit
    from PySide2.QtWidgets import QWidget, QPushButton, QMessageBox
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtCore import QFile, Qt

from moomins.api_scripts.shotgun_api import ShotgunApi
from moomins.api_scripts.maya_api import MayaApi

sys.path.append("/home/rapa/git/pipeline/api_scripts")
sys.path.append("/usr/local/lib/python3.6/site-packages")


class ShotPublish(QWidget):

    def __init__(self):
        super().__init__()

        self.sg_api = ShotgunApi()
        self.maya_api = MayaApi()

        self.get_env_info()
        self.make_ui()
        self.sg_api.connect_sg()

        self.get_current_file_path()
        self.get_project()
        self.get_seq_name()
        self.get_seq_number()
        self.get_shot_task()
        self.get_shot_version()

        self.classify_task()

        self.ui.pushButton_shotpub.clicked.connect(self.get_root_nodes)
        
    def get_env_info(self):
        from dotenv import load_dotenv

        load_dotenv()  # read .env file

        self.user_id = os.getenv("USER_ID")
        self.root_path = os.getenv("ROOT")

        if self.user_id and self.root_path:
            self.image_path = self.root_path + "/sourceimages"

    def make_ui(self):
        """
        Create a UI
        """
        my_path = os.path.dirname(__file__)      
        ui_file_path = my_path +"/shot_publish.ui"

        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Shot Publish")
        ui_file.close()

    # Path to the shot file you are working on
    def get_current_file_path(self): 
        self.current_file_path = self.maya_api.get_current_maya_file_path()
        return self.current_file_path


    # Get information through the path
    def get_project(self):
        split_file_path = self.current_file_path.split("/")
        project_name = split_file_path[4] # 'Marvelous'
        self.ui.label_project.setText(project_name)
        return project_name
    
    def get_seq_name(self):
        split_file_path = self.current_file_path.split("/")
        seq_name = split_file_path[6] # FCG
        self.ui.label_seq_name.setText(seq_name)
        return seq_name

    def get_seq_number(self):
        split_file_path = self.current_file_path.split("/")
        seq_number = split_file_path[7] # FCG_0010
        self.ui.label_seq_number.setText(seq_number)
        return seq_number

    def get_shot_id(self):
        seq_num = self.get_seq_number()
        shot_id = self.sg_api.get_shot_id_by_seq_num(seq_num)
        return shot_id

    def get_shot_version(self):
        split_file_path = self.current_file_path.split("/")
        shot_version = split_file_path[-1] # FCG_0010_light_v001.ma
        p = re.compile('v\d{3}')
        p_data = p.search(shot_version)
        version = p_data.group() # v001
        self.ui.label_version.setText(version)
        return version

    def get_shot_task(self):
        split_file_path = self.current_file_path.split("/") #['', 'home', 'rapa', 'wip', 'Marvelous', 'seq', 'FCG', 'FCG_0010', 'lgt', 'wip', 'scenes', 'FCG_0010_light_v001.ma']
        user_task = split_file_path[8] #lgt
        return user_task



    def classify_task(self):
        """
        Separate the tasks of the current task,
        show the clean-up list of each, and run other functions when exporting
        """
        user_task = self.get_shot_task()
        print(f"The current working task is {user_task}.")

        # Matchmove : mb,      camera abc export + link    + sg status update + abc pub directory upload + sg undistortion size update
        # layout    : mb, abc, camera abc export + link    + sg status update + abc pub directory upload
        # Animation : mb, abc, camera abc export + link    + sg status update + abc pub directory upload
        # Lighting  : mb,             exr export + link    + sg status update + abc pub directory upload

        # sg update runs separately within the classify task function after the export-related function is executed

        if user_task == 'mm':
            mm_clean_up_list = """
MatchMove Team Cleanup List\n
- Organize and optimize camera tracking data
- 3D Point Cloud Cleanup
- Remove unnecessary tracking markers
- Camera movement smoothing
- Correction of lens distortion
- Check the alignment of 3D geometry and live-action images
- Converting and exporting camera data
- Organizing and documenting job files
            """
            self.ui.textEdit_shotcomment.setText(mm_clean_up_list)
            self.ui.pushButton_shotpub.clicked.connect(self.make_pub_path) # Create Directory
            self.ui.pushButton_shotpub.clicked.connect(self.export_mb)
            self.ui.pushButton_shotpub.clicked.connect(self.export_camera_alembic)

            self.ui.pushButton_shotpub.clicked.connect(self.link_camera) # Link camera to 'rendercam' directory
            self.ui.pushButton_shotpub.clicked.connect(self.open_folder)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_status_update)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_abc_pub_directory_update)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_undistort_size_update)

        elif user_task == 'ly':
            layout_clean_up_list = """
Layout Team Cleanup List\n
- Organizing and optimizing scene components
- Adjusting the consistency and proportion of object placement
- Review camera angle and composition
- Accuracy of spatial and depth expressions
- Harmonious arrangement between background and key elements
- Free space for animation and VFX work
- Remove unnecessary elements and geometry
- Organizing and documenting job files
            """ 
            self.ui.textEdit_shotcomment.setText(layout_clean_up_list)
            self.ui.pushButton_shotpub.clicked.connect(self.make_pub_path)
            self.ui.pushButton_shotpub.clicked.connect(self.export_mb)
            self.ui.pushButton_shotpub.clicked.connect(self.export_alembic)
            self.ui.pushButton_shotpub.clicked.connect(self.export_camera_alembic)

            self.ui.pushButton_shotpub.clicked.connect(self.link_camera)
            self.ui.pushButton_shotpub.clicked.connect(self.open_folder)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_status_update)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_abc_pub_directory_update)

        elif user_task == 'ani':
            ani_clean_up_list = """
Animation Team Cleanup List\n
- Smooth adjustment and timing between keyframes
- overshoot/undershoot correction and continuity of motion
- Fine adjustment of facial expressions and lip sync
- Resolving joint deformation problems and improving costume/hair simulation
- Weight and balance, add and improve secondary motion
- Synchronize animation and camera movement
- Correcting and detecting/resolving issues related to rigging
- Adjust animation for rendering optimization
            """
            self.ui.textEdit_shotcomment.setText(ani_clean_up_list)
            self.ui.pushButton_shotpub.clicked.connect(self.make_pub_path)
            self.ui.pushButton_shotpub.clicked.connect(self.export_mb)
            self.ui.pushButton_shotpub.clicked.connect(self.export_alembic)
            self.ui.pushButton_shotpub.clicked.connect(self.export_camera_alembic)

            self.ui.pushButton_shotpub.clicked.connect(self.link_camera)
            self.ui.pushButton_shotpub.clicked.connect(self.open_folder)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_status_update)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_abc_pub_directory_update)

        elif user_task == 'lgt':
            lgt_clean_up_list = """
Lighting Team Cleanup List\n
- Unnecessary light removal and light intensity/color fine-tuning
- Improve shadow quality and optimize environmental lighting (HDRI, GI)
- Remove unnecessary render layers and organize render path structures
- Shader and Texture Properties Fine-tuning, Quality Check
- Improve reflection, refraction, and ambient occlusion effects
- Ensure consistency between render elements and check alpha channel/mask
- Volumetric lighting, luminescence effect, lens flare purification
- Optimizing overall render settings and reducing render time
            """
            self.ui.textEdit_shotcomment.setText(lgt_clean_up_list)
            self.ui.pushButton_shotpub.setText("Publish")

            self.ui.pushButton_shotpub.clicked.connect(self.make_pub_path)
            self.ui.pushButton_shotpub.clicked.connect(self.export_mb)

            self.ui.pushButton_shotpub.clicked.connect(self.export_exr)
            self.ui.pushButton_shotpub.clicked.connect(self.copy_folders)

            self.ui.pushButton_shotpub.clicked.connect(self.open_folder)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_status_update)
            self.ui.pushButton_shotpub.clicked.connect(self.sg_pub_exr_directory_update)


        else: # user_task in ["mod", "lkd", "rig", "fx", "comp"]:
            QMessageBox.about(self, "Warning", "'Shot Publish' can only be run on Shot tasks using Maya.\nPlease check what you're working on")



    def make_pub_path(self): 
        """
        Create 'cache','scenes','images','sourceimages' directories.
        """
        if not self.current_file_path:
            QMessageBox.about(self, "Warning", "The file was not saved or opened.")

        project = self.get_project() # Marvelous
        seq_name = self.get_seq_name() # FCG
        seq_number = self.get_seq_number() # FCG_0010
        task = self.get_shot_task() # lgt
        version = self.get_shot_version() # v001

        self.open_pub_path = f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/{task}/pub/"

        folder_list = ['cache','scenes','images','sourceimages']
        created_folders = []
        for folder in folder_list:
            folder_path = os.path.join(self.open_pub_path, folder, version)

            if not os.path.exists(folder_path): # Create a folder when there is no path
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    created_folders.append(folder_path)

                except OSError as e: 
                    QMessageBox.about(self, "Warning", f"Error creating path : {str(e)}")
        print (f"Under {self.open_pub_path}\nPath 'cache', 'scenes', 'images', 'sourceimages' was successfully created.")

    def open_folder(self): # Open created Directory
        if hasattr(self, 'open_pub_path') and os.path.exists(self.open_pub_path):
            subprocess.call(["xdg-open", self.open_pub_path])
        else:
            QMessageBox.warning(self, "Warning", "Path that does not exist.")



    # Export
    def get_root_nodes(self):
        """
        Return top group name except camera to only_assemblies list
        """
        assemblies, cameras = self.maya_api.get_root_nodes()
        only_assemblies = list(set(assemblies) - set(cameras))
        return only_assemblies

    def export_mb(self):
        """
        Create a scenes/v001
        Export the entire scene including the camera
        """

        project = self.get_project() # Marvelous
        seq_name = self.get_seq_name() # FCG
        seq_number = self.get_seq_number() # FCG_0010
        task = self.get_shot_task() # lgt
        version = self.get_shot_version() # v001

        self.open_pub_path=f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/{task}/pub/"
        self.pub_path = os.path.join(self.open_pub_path, 'scenes', version)

        # mb file path
        mb_file_path = os.path.join(self.open_pub_path, 'scenes', version, f'{seq_number}_{task}_{version}.mb')

        # Validate
        if os.path.exists(mb_file_path):
            print (f"MB file {mb_file_path} already exists. Cancel export.")
            return

        try:
            self.maya_api.export_mb(mb_file_path)
            print(f"MB file exported successfully : {mb_file_path}")
        except Exception as e:
            print(f"Error exporting MB file : {str(e)}")
            error_msg_box = QMessageBox()
            error_msg_box.setIcon(QMessageBox.Critical)
            error_msg_box.setText(f"Error creating '{mb_file_path}' : {str(e)}")
            error_msg_box.setWindowTitle("File Export Failed")
            error_msg_box.setStandardButtons(QMessageBox.Ok)
            error_msg_box.exec()      

    def export_alembic(self): # Create cache/v001, Export abc excluding camera.

        project = self.get_project() #Marvelous
        seq_name = self.get_seq_name() #FCG
        seq_number = self.get_seq_number() #FCG_0010
        task = self.get_shot_task() #lgt
        version = self.get_shot_version() #v001

        self.open_pub_path=f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/{task}/pub/"
        self.pub_path = os.path.join(self.open_pub_path, 'cache', version)

        # Alembic file path
        abc_file_path = os.path.join(self.open_pub_path, 'cache', version, f'{seq_number}_{task}_{version}.abc')

        # Validate
        if os.path.exists(abc_file_path):
            print (f'ABC file {abc_file_path} is already exist. Cancel the Export.')
            return

        root_nodes = self.get_root_nodes()
        if not root_nodes:
            print ('No root node to export.')
            return

        # Execute ABC Export
        self.maya_api.export_abc(root_nodes, abc_file_path)

    def export_camera_alembic(self): # Export Camera ABC

        project = self.get_project() # Marvelous
        seq_name = self.get_seq_name() # FCG
        seq_number = self.get_seq_number() # FCG_0010
        task = self.get_shot_task() # lgt
        version = self.get_shot_version() # v001

        self.open_pub_path = f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/{task}/pub/"
        self.pub_path = os.path.join(self.open_pub_path,'cache',version)
        camera_file_path = os.path.join(self.open_pub_path,'cache',version,f'{seq_number}_{task}_cam.abc')

        self.maya_api.export_camera_abc(camera_file_path)

        return camera_file_path


    def extract_version(self, file_path):
        """
        Extract the version number from the file path.
        """
        match = re.search(r'v(\d{3})', file_path)  # Extract only numbers from 'vXXX' format
        if match:
            return match.group(1)    # Returns the entire string that matches the pattern.

    def set_image_size(self, width, height):
        """
        Change the image size in Maya render settings.

        :param width: Width of the rendering image
        :param height: Height of the rendering image
        """
        # Access the 'defaultResolution' node.
        default_resolution = 'defaultResolution'
        
        # Sets the image size.
        self.maya_api.set_render_resolution2(default_resolution, width, height)


    def export_exr(self):

        camera = self.get_camera_names() # Camera Settings for Rendering
        self.maya_api.arnold_render_setting(camera)

        # Gets the path to the currently open file.
        current_file_path =self.maya_api.get_current_file_directory()
        images_path = current_file_path.replace("scenes", "images")

        file_name = os.path.dirname(images_path)
        pub_path = file_name.replace("wip","pub")
        file_path = pub_path.split('/')[:-1]
        base_folder = '/'.join(file_path)

        # Undistortion Size
        image_size = self.get_image_plane_coverage()
        camera_names = self.get_camera_names()
        image_size_width = int(image_size[camera_names]["width"]) 
        image_size_height = int(image_size[camera_names]["height"]) 
        
        # Image Size Settings
        self.set_image_size(image_size_width, image_size_height)

        # Extract version number from file path.
        version = self.extract_version(current_file_path)
        ver = f"v{version}"

        # Create a version folder
        self.version_folder = os.path.join(base_folder, ver)
        #/home/rapa/pub/Moomins/seq/AFT/AFT_0010/lgt/pub/images/v002
        
        # Create a version folder if it does not exist.
        if not os.path.exists(self.version_folder):
            os.makedirs(self.version_folder)

        # Enable rendering of all render layers.
        self.maya_api.arnold_render_setting(camera, image_size_width, image_size_height, self.version_folder)

    def extract_version_folder_name(self,folder_name):
        """
        Extract the version number from the folder name.
        """
        match = re.search(r'v(\d{3})', folder_name)
        if match:
            return int(match.group(1))



    def get_version_folders(self, base_folder, file_name):
        """
        Extract the version number from the current file name, and create a folder path for the current version and the version with -1 applied from that version.
        """
        current_version = self.extract_version_folder_name(file_name)
        if current_version:
            current_version_folder = os.path.join(base_folder, f"v{current_version:03d}")
            previous_version_folder = os.path.join(base_folder, f"v{current_version - 1:03d}")
            
            return current_version_folder, previous_version_folder

    def get_file_paths(self):
        """
        Returns the path of the current and previous versions based on the path of the currently open Maya file.
        """
        # Get current file path.
        current_file = self.maya_api.get_current_maya_file_path()
        images_path = current_file.replace("scenes", "images")
        pub_path = images_path.replace("wip", "pub")

        file_name = os.path.basename(pub_path)  # Extract only the file name.
        file_path = os.path.dirname(pub_path)  # Gets the directory name of the file.
        
        base_folder = os.path.dirname(file_path)  # Split the path into slashes, excluding the last part.

        # Return current version (v002) and previous version path (v001).
        current_version_folder, previous_version_folder = self.get_version_folders(base_folder, file_name)
        return current_version_folder, previous_version_folder

    def copy_folders(self):

        # Get path from maya.
        dest_dir, src_dir = self.get_file_paths()

        # If the current version is v001, do not copy.
        current_version = self.extract_version(os.path.basename(dest_dir))
        if current_version == 1:
            return

        # Create a destination directory if it does not exist.
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Repeat for each item in the source directory.
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dest_path = os.path.join(dest_dir, item)

            if os.path.isdir(src_path):
                if not os.path.exists(dest_path):
                    # Copy folders if they don't exist.
                    shutil.copytree(src_path, dest_path)

    def link_camera(self):
        project = self.get_project()
        seq_name = self.get_seq_name()
        seq_number = self.get_seq_number()
        task = self.get_shot_task()

        seq_cam_folder_path = f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/rendercam"
        seq_cam_file_name = f"{seq_number}_cam.abc" # OPN_0010_cam.abc
        seq_cam_path = os.path.join(seq_cam_folder_path, seq_cam_file_name)

        print(f"{seq_cam_folder_path}") # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/rendercam
        print(f"{seq_cam_file_name}") # AFT_0010_cam.abc
        print(f"{seq_cam_path}") # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/rendercam/AFT_0010_cam.abc


        if not os.path.exists(seq_cam_folder_path): # Create a route if rendercam is not present.
            os.makedirs(seq_cam_folder_path)

        # Link to Rendercam
        task_list = ["mm","ly","ani"]
        for task in task_list:
            cam_path = f"/home/rapa/pub/{project}/seq/{seq_name}/{seq_number}/{task}/pub/cache"
            cam_name = f"{seq_number}_{task}_cam.abc" # OPN_0010_ani_cam.abc
            cam_full_path = os.path.join(cam_path, cam_name)

            if os.path.exists(cam_full_path):
                os.system(f"ln -s {cam_full_path} {seq_cam_path}") # ln -s "original path" "symbolic path"
                print(f"You have linked your {task} camera to rendercam!")

    def get_task_id(self):
        # Get seq_num_id
        seq_num = self.get_seq_number()
        step_name = self.get_shot_task() # lgt, ly...

        seq_num_id = self.sg_api.get_task_id(seq_num)
        self.sg_api.get_step_id(step_name, seq_num_id)


# Backend
    def sg_status_update(self):
        task_id = self.get_task_id()

        self.sg_api.update_status_to_pub(task_id)
        print(f"Update the status of {task_id} to pub in the Task entity.")

    def sg_abc_pub_directory_update(self):
        """
        Upload the path of the published abc file into the pub file directory field.
        """
        task_id = self.get_task_id()
        camera_path = self.export_camera_alembic()
        # /home/rapa/pub/Moomins/seq/AFT/AFT_0010/lgt/pub/cache/v001/AFT_0010_lgt_cam.abc

        self.sg_api.update_camera_path(task_id, camera_path)

    def sg_pub_exr_directory_update(self):
        """
        Upload the path of the published exr file into the pub file directory field.
        """
        task_id = self.get_task_id()
        exr_path  = self.version_folder()

        self.sg_api.update_camera_path(task_id, exr_path)



    def get_camera_names(self):
        """
        Get the name of the camera in Maya, excluding the Default camera
        """
        self.maya_api.get_camera_names()

    def sg_undistort_size_update(self):
        """
        Update the undistortion size from the camera in the match move step to sg.
        """
        undistortion_dict = self.get_image_plane_coverage()
        print(undistortion_dict) # {'camera1': {'width': 2040, 'height': 1220}}
        camera_names = self.get_camera_names() # camera1
        
        undistortion_width = str(undistortion_dict[camera_names]["width"]) # 2040 (str)
        undistortion_height = str(undistortion_dict[camera_names]["height"]) # 1220 (str)

        shot_id = self.get_shot_id_by_seq_num() # 1353

        # Upload each to the undistortion size field of the SG Shot entity.
        self.sg_api.update_undistortion_size(shot_id, undistortion_width, undistortion_height)

    def get_image_plane_coverage(self):
        """
        Search for the camera's image plan and get coverage X and Y.
        Group the imported camera name and coverage into a double dictionary
        ex : {'OPN_0010': {'width': 3000, 'height': 2145}}
        """
        # Get the name of the camera
        result = self.get_camera_names()
        split_name = result.split("_")
        seq_name = split_name[:2]
        camera_name = "_".join(seq_name)

        self.maya_api.get_coverage_values(result, camera_name)




if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = ShotPublish()
    win.show()
    app.exec()