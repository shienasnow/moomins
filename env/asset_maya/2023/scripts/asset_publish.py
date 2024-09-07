# Asset Publish
import os
import sys
import re
import subprocess
import json
import maya.cmds as cmds
import maya.mel as mel
from maya  import OpenMayaUI as omui
sys.path.append("/home/rapa/git/pipeline/api_scripts")
sys.path.append("/usr/local/lib/python3.6/site-packages")
from pprint import pprint
pprint(sys.path)

from shiboken2 import wrapInstance
from shotgun_api3 import shotgun

try:
    from PySide6.QtWidgets import QApplication, QLabel, QTextEdit
    from PySide6.QtWidgets import QWidget, QPushButton, QMessageBox
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile
except:
    from PySide2.QtWidgets import QApplication, QLabel, QTextEdit
    from PySide2.QtWidgets import QWidget, QPushButton, QMessageBox
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtCore import QFile, Qt

class AssetPublish(QWidget):
    def __init__(self):
        super().__init__()

        self.make_ui()
        self.connect_sg()

        self.get_current_file_path()
        self.get_project()
        self.get_user_task()
        self.get_version()
        self.get_asset_type()
        self.get_asset_name()
        self.classify_task()

        self.ui.pushButton_pub.clicked.connect(self.get_root_nodes)


# UI 생성
    def make_ui(self):
        my_path = os.path.dirname(__file__)
        ui_file_path = my_path +"/asset_publish.ui"

        ui_file = QFile(ui_file_path)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle("Asset Publish")
        ui_file.close()
        self.make_ui_center()

    def make_ui_center(self): # UI를 화면 중앙에 배치
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def connect_sg(self):
        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"

        self.sg = shotgun.Shotgun(URL,
                            SCRIPT_NAME,
                            API_KEY)

# 정보가져오기
    def get_current_file_path(self): # 현재 작업 파일의 경로 가져오기
        self.current_file_path = cmds.file(query=True, sceneName=True)
        # /home/rapa/wip/Moomins/asset/Prop/coffee cup/lkd/wip/scenes/v001/glass_v001_w001.mb

    def get_project(self):
        split_file_path = self.current_file_path.split("/")
        project = split_file_path[4]
        self.ui.label_project.setText(project)
        return project
    
    def get_asset_type(self):
        split_file_path = self.current_file_path.split("/")
        asset_type = split_file_path[6]
        self.ui.label_asset_type.setText(asset_type)
        return asset_type
    
    def get_asset_name(self):

        split_file_path = self.current_file_path.split("/")
        asset_name = split_file_path[7]
        self.ui.label_assetname.setText(asset_name)
        return asset_name
    
    def get_user_task(self):
        split_file_path = self.current_file_path.split("/")
        user_task = split_file_path[8] # mod, lkd, rig
        return user_task

    def get_version(self):

        split_file_path = self.current_file_path.split("/")
        file_name = split_file_path[11]
        p = re.compile('v\d{3}')
        p_data = p.search(file_name) #객체화
        version = p_data.group()
        self.ui.label_version.setText(version)
        # print (f'버전 : {version}')
        return version


