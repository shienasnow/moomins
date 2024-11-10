import sys
sys.path.append("/usr/local/lib/python3.6/site-packages")
from shotgun_api3 import shotgun
import os
from pprint import pprint


class ShotgunApi:
    def __init__(self):
        self.connect_sg()

    def connect_sg(self): # 샷그리드를 연결하는 메쏘드
        
        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"

        self.sg = shotgun.Shotgun(URL,
                                SCRIPT_NAME,
                                API_KEY)
        
        return URL

    def get_datas_by_user_id(self, user_id): # 로그인된 유저의 데이터를 가져오는 함수  

        filters = [["id", "is", user_id]]
        fields = ["name","projects"]   
        user_datas = self.sg.find_one("HumanUser", filters=filters, fields=fields)

        if isinstance(user_datas, dict):
            return user_datas
        # {'type': 'HumanUser', 'id': 105, 'name': '다미 김', 'projects': [{'id': 188, 'name': 'Moomins', 'type': 'Project'}]}

    def get_task_data(self, user_id): # Shot 작업자에게 할당된 데이터 정보 가져오기 
        """
        shot 작업자의 user data 가져오기
        """
        # user_id = 121
        user_data = self.get_datas_by_id(user_id)  
        shot_user_id = user_data["id"]
        user_name = user_data["name"]

        filters = [["task_assignees", "is", {'id': shot_user_id, 'name': user_name, 'type': 'HumanUser'}]]
        fields = ["projects", "entity", "task_assignees", "step", "sg_status_list", "start_date", "due_date", "project"]
        datas_list = self.sg.find("Task", filters=filters, fields=fields) # 리스트에 싸여진 딕셔너리들 데이터
        
        # print (datas_list)
        return datas_list

        # {'due_date': '2024-09-29',
        # 'entity': {'id': 1349, 'name': 'TRS_0010', 'type': 'Shot'},
        # 'id': 7022,
        # 'project': {'id': 188, 'name': 'Moomins', 'type': 'Project'},
        # 'sg_status_list': 'wtg',
        # 'start_date': '2024-09-27',
        # 'step': {'id': 7, 'name': 'lgt', 'type': 'Step'},
        # 'task_assignees': [{'id': 94, 'name': '주석 박', 'type': 'HumanUser'}],
        # 'type': 'Task'},

        # {'due_date': '2024-10-02',
        # 'entity': {'id': 1344, 'name': 'BRK_0020', 'type': 'Shot'},
        # 'id': 7023,
        # 'project': {'id': 188, 'name': 'Moomins', 'type': 'Project'},
        # 'sg_status_list': 'wtg',
        # 'start_date': '2024-09-30',
        # 'step': {'id': 8, 'name': 'cmp', 'type': 'Step'},
        # 'task_assignees': [{'id': 94, 'name': '주석 박', 'type': 'HumanUser'}],
        # 'type': 'Task'}
        
    def get_assets_data(self,asset_id): # 할당된 데이터중 asset_id를 받아 assets의 데이터를 찾는 함수
        filters = [["id", "is", asset_id]]
        fields = ["code","sg_asset_type"] 
        if asset_id:
            assets_datas = self.sg.find_one("Asset",filters=filters,fields=fields)
        if isinstance(assets_datas, dict):
            return assets_datas
        
    def get_assigned_Shot_num_lgt_task(self,seq_num): # comp팀의 작업을 위해 lgt팀의 할당된 작업들을 구하는 함수

        filter = [["code","is",seq_num]]
        content_field = ["content"]
        frame_field = ["sg_cut_in","sg_cut_out"]
        lgt_content = self.sg.find("Shot", filters=filter, fields=content_field)
        seq_frame_list = self.sg.find("Shot", filters=filter, fields=frame_field)

        # lgt_shot = [{'type': 'Shot', 'id': 1343}]
        filter = [["entity","is",lgt_content],["step","is",{'id': 7, 'name': 'lgt', 'type': 'Step'}]]
        field = ["task_assignees","updated_at","sg_status_list"]
        datas_list = self.sg.find("Task", filters=filter, fields=field)

        return seq_frame_list,datas_list
        
    def sg_status_update(self,asset_name,task):  ################# status update
        print("Shotgrid Status Update")

        # project id 구하기
        project_name = "Moomins"
        project = self.sg.find_one("Project", [["name", "is", project_name]], ["id", "name"])

        # asset id 구하기
        asset_filter = [["code", "is", asset_name], ["project", "is", project]]
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}
        asset_id = asset_info["id"]

        # task id 구하기 (mod, lkd, rig)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])              ####### 이것두 가져와야댐
        step_id = step["id"]

        print(asset_info) # {'type': 'Asset', 'id': 2008}
        print(asset_name) # mat
        print(asset_id) # 2008
        print(step_id) # 16

        filter =[
            ["entity", "is", {"type": "Asset", "id": asset_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                    ]
        field = ["id"]
        task_ids = self.sg.find("Task", filters=filter, fields=field)                   # task, asset id 조건에 맞는 status 필드 찾기

        for task in task_ids:
            task_id = task["id"]
            self.sg.update("Task", task_id, {"sg_status_list": "wip"})
            print(f"Task ID {task_id}의 status를 wip으로 바꿉니다")                      # Task ID 7033의 status를 wip으로 바꿉니다



# login
    def get_dept(self, shotgrid_id): # 사용자 이름, Department 정보 가져오기
        # print(shotgrid_id) # 작업자의 id
        
        filter_dept = [["id", "is", shotgrid_id]]
        field_dept = ["name", "department"]
        datas = self.sg.find_one("HumanUser", filters=filter_dept, fields=field_dept) # "~"에서 filters 조건에 맞는 fields를 찾는다
        # print(datas) # {'type': 'HumanUser', 'id': 121, 'name': 'hyoeun seol', 'department': {'id': 41, 'name': 'Shot', 'type': 'Department'}}

        return datas
    
    def get_shotgrid_email(self, input_id, input_pw):

        URL = self.connect_sg()

        a = shotgun.Shotgun(URL, input_id, input_pw)
        user = a.authenticate_human_user(input_id, input_pw)

        return user
    
    def find_camera_path_to_seq_num(self,seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["id"]
        shot_entity = self.sg.find_one("Shot", filters=shot_filter, fields=shot_fields)
        shot_id = shot_entity['id']
        filter = [["id", "is", shot_id]]
        field = ["description"]
        camera_info = self.sg.find_one("Shot", filters=filter, fields=field)
        shot_camera_directory = camera_info["description"]

        return shot_camera_directory
    
    def get_project_res_to_project_name(self,project_name):
        shot_filter = [["name", "is", project_name]]
        shot_fields = ["sg_resolutin_width","sg_resolution_height"]
        project_res_list = self.sg.find("Project", filters=shot_filter, fields=shot_fields)
        project_res = project_res_list[0]
        
        
        return project_res
    
    def get_shot_undistortion_size_to_seq_num(self,seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["sg_undistortion_height","sg_undistortion_width"]
        undistortion_size_list = self.sg.find("Shot", filters=shot_filter, fields=shot_fields)
        undistortion_size = undistortion_size_list[0]
        
        return undistortion_size
        
    def get_shot_frame_range_to_seq_num(self,seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["sg_cut_in","sg_cut_out"]
        frame_range_list = self.sg.find("Shot", filters=shot_filter, fields=shot_fields)
        frame_range = frame_range_list[0]
        
        return frame_range

    def get_shot_due_date_to_seq_num(self, user_id, seq_num):
        user_data = self.get_datas_by_id(user_id)  

        # shot_user_id = 94
        shot_user_id = user_data["id"]
        user_name = user_data["name"]

        filters = [["task_assignees", "is", {'id': shot_user_id, 'name': user_name, 'type': 'HumanUser'}]]
        fields = ["due_date","entity"]
        user_entity_list = self.sg.find("Task", filters=filters, fields=fields)
        user_entity = user_entity_list[0]
        date_list = []
        for key,value in user_entity.items():
            if key == "due_date":
                date_list.append(value)
            if key == "entity":
                for keys,values in value.items():
                    if keys == "name":
                        if values == seq_num:
                            due_date = date_list[-1]
                            return due_date
        
        # [{'due_date': '2024-09-29',
        # 'entity': {'id': 1349, 'name': 'TRS_0010', 'type': 'Shot'}},
        # {'due_date': '2024-09-31',
        # 'entity': {'id': 1349, 'name': 'AFT_0010', 'type': 'Shot'}}]

    def get_shot_id(self, seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["id"]
        shot_entity = self.sg.find_one("Shot", filters=shot_filter, fields=shot_fields)
        shot_id = shot_entity['id']
        
        return shot_id

    def get_assets_of_seq(self, seq_num): # 시퀀스에 해당되는 에셋들을 구합니다.
        filter = [["code", "is", seq_num]]
        field = ["assets"]
        assets_of_seq = self.sg.find_one("Shot", filters=filter, fields=field)

        return assets_of_seq

    def get_asset_info(self, asset_id): # asset id로 에셋 정보를 구합니다.
        filter = [["id", "is", asset_id]] # [1546, 1479, 1547]
        field = ["code", "sg_status_list", "tasks"]
        asset_info = self.sg.find("Asset", filters=filter, fields=field)

        return asset_info

    def get_link_camera_directory(self, shot_id): # shot id 기준으로 rendercam 경로 리턴
        filter = [["id", "is", shot_id]]
        field = ["description"]
        camera_info = self.sg.find_one("Shot", filters=filter, fields=field)
        shot_camera_directory = camera_info["description"]

        return shot_camera_directory

    def get_undistortion_size(self, shot_id): # 매치무브 팀에서 샷그리드에 pub한 undistortion size를 받아와서 리턴
        # shot_id를 기준으로 undistortion size를 가져온다.
        filter = [["id", "is", shot_id]]
        field =["sg_undistortion_height", "sg_undistortion_width"]
        undistortion_info = self.sg.find_one("Shot", filters=filter, fields=field)
        undistortion_height = undistortion_info["sg_undistortion_height"] # 1220
        undistortion_width = undistortion_info["sg_undistortion_width"] # 2040

        return undistortion_height, undistortion_width

    def get_frame_range(self, shot_id): # 샷그리드에서 Frame Range를 받아와서 리턴
        # shot_id를 기준으로 frame range를 받아온다.
        filter = [["id", "is", shot_id]]
        field = ["sg_cut_in", "sg_cut_out"]
        frame_info = self.sg.find_one("Shot", filters=filter, fields=field)
        start_frame = frame_info["sg_cut_in"] # 1
        end_frame = frame_info["sg_cut_out"] # 25

        return start_frame, end_frame
    
    def get_tasks_info(self, task_id): 
        tasks_info = self.sg.find("Task", [["id", "is", task_id]], ["task_assignees", "step", "sg_status_list"])

        return tasks_info
    
    def get_path_info(self, task_id):
        # task entity에서 sg_description으로 에셋이 publish된 경로와 pub 날짜 가져오기
        filter = [["id", "is", task_id]]
        field = ["sg_description"]
        path_info = self.sg.find_one("Task", filters=filter, fields=field)

        field2 = ["updated_at"]
        date_info = self.sg.find_one("Task", filters=filter, fields=field2)

        return path_info, date_info
    
    def get_lgt_assgined_assets(self, shot_id):
         
        filter_ly = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 277}]] # shot_id + ly의 step id
        filter_ani = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 106}]] # shot_id + ani의 step id
        filter_fx = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 276}]] # shot_id + fx의 step id
        field = ["id", "sg_description"] # pub abc 파일 경로, task id

        ly_asset_info = self.sg.find("Task", filters=filter_ly, fields=field)
        ani_asset_info = self.sg.find("Task", filters=filter_ani, fields=field)
        fx_asset_info = self.sg.find("Task", filters=filter_fx, fields=field)
        
        ly_asset_info = ly_asset_info[0]
        ani_asset_info = ani_asset_info[0]
        fx_asset_info = fx_asset_info[0]

        return ly_asset_info, ani_asset_info, fx_asset_info

    def get_asset_datas(self, asset_id):
        # 어셋 id로 작업자, status, pub날짜, 에셋 이름, step 찾기
        filter = [["id", "is", asset_id]]
        field = ["task_assignees", "sg_status_list", "updated_at", "content", "step"]
        asset_datas = self.sg.find("Task", filters=filter, fields=field)
        return asset_datas




