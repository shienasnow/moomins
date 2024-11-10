import nuke
import os
import subprocess
import re
import shutil

class NukeApi:
    def __init__(self):
        pass

    @staticmethod
    def check_read_node_connection(node_name):
        
        """
        checking connected node in "Read"type
        
        input type = str
        
        output = Bool
        
        Have Read Type return True

        Have not Read Type return False
        """
        
        current_node = nuke.toNode(node_name)
    
        if current_node is None:
            raise nuke.message(f"ReadNode is None")
        
        while current_node is not None:
            # Current node Class is Read
            if current_node.Class() == "Read":
                return True
            # Move Next node
            current_node = current_node.input(0)
        
        return False
    @property
    def nuke_path(self):
        return nuke.scriptName()
    @property
    def pub_path(self):
        _pub_path = self.nuke_path.replace("wib", "wib")
        return _pub_path

    def find_nuke_file(self,data = dict):
        '''
        if lighting task have precomp, return nk or nknc file
        '''

        lgt_pub_nuke_file_path,_ = data
        files = os.listdir(lgt_pub_nuke_file_path)
        nuke_file_path = ""
        for file in files:
            check_path = f"{lgt_pub_nuke_file_path}/{file}"
            if os.path.isfile(check_path):
                _,ext = os.path.splitext(file)
                ext = ext.replace(".","")
                if ext in ["nk","nknc"]:
                    nuke_file_path = check_path
                else:
                    nuke_file_path = lgt_pub_nuke_file_path
        return nuke_file_path





    def convert_jpg_to_exr(self, exr_path):
        """
        if select row, convert exr file to jpg and show thumbnail
        """
        files = sorted(os.listdir(exr_path))
        if not files:
            return
        first_file = files[0]
        exr_file_path = os.path.join(exr_path, first_file)
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

    def get_selected_nodes(self):
        selected_nodes = nuke.selectedNodes()
        if not selected_nodes:
            return nuke.message("Select Node!")
        return selected_nodes


    def get_node_class(self,node):
        return node.Class()

    def set_image_path(self, node_name, file_path):
        node = nuke.toNode(node_name)
        node["file"].setValue(file_path)

    def make_pub_file(self):
        """
        makedir path , if not version folder make version folder too
        """
        pub_change_path = self.pub_path
        images_path = pub_change_path.replace("scenes", "images")
        # 이미지 폴더 경로
        if not os.path.exists(images_path):
            os.makedirs(images_path)

        file_name_nknc = os.path.basename(pub_change_path)
        file_name = file_name_nknc.split('.')[0]
        wip_name_list = file_name.split('_')[:-1]
        pub_file_name = '_'.join(wip_name_list)
        pub_path = os.path.join(images_path, pub_file_name)

        return pub_path
    def shot_pub_func(self, node_name):
        if not node_name:
            return
        pub_path = self.make_pub_file()
        nk_path = f"{pub_path}.nknc"
        file_path = nk_path.replace(".nknc", f"_{node_name}.####.exr")
        self.set_image_path(node_name,file_path)

    def extract_write_number(file_name):
        """
        if file name in Write return four char num
        or return 0
        """
        match = re.search(r'Write\d+\.(\d{4})', file_name)
        if match:
            return int(match.group(1))  # 네 자리 숫자를 반환
        return -1

    def get_last_exr_num(self):
        """
        return lastest num in exr files four char or None
        """
        images_change_path = self.pub_path.replace("scenes", "images")
        split_name = images_change_path.split("/")[:-1]
        join_path = "/".join(split_name)
        files = []

        for f in os.listdir(join_path):
            if os.path.isfile(os.path.join(join_path, f)):
                files.append(f)
        image_files = []
        for f in files:
            if f.lower().endswith('.exr'):
                image_files.append(f)

        # exr 파일들을 번호를 기준으로 정렬하고 가장 높은 번호의 파일 선택
        image_files.sort(key=self.extract_write_number, reverse=True)

        if image_files:
            highest_write_number = self.extract_write_number(image_files[0])
            return highest_write_number
        return None

    def export_nuke_file(self):
        """
        if execute button, nuke file copy to pub server
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