# 현재 작업 task를 분리해서 각각 클린업리스트 보여주고, export할 때 다른 함수 실행
    def classify_task(self):
        user_task = self.get_user_task()
        print(f"현재 작업 Task는 {user_task}입니다.")
        # Modeling : mb                           export + sg status update + mb pub directory update
        # Lookdev  : mb, abc, shader.ma, json, texture export + sg status update + mb pub directory update
        # Rigging  : mb                           export + sg status update + mb pub directory update

        # """ """안의 내용은 주석이 아니라 변수로 받기 위한 내용입니다
        if user_task == "mod": # mb export
            mod_clean_up_list = """
Modeling팀 클린업리스트\n
- 불필요한 폴리곤 제거 및 N-gons/트라이앵글 정리
- 에지 플로우 개선 및 토폴로지 최적화
- 심(seam) 위치 조정 및 버텍스 웰딩 확인
- 중복 버텍스 제거 및 지오메트리 정리
- 일관된 네이밍 규칙 적용 및 논리적 오브젝트 그룹화
- 불필요한 그룹 및 레이어 정리
- 모델링 히스토리 삭제 및 프리즈 트랜스폼 적용
- 피벗 포인트 중심 정렬 및 최종 구조 확인
            """
            self.ui.textEdit_comment.setText(mod_clean_up_list)
            self.ui.pushButton_pub.clicked.connect(self.mod_event)

        elif user_task == "lkd": # mb, scenes/shader/shader.ma, sourceimages/texture, json export
            lkd_clean_up_list = """
LookDev팀 클린업리스트\n
- 텍스처 해상도 표준화 및 파일 포맷 최적화
- UV 레이아웃 확인 및 텍셀 밀도 균일화
- UV 아일랜드 간 블리딩 방지
- 머티리얼 네이밍 규칙 적용 및 불필요한 머티리얼 제거
- 셰이더 네트워크 정리 및 최적화
- 사용하지 않는 텍스처 파일 제거 및 네이밍 규칙 적용
- 텍스처 맵 종류별 구조화 (Diffuse, Normal, Specular 등)
- 텍스처 타일링, 노멀 맵 방향, 라이팅 환경에서의 테스트 수행
            """
            self.ui.textEdit_comment.setText(lkd_clean_up_list)
            self.ui.pushButton_pub.clicked.connect(self.lkd_event)

        elif user_task == "rig": # mb export
            rig_clean_up_list = """
Rigging팀 클린업리스트\n
- 조인트 계층 구조 확인 및 컨트롤러 최적화
- 제약 조건(Constraints) 검토 및 정리
- 일관된 네이밍 규칙 적용 및 논리적 그룹화
- 스키닝 품질 확인 및 웨이트 페인팅 조정
- 디포머 최적화 및 성능 개선
- 불필요한 히스토리 및 노드 제거
- 포즈별 사이클 애니메이션 테스트 수행
- 커스텀 속성 정리 및 리그 사용 설명서 작성
            """
            self.ui.textEdit_comment.setText(rig_clean_up_list)
            self.ui.pushButton_pub.clicked.connect(self.rig_event)

    def mod_event(self):
        self.export_mb()

        self.open_folder()
        self.sg_mb_pub_directory_update()
        self.sg_status_update()

    def lkd_event(self):
        self.export_mb()
        self.export_alembic()
        self.export_shader()
        self.make_symbolic_link()
        self.export_texture()

        self.open_folder()
        self.sg_abc_pub_directory_update()
        self.sg_status_update()

    def rig_event(self):
        self.export_mb()
        self.open_folder()

        self.sg_mb_pub_directory_update()
        self.sg_status_update()


# 경로 생성
    def make_publish_path(self): #폴더 생성
        if not self.current_file_path: # 현재 작업 파일 경로가 없을 경우
            print("파일이 저장되지 않았거나 열리지 않았습니다.")
            QMessageBox.about(self, "경고", "파일이 저장되지 않았거나 열리지 않았습니다.")

        project = self.get_project() # Moomins
        asset_type = self.get_asset_type() # prop
        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        version = self.get_version() # v001

        # Publish 경로에 (cache/scenes/images/sourceimages) 4개 폴더 생성되어야함
        self.open_pub_path=f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/"
        # /home/rapa/pub/Moomins/asset/prop/cup/lkd/pub/
        folder_list =['cache', 'scenes', 'images', 'sourceimages']

        created_folders = []

        for folder in folder_list:
            folder_path = os.path.join(self.open_pub_path, folder) 
            version_path = os.path.join(folder_path, version)
            
            if not os.path.exists(version_path):
                try:           
                    os.makedirs(version_path, exist_ok=True) # 폴더 생성
                    print (f"경로 '{version_path}가 성공적으로 생성되었습니다.")
                    created_folders.append(version_path)
                    success_msg_box = QMessageBox()
                    success_msg_box.setIcon(QMessageBox.Information)
                    success_msg_box.setText(f"경로 '{version_path}가 성공적으로 생성되었습니다.")
                    success_msg_box.setWindowTitle('경로 생성 성공!')
                    success_msg_box.setStandardButtons(QMessageBox.Ok)
                    success_msg_box.exec()

                except OSError as e: 
                    print (f"경로 '{version_path}'생성 중 오류 발생 : {str(e)}")
                    error_msg_box = QMessageBox()
                    error_msg_box.setIcon(QMessageBox.Critical)
                    error_msg_box.setText(f"경로 '{version_path}'생성 중 오류 발생 : {str(e)}")
                    error_msg_box.setWindowTitle("경로 생성 실패")
                    error_msg_box.setStandardButtons(QMessageBox.Ok)
                    error_msg_box.exec()     
       
        return self.open_pub_path
    
    def make_publish_lkd_path(self): # lkd에서만 scenes 안에 shader 폴더 생성
        if not self.current_file_path: # 현재 작업 파일 경로가 없을 경우
            print("파일이 저장되지 않았거나 열리지 않았습니다.")
            QMessageBox.about(self, "경고", "파일이 저장되지 않았거나 열리지 않았습니다.")

        project = self.get_project() # Moomins
        asset_type = self.get_asset_type() # prop
        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        version = self.get_version() # v001

        lkd_pub_path = f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/scenes/{version}/shader/"
        
        if not os.path.exists(lkd_pub_path):
            os.makedirs(lkd_pub_path, exist_ok=True) # 폴더 생성
            print (f"경로 '{lkd_pub_path}가 성공적으로 생성되었습니다.")
            try:           
                os.makedirs(lkd_pub_path, exist_ok=True) # 폴더 생성
                print (f"경로 '{lkd_pub_path}가 성공적으로 생성되었습니다.")
                success_msg_box = QMessageBox()
                success_msg_box.setIcon(QMessageBox.Information)
                success_msg_box.setText(f"경로 '{lkd_pub_path}가 성공적으로 생성되었습니다.")
                success_msg_box.setWindowTitle('경로 생성 성공!')
                success_msg_box.setStandardButtons(QMessageBox.Ok)
                success_msg_box.exec()

            except OSError as e: 
                print (f"경로 '{lkd_pub_path}'생성 중 오류 발생 : {str(e)}")
                error_msg_box = QMessageBox()
                error_msg_box.setIcon(QMessageBox.Critical)
                error_msg_box.setText(f"경로 '{lkd_pub_path}'생성 중 오류 발생 : {str(e)}")
                error_msg_box.setWindowTitle("경로 생성 실패")
                error_msg_box.setStandardButtons(QMessageBox.Ok)
                error_msg_box.exec()     
    
        return lkd_pub_path