# Backend
    # Asset Loader - re, wtg에서 new scene하면 status wip으로 변경
    def sg_asset_task_status_update(self,asset_name,task):
        print("wtg, re 상태에서 new scene을 했을 때, status를 wip으로 업데이트합니다.")

        # asset id 구하기
        asset_filter = [["code", "is", asset_name]] # 현재 작업 중인 asset name ex.jane
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}
        asset_id = asset_info["id"]
        print(f"asset_id : {asset_id}")

        # task id 구하기 (mod, lkd, rig)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"]
        print(f"step_id : {step_id}")

        filter =[
            ["entity", "is", {"type": "Asset", "id": asset_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                    ]
        field = ["id"]
        task_ids = self.sg.find("Task", filters=filter, fields=field)
        print(f"task_ids : {task_ids}")

        for task in task_ids:
            task_id = task["id"]
            self.sg.update("Task", task_id, {"sg_status_list": "wip"})
            print(f"Task ID {task_id}의 status를 wip으로 바꿉니다")


    # Shot Loader - re, wtg에서 new scene하면 status wip으로 변경
    def sg_shot_task_status_update(self, seq_num, task): # 완료
        print("wtg, re 상태에서 new scene을 했을 때, status를 wip으로 업데이트합니다.")
        print("***************************** shot wip status update")

        # shot id 구하기
        seq_filter = [["code", "is", seq_num]] # 현재 작업 중인 시퀀스 넘버 ex.OPN_0010
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        shot_id = seq_info["id"]
        print(f"shot_id 찾기 : {shot_id}")

        # task id 구하기 (mm, ly, ani, fx, lgt, prc, cmp)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"]
        print(f"step_id 찾기 : {step_id}")

        filter =[
            ["entity", "is", {"type": "Shot", "id": shot_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                    ]
        field = ["id"]
        task_ids = self.sg.find("Task", filters=filter, fields=field)
        print(f"task_ids = {task_ids}")

        for task in task_ids:
            task_id = task["id"]
            self.sg.update("Task", task_id, {"sg_status_list": "wip"})
            print(f"Task ID {task_id}의 status를 wip으로 바꿉니다")



    # Asset, Shot Status 자동화 메서드
    # maya와 nuke의 모든 코드에서 실행
    def sg_asset_status_update_automation1(self, asset_name):
        print("********** Asset Status 자동화 백엔드")

        """
        asset_id에 해당하는 mod, lkd, rig task의 status를 조회
        모두 fin일 때 Asset Status가 fin이 되게
        """
        # asset id 구하기
        asset_filter = [["code", "is", asset_name]] # 현재 작업 중인 asset name
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field)
        asset_id = asset_info["id"]

        filter = [["entity", "is", {"type" : "Asset", "id" : asset_id}]]
        field = ["step", "sg_status_list"]
        tasks_info = self.sg.find("Task", filters=filter, fields=field)

        status_list = []
        for task in tasks_info:
            pipeline_step = task["step"]["name"]
            status = task["sg_status_list"]
            print(f"{pipeline_step}")
            print(f"pipeline_step : {pipeline_step}\nstatus : {status}")

            status_list.append(status)
        
        all_fin = True
        for status in status_list:
            if not status == "fin": # 하나라도 fin인 상태가 아니면 False
                all_fin = False
                break

        if all_fin == True:
            self.sg.update("Asset", asset_id, {"sg_status_list": "wip"}) # 모두 fin인 경우 Asset Status를 fin으로 바꾼다.


        """
        asset_id에 해당하는 task 중 하나라도 re이면
        Asset Status가 re이 되게
        """
        all_re = False
        for status in status_list:
            if status == "re":
                all_re = True
                break
        if all_re == True:
            self.sg.update("Asset", asset_id, {"sg_status_list": "re"})

    def sg_shot_status_update_automation(self, seq_num):
        """
        shot_id에 해당하는 mm, ly, ani, fx, lgt, cmp의 task의 status를 조회
        모두 fin일 때 shot status가 fin이 되게
        """
        print("********** Shot Status 자동화 백엔드")


        # shot id 구하기
        seq_filter = [["code", "is", seq_num]] # 현재 작업 중인 시퀀스 넘버 ex.OPN_0010
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        shot_id = seq_info["id"]
        print(f"shot_id 찾기 : {shot_id}")


        # shot id에 해당하는 task들의 status 다 구하기
        filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
        fields = ["sg_status_list", "content"]  # content는 Task의 이름입니다.
        tasks = self.sg.find("Task", filters=filters, fields=fields)

        for task in tasks:
            task_name = task["content"]
            task_status = task["sg_status_list"]
            print(f"Task: {task_name}, Status: {task_status}")

        status_list = []
        for task in tasks:
            pipeline_step = task["step"]["name"]
            status = task["sg_status_list"]
            print(f"{pipeline_step}")
            print(f"pipeline_step : {pipeline_step}\nstatus : {status}")

            status_list.append(status)
        
        all_fin = True
        for status in status_list:
            if not status == "fin": # 하나라도 fin인 상태가 아니면 False
                all_fin = False
                break

        if all_fin == True:
            self.sg.update("Asset", shot_id, {"sg_status_list": "wip"}) # 모두 fin인 경우 Asset Status를 fin으로 바꾼다.

        """
        shot_id에 해당하는 task 중 하나라도 re이면
        Shot Status가 wip이 되게
        """
        all_re = False
        for status in status_list:
            if status == "re":
                all_re = True
                break
        if all_re == True:
            self.sg.update("Asset", shot_id, {"sg_status_list": "re"})
