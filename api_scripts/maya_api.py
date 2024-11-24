import os
import json
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui


class MayaAPI:
    def __init__(self):
        pass

    def import_reference_asset(asset_path):
        reference_node = import_reference(asset_path)
        if not reference_node:
            return

        return reference_node
        
        # print (f"The asset was successfully imported as a reference {reference_node}")
        # assign_shader_to_asset(reference_node)

    def assign_shader_to_asset(reference_node, shader_json_file, shader_ma_file):
        """
        애셋에 셰이더를 붙이는 함수입니다.
        셰이더는 ma파일과 셰이더 어싸인 정보가 담긴 json 파일을 이용합니다.
        """
        print ("*******************")
        print ("assign_shader_to_asset")
        print (reference_node, shader_json_file, shader_ma_file)
        
        node_name = cmds.referenceQuery(reference_node, nodes=True, dagPath=True)[0]
        if ":" in node_name:
            asset_name = node_name.split(":")[-1]
        else:
            asset_name = node_name

        # asset_name 으로 shader 파일 경로를 찾는 스크립트 필요
        # shader_json_file = f"/show/4th_academy/assets/char/{asset_name}/lookdev/wip/maya/data/shader.json"
        # shader_ma_file = f"/show/4th_academy/assets/char/{asset_name}/lookdev/wip/maya/data/shader.ma"

        if not os.path.exists(shader_json_file):
            print ("publish된 셰이더 정보가 없습니다.")
            return

        if not os.path.exists(shader_ma_file):
            print ("publish된 셰이더 데이터 없습니다.")
            return

        name_space = os.path.basename(shader_ma_file).split(".")[0]
        cmds.file(shader_ma_file, i=True, namespace=name_space)

        # json파일 로드.
        with open(shader_json_file, "r") as f:
            shader_data = json.load(f)

        # shader dictionary 정보대로 임포트한 셰이더에 오브젝트를 붙인다.
        for shader, objects in shader_data.items():
            name_space_shader = f"{name_space}:{shader}"
            for object in objects:
                for ns_obj in cmds.ls(node_name, dag=True, shapes=True):
                    if ns_obj.endswith(object):
                        cmds.select(ns_obj, add=True)
            cmds.hyperShade(assign=name_space_shader)
            cmds.select(clear=True)

    def import_reference(asset_path):
        """
        애셋의 경로를 입력받으면 레퍼런스로 임포트하는 메서드입니다.
        마야 특징을 따라 네임 스페이스는 파일의 이름으로 생성합니다.
        """
        file_name = os.path.basename(asset_path)
        name_space = file_name.split(".")[0]

        try:
            reference_node = cmds.file(asset_path, reference=True, namespace=name_space, returnNewNodes=True)[0]
            return reference_node
        except:
            return None

    def get_reference_assets():
        """
        레퍼런스 노드들의 애셋 이름과 파일 경로를 딕셔너리로 리턴합니다.
        """
        reference_dict = {}
        ref_assets = cmds.ls(type="reference")
        for ref in ref_assets:
            if ref == 'sharedReferenceNode':
                continue
            tmp = {}
            node_name = cmds.referenceQuery(ref, nodes=True, dagPath=True)[0]
            reference_file_path = cmds.referenceQuery(ref, filename=True)
            if ":" in node_name:
                asset_name = node_name.split(":")[-1]
            else:
                asset_name = node_name
            tmp["asset_name"] = asset_name
            tmp["reference_file_path"] = reference_file_path
            tmp["version"] = reference_file_path.split("/")[-2] # v002
            reference_dict[ref] = tmp

        return reference_dict

    def update_reference_file_path(ref_node, new_path, pushButton_update):
        """
        레퍼런스 노드와 새로운 경로를 주면 레퍼런스 노드의 파일 경로를 업데이트 합니다.
        """
        if not os.path.exists(new_path):
            print ("경로에 파일이 존재하지 않습니다. 레퍼런스 노드를 업데이트 할 수 없습니다.")
            return None
        cmds.file(new_path, loadReference=ref_node)
        pushButton_update.setEnabled(False)
        return ref_node

    def assgin_shader():
        shader_ma_file = "/show/4th_academy/assets/char/teapot/lookdev/wip/maya/data/shader.ma"
        shader_file = "/show/4th_academy/assets/char/teapot/lookdev/wip/maya/data/shader.json"

        # 마야 네임스페이스를 설정합니다.
        name_space = os.path.basename(shader_ma_file).split(".")[0]
        cmds.file(shader_ma_file, i=True, namespace=name_space)

        # json파일 로드.
        with open(shader_file, "r") as f:
            shader_data = json.load(f)

        # shader dictionary 정보대로 임포트한 셰이더에 오브젝트를 붙인다.
        for shader, objects in shader_data.items():
            name_space_shader = f"{name_space}:{shader}"
            cmds.select(clear=True)
            for object in objects:
                cmds.select(object, add=True)
            cmds.hyperShade(assign=name_space_shader)



    def set_render_resolution(undistortion_height, undistortion_width):

        cmds.setAttr("defaultResolution.width", int(undistortion_width))
        cmds.setAttr("defaultResolution.height", int(undistortion_height))

    def get_frame_range(self, shot_id): # 샷그리드에서 shot_id 기준으로 Frame Range를 가져오기
        filter = [["id", "is", shot_id]]
        field = ["sg_cut_in", "sg_cut_out"]
        frame_info = self.sg.find_one("Shot", filters=filter, fields=field)
        start_frame = frame_info["sg_cut_in"] # 1
        end_frame = frame_info["sg_cut_out"] # 25

        return start_frame, end_frame

    def set_frame_range(start_frame, end_frame):
        # 타임 슬라이더의 시작 및 종료 프레임 설정
        cmds.playbackOptions(min=start_frame, max=end_frame)

        # 현재 프레임 범위도 동일하게 설정 (프레임 범위 안에서 현재 시작 및 종료 프레임 설정)
        cmds.playbackOptions(ast=start_frame, aet=end_frame)


    def get_current_file_directory():
        current_file_path = cmds.file(q=True, sn=True)
        print(f"현재 마야 파일 경로 : {current_file_path}")
        # /home/rapa/wip/Moomins/seq/AFT/AFT_0010/ly/wip/scene/v001/AFT_0010_v001_w001.mb
        return current_file_path

    def import_shader(shader_ma_path, shader_json_path):

        # maya name space 설정
        name_space = os.path.basename(shader_ma_path).split(".")[0]
        cmds.file(shader_ma_path, i=True, namespace=name_space)

        # json 파일 로드
        with open(shader_json_path, "r") as f:
            shader_dict = json.load(f)

        # shadere dictionary 정보대로 shader에 오브젝트 붙이기
        for shader, objects in shader_dict.items():
            name_space_shader = f"{name_space}:{shader}"
            cmds.select(clear=True)
            for oject in objects:
                cmds.select(object, add=True)
            cmds.hyperShade(assign=name_space_shader)





    # Shot Publish
    def get_current_maya_file_path():
        file_path = cmds.file(query=True, sceneName=True)
        return file_path