# 생성된 폴더 오픈
    def open_folder(self): 
        subprocess.call(["xdg-open", self.open_pub_path])


# Get Nodes
    def get_root_nodes(self): # 최상위의 그룹 이름을 root_nodes 리스트로 리턴
        """
        씬의 최상위 노드를 찾아서 root_nodes 리스트에 넣는다
        """
        all_objects = cmds.ls(dag=True, long=True) # 씬의 모든 노드를 가져옴

        root_nodes = []
        # 모든 오브젝트를 반복하면서 최상위 노드를 찾습니다.
        for obj in all_objects:
            parent = cmds.listRelatives(obj, parent=True) # 현재 오브젝트의 부모를 가져옵니다.
            if parent is None: # 부모가 없으면 최상위 노드로 간주합니다.
                root_nodes.append(obj)
        return root_nodes

    def get_shader_nodes(self):
    # 모든 쉐이더 노드를 가져옵니다.
        all_shaders = cmds.ls(materials=True)
    
    # 제외할 기본 쉐이더 이름 리스트
        base_shaders = ["lambert1", "standardSurface1", "particleCloud1"]
        
        # 기본 쉐이더를 제외한 나머지 쉐이더만 필터링
        custom_shaders = []

        for shader in all_shaders:
            if shader not in base_shaders:
                custom_shaders.append(shader)

        return custom_shaders

    def collect_shader_assignments(self):
        """
        셰이더와 오브젝트들을 컬렉션하는 함수.
        """
        shader_dictionary = {}
        shading_groups = cmds.ls(type="shadingEngine")
        for shading_group in shading_groups:
            shader = cmds.ls(cmds.listConnections(shading_group + ".surfaceShader"), materials=True)    
            if not shader:
                continue
            objects = cmds.sets(shading_group, q=True)
            shader_name = shader[0]
            if objects:
                if shader_name not in shader_dictionary:
                    shader_dictionary[shader_name] = []
                shader_dictionary[shader_name].extend(objects)
        return shader_dictionary   


# Export
    def export_mb(self): # mod, rig

        self.make_publish_path() # 폴더 생성
        project = self.get_project() # Moomins
        asset_type = self.get_asset_type() # prop
        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        version = self.get_version() # v001

        self.open_pub_path=f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/"
        mb_file_path = os.path.join(self.open_pub_path,'scenes', version, f'{asset_name}_{task}_{version}.mb')
        folder_path = os.path.dirname(mb_file_path)
        print(f'MB 파일 경로 : {folder_path}')

        try:
            cmds.file(rename=mb_file_path)
            cmds.file(mb_file_path, exportAll=True, type="mayaBinary", force=True)
            print(f"MB Export 성공 : {mb_file_path}")

        except Exception as e:
            QMessageBox.about(self, "경고", f"{mb_file_path} 생성 중 export 중 오류 발생 : {str(e)}")
            print(f"MB 파일 내보내기 중 오류 발생: {str(e)}")

        if os.path.exists(mb_file_path):
            print(f"MB 파일 {mb_file_path}가 이미 존재하기 때문에 Export를 취소합니다.")

        return mb_file_path

    def export_alembic(self): # lkd
        """
        선택된 오브젝트를 Alembic 파일로 내보냅니다.
        수정사항 : 어셋의 경우는 프레임레인지가 안나오게 만들기
        
        file_path: 내보낼 Alembic 파일의 전체 경로
        frame_range: 내보낼 프레임 범위 (기본값은 1에서 24까지)
        data_format: Alembic 파일의 데이터 형식 (기본값은 'ogawa')
        root_node: 내보낼 루트 노드 (기본값은 None, 지정하지 않으면 전체 씬을 내보냄)
        """
        print("export alembic 함수 실행")
        # 마야에 열려있는 파일경로 가져오기
        if not self.current_file_path:
            print ("파일이 저장되지 않았거나 열리지 않았습니다.")
            return
        
        # 경로 분석
        self.make_publish_path() #폴더 생성
        project = self.get_project() # Moomins
        asset_type = self.get_asset_type() # prop
        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        version = self.get_version() # v001
        
        # PUB 경로
        self.open_pub_path=f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/"
        abc_file_path = os.path.join(self.open_pub_path,'cache', version, f'{asset_name}_{task}_{version}.abc')
        folder_path = os.path.dirname(abc_file_path)
        print(f'ABC 파일 경로 : {folder_path}')
                
        # 파일 존재 여부 확인
        if os.path.exists(abc_file_path):
            print (f'Alembic파일 {abc_file_path}가 이미 존재합니다. 내보내기를 취소합니다.')
            return

        # 노드 찾아서
        root_nodes = self.get_root_nodes()
        if not root_nodes:
            print ('내보낼 루트 노드가 없습니다.')
            return

        # Alembic 파일 내보내기
        abc_command = f"-frameRange 1 1 -uvWrite -worldSpace -writeVisibility -dataFormat ogawa"

        for node in root_nodes:
            abc_command += f" -root{node}"
        abc_command += f' -file {abc_file_path}'

        # Alembic 내보내기
        try:
            cmds.AbcExport(j=abc_command)
            print (f'Alembic 파일이 성공적으로 Export 되었습니다.: {abc_file_path}')
        except Exception as e:
            print (f"Alembic Export 오류 발생 : {str(e)}")

        return abc_file_path

    def export_texture(self): # sourceimages / texture.tiff
        """
        지정된 쉐이더에 연결된 모든 파일 텍스처를 새로운 폴더로 복사하고,
        경로를 업데이트합니다.

        :param shader_name: 쉐이더 노드의 이름
        :param new_folder: 파일을 복사할 대상 폴더의 경로
        """
        print("export texture 함수 실행")
        #파일경로 찾아내기
        cache_path = self.current_file_path.replace("/scenes/", "/sourceimages/")
        file_path = cache_path.replace("/wip/", "/pub/")

        #디렉토리 이름
        directory_path = os.path.dirname(file_path)

        #쉐이더 노드 검색해서 넣어놓음
        shaders = self.get_shader_nodes()
        for shader in shaders:
            shader_name = shader

            if not cmds.objExists(shader_name):
                print(f"쉐이더 '{shader_name}'을(를) 찾을 수 없습니다.")
                return

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            connections = cmds.listConnections(shader_name, source=True, destination=False) # 연결된 택스쳐파일 가져오기

            for connected_node in connections:
                node_type = cmds.nodeType(connected_node)# 노드 타입이 파일인지 확인

                if node_type == 'file':
                    #fileTextureName : tiff파일이나 다른 파일의 확장자까지 받음
                    current_path = cmds.getAttr(f"{connected_node}.fileTextureName") 

                    if not current_path or not os.path.exists(current_path):
                        print(f"'{connected_node}'에 연결된 유효한 파일이 없습니다.")
                        continue

                    file_name = os.path.basename(current_path)
                    new_path = os.path.join(directory_path, file_name)

                    try:
                        shutil.copy2(current_path, new_path)
                        print(f"파일을 복사했습니다: {current_path} -> {new_path}")
                        cmds.setAttr(f"{connected_node}.fileTextureName", new_path, type="string")
                        print(f"'{connected_node}'의 파일 경로를 업데이트했습니다.")

                    except IOError as e:
                        print(f"파일 복사 중 오류 발생: {e}")

                elif node_type in ['aiImage', 'aiNormalMap', 'bump2d', 'place2dTexture']: #노말맵 범프맵인지 확인하고 파일이름 리스트 만들기
                    sub_connections = cmds.listConnections(connected_node, source=True, destination=False)

                    if sub_connections:
                        for sub_node in sub_connections:
                            if cmds.nodeType(sub_node) == 'file':
                                current_path = cmds.getAttr(f"{sub_node}.fileTextureName") #파일경로 가져오기

                                if not current_path or not os.path.exists(current_path): #파일이 있는지 확인
                                    print(f"'{sub_node}'에 연결된 유효한 파일이 없습니다.")
                                    continue

                                file_name = os.path.basename(current_path)
                                new_path = os.path.join(directory_path, file_name)

                                try:
                                    shutil.copy2(current_path, new_path)
                                    print(f"파일을 복사했습니다: {current_path} -> {new_path}")
                                    cmds.setAttr(f"{sub_node}.fileTextureName", new_path, type="string")
                                    print(f"'{sub_node}'의 파일 경로를 업데이트했습니다.")
                                except IOError as e:
                                    print(f"파일 복사 중 오류 발생: {e}")

            print("Texture Export 작업이 완료되었습니다.")

    def export_shader(self): # shader.ma, shader.json
        """
        maya에서 오브젝트에 어싸인된 셰이더들을 ma 파일로 익스포트하고,
        그 정보들을 json 파일로 익스포트 하는 함수이다.
        """
        print("export shader 함수 실행")
        shader_folder = self.make_publish_lkd_path()
        # lkd_pub_path = f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/scenes/{version}/shader/"

        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        version = self.get_version() # v001

        # 최종 파일 경로 설정
        file_path_export = os.path.join(shader_folder, f"{asset_name}_{task}_{version}_shader.ma") # coffecup_lkd_v001_shader.ma
        json_path_export = os.path.join(shader_folder, f"{asset_name}_{task}_{version}_shader.json")
        file_path_export = os.path.abspath(file_path_export)

        # 모든 커스텀 쉐이더 가져오기
        shaders = self.get_shader_nodes()
        if not shaders:
            cmds.warning("내보낼 커스텀 쉐이더가 없습니다.")
            return False

        # 현재 선택된 오브젝트 저장
        original_selection = cmds.ls(selection=True)

        try:
            # 쉐이더와 관련된 노드만 선택합니다.
            cmds.select(shaders, noExpand=True)
            
            # 쉐이더 네트워크를 포함한 파일 내보내기
            cmds.file(file_path_export, 
                    force=True, 
                    options="v=0;", 
                    type="mayaAscii", 
                    exportSelected=True)
            
        except Exception as e:
            cmds.warning(f"쉐이더 내보내기 중 오류 발생: {str(e)}")
            return False

        finally:
            cmds.select(original_selection, replace=True)

        shader_dictionary = self.collect_shader_assignments()
        with open(json_path_export, 'w') as f:
            json.dump(shader_dictionary, f)

    def make_symbolic_link(self):
        """
        가장 마지막 버전의 폴더를 링크 파일에 덮어씌우는 코드
        """
        print("symbolic link 생성하는 함수 실행")
        # 프로젝트 및 파일 정보
        self.make_publish_lkd_path() # shader 폴더 생성
        project = self.get_project() # Moomins
        asset_type = self.get_asset_type() # prop
        asset_name = self.get_asset_name() # coffee cup
        task = self.get_user_task() # lkd
        link_path = f"/home/rapa/pub/{project}/asset/{asset_type}/{asset_name}/{task}/pub/scenes/"

        # 버전 폴더 목록 가져오기
        version_path = os.listdir(link_path)
        # isdir하고 나서 sort하기로 했었는데 이게 머지???
        version_path.sort()
        print (f'쉐이더 폴더 경로 :{version_path}') # ['shader.ma', 'v001', 'v002', 'v003', 'v004']

        # 버전 폴더만 필터링 ################################################### 이 부분 문제 있을 것 같음
        version_folders = []
        for version in version_path: # ver_path의 각 요소를 순회
            # 요소가 'v'로 시작하는지 확인
            if version.startswith("v"):
                # 조건을 만족하면 리스트에 추가
                version_folders.append(version)

        if version_folders: # 버전 리스트가 하나 이상일 때
            last_version = version_folders[-1] # 가장 최신 버전 선택

            # 최신 버전의 셰이더 파일 이름 설정
            shader_name = f"{asset_name}_{task}_{last_version}_shader.ma"
            json_name = f"{asset_name}_{task}_{last_version}_shader.json"
            shader_ver = f"{last_version}/shader"

            # 최신 버전 셰이더 및 JSON 파일 경로 설정
            shader_path = os.path.join(link_path, shader_ver, shader_name)
            json_path = os.path.join(link_path, shader_ver, json_name)

        else:
            # 버전 폴더가 없는 경우
            shader_path = os.path.join(link_path, "shader.ma")
            json_path = os.path.join(link_path, "shader.json")

        # 셰이더 파일 및 JSON 파일 생성 (존재하지 않을 경우)
        if not os.path.exists(shader_path):
            os.system(f"touch {shader_path}")

        if not os.path.exists(json_path):
            os.system(f"touch {json_path}")

        # 심볼릭 링크 파일 이름과 경로 설정
        shader_link_name = f"{asset_name}_{task}_shader_link.ma"
        shader_link_full_path = os.path.join(link_path, shader_link_name)

        json_link_name = f"{asset_name}_{task}_json_link.json"
        json_link_full_path = os.path.join(link_path, json_link_name)

        # 기존의 심볼릭 링크가 있으면 삭제
        if os.path.islink(shader_link_full_path):
            os.remove(shader_link_full_path)

        if os.path.islink(json_link_full_path):
            os.remove(json_link_full_path)

        # 새로 심볼릭 링크 생성 (ln -s "파트 경로" "공용 경로")
        os.system(f"ln -s {os.path.abspath(shader_path)} {os.path.abspath(shader_link_full_path)}")
        os.system(f"ln -s {os.path.abspath(json_path)} {os.path.abspath(json_link_full_path)}")



### Bachend (효은)
    def get_task_id(self): # 완료
        # asset_id 구하기
        asset_name = self.get_asset_name()
        print(f"********************* asset name 출력 테스트 {asset_name}")
        asset_filter = [["code", "is", asset_name]]
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field)
        asset_id = asset_info["id"]
        print(f"**************asset id 출력 테스트 {asset_id}")

        # step_id 찾기
        step_name = self.get_user_task() # lgt, ly 등
        step_info = self.sg.find_one("Step",[["code", "is", step_name]], ["id"])
        step_id = step_info["id"]
        print(f"step id 찾기 : {step_id}")

        # asset_id, step_id 조건에 맞는 task_id 찾기
        task_filter = [
                ["entity", "is", {"type": "Asset", "id": asset_id}],
                ["step", "is", {"type": "Step", "id": step_id}]
                       ]
        task_field = ["id"]
        task_info = self.sg.find_one("Task", filters=task_filter, fields=task_field)
        task_id = task_info["id"]
        print(f"************ task id 찾기 출력 테스트 : {task_id}")

        return task_id

    def sg_status_update(self): # 완료
        task_id = self.get_task_id()
        self.sg.update("Task", task_id, {"sg_status_list" : "fin"})

        print(f"task id : {task_id}의 status를 'fin'으로 업데이트합니다.")
        # self.ui.label_status.setText("fin")
        image_path = "/home/rapa/git/pipeline/sourceimages/fin.png"

        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(30, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.label_status.setPixmap(scaled_pixmap)
        self.ui.label_status.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.ui.label_status.setFixedSize(80, 20)

    def sg_mb_pub_directory_update(self): # mod, rig 완료
        task_id = self.get_task_id()
        mb_pub_directory = self.export_mb()
        print(mb_pub_directory)
        self.sg.update("Task", task_id, {"sg_description" : mb_pub_directory})

        print(f"task id : {task_id}의 pub directory를 업데이트 합니다.\n업데이트 될 경로 확인 : {mb_pub_directory}")

    def sg_abc_pub_directory_update(self): # lkd
        task_id = self.get_task_id()
        abc_pub_directory = self.export_alembic()
        print(abc_pub_directory)
        self.sg.update("Task", task_id, {"sg_description" : abc_pub_directory})

        print(f"task id : {task_id}의 pub directory를 업데이트 합니다.\n업데이트 될 경로 확인 : {abc_pub_directory}")


if __name__ == "__main__":
    if not QApplication.instance():
        app = QApplication(sys.argv)
    win = AssetPublish()
    win.show()
    app.exec()