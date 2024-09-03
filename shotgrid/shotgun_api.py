
from shotgun_api3 import shotgun
import os

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
    
    def get_datas_by_id(self, user_id): # 로그인된 유저의 데이터를 가져오는 함수  


        filters = [["id", "is", user_id]]
        fields = ["name","projects"]
        # entity # 조건에맞는 사람의 # 이 필드들을 가져와라.    
        user_datas = self.sg.find_one("HumanUser", filters=filters, fields=fields)

        if isinstance(user_datas, dict):
            
            return user_datas
        # {'type': 'HumanUser', 'id': 105, 'name': '다미 김', 'projects': [{'id': 188, 'name': 'Moomins', 'type': 'Project'}]}

    def get_assign_project_id(self, user_id): # login된 사람이 포함된 project를 가져오는 함수
        
        user_datas = self.get_datas_by_id(user_id)
        project_name_list = []           # 이름 는 리스트
        project_id_list = []        # 프로젝트 id를 담는 리스트
        if not user_datas:
            return
        for key,values in user_datas.items():
            if key == "projects":
                for value in values:    
                    project_name_list.append(value["name"])     # ["Marvelous","Moomins"]
                    project_id_list.append(value["id"])    # [122,188]
                    
        return project_name_list,project_id_list
    
        # {'Moomins': [{'asset_data': {'code': 'car',
        #                              'id': 1479,
        #                              'sg_asset_type': 'prop',
        #                              'type': 'Asset'},
        #               'due_date': '2024-08-11',
        #               'entity': {'id': 1479, 'name': 'car', 'type': 'Asset'},
        #               'id': 6195,
        #               'sg_status_list': 'wip',
        #               'start_date': '2024-08-10',
        #               'step': {'id': 16, 'name': 'lkd', 'type': 'Step'},
        #               'type': 'Task'},

    def get_tasks_from_project(self, user_id): # 프로젝트별로 테스크의 모든 데이터를 가져오는 함수 # 개어렵다 진짜
        project_task = {}
        project_name_list,project_id_list = self.get_assign_project_id(user_id)
        
        for project,project_id in zip(project_name_list,project_id_list):          # zip 이라는 모듈은 이게 짝짝쿵을 맞춰준다.
            filters = [["project", "is", {"type": "Project", "id": project_id}]]        # 프로젝트들 [122,188]
            fields = ["content", "entity","task_assignees"]                             # 필드들을 가져와라.
            tasks_data = self.sg.find("Task",filters=filters , fields=fields)
            project_task[project] = tasks_data
            
        return project_task
    
            # {'content': 'FIN_0020_ly',
            #           'entity': {'id': 1351, 'name': 'FIN_0010', 'type': 'Shot'},
            #           'id': 6307,
            #           'task_assignees': [{'id': 121,
            #                               'name': 'hyoeun seol',
            #                               'type': 'HumanUser'}],
            #           'type': 'Task'},
            #          {'content': 'FIN_0010_fx',
            #           'entity': {'id': 1351, 'name': 'FIN_0010', 'type': 'Shot'},
            #           'id': 6310,
            #           'task_assignees': [{'id': 187,
            #                               'name': 'seonil hong',
            #                               'type': 'HumanUser'}],
            #           'type': 'Task'},
                    

    def get_assgined_user_project_by_task(self, user_id):        # 프로젝트 별 assign된 task를 가져오는 함수
        
        project_task = self.get_tasks_from_project(user_id)    # 프로젝트 별 데이터가 가져온다.
        # user_data = self.get_datas_by_id()               # user 데이터만 가져오기때문에 비교하려고 가져왔음
        # user_id = user_data["id"]                       # [105]
        assign_user_project_by_task = {}                # assign 된 데이터를 저장하기 위한 딕셔너리 # 쓰다보니 여러곳에서 사용해서 전역변수로 사용했다. # 나중에 datas라고 선언했음
            # mar,moo # tasks
        for project,tasks in project_task.items():
            assign_user_project_by_task[project] = []
            
            for task in tasks:
                if not task.get("task_assignees"):
                    continue
                
                assign_task = task["task_assignees"][0]  # 리스트를 풀기위해 [0]을 붙혔다. # [다미 김] => "다미 김"
                assign_task_id = assign_task["id"]       # assign된 모든 테스크의 id를 가져온다. # ex) task_assignees': [{'id': 105, 'name': '다미김', 'type': 'HumanUser'}
                
                if user_id == assign_task_id:            # user에 할당된 테스크와 id가 같을때 
                    filters = [['id', "is", task["id"]]]
                    fields = ["step", "entity","start_date","due_date","sg_status_list"]
                    fields = fields
                    user_tasks_data = self.sg.find("Task",filters=filters , fields=fields)
                    for task_data in user_tasks_data:
                        asset_id = task_data["entity"]["id"]
                        asset_data = self.get_assets_data(asset_id)
                        task_data["asset_data"] = asset_data
                    if project not in assign_user_project_by_task:              # 프로젝트가 저장된 딕셔너리 안에 없으면 새로운 리스트를 만든다.
                        assign_user_project_by_task[project] = []
                    assign_user_project_by_task[project].append(task_data)

        return assign_user_project_by_task
    
            # {'Moomins': [{'asset_data': {'code': 'car',
            #                          'id': 1479,
            #                          'sg_asset_type': 'prop',
            #                          'type': 'Asset'},
            #           'due_date': '2024-08-11',
            #           'entity': {'id': 1479, 'name': 'car', 'type': 'Asset'},
            #           'id': 6195,
            #           'sg_status_list': 'wip',
            #           'start_date': '2024-08-10',
            #           'step': {'id': 16, 'name': 'lkd', 'type': 'Step'},
            #           'type': 'Task'},
    
    
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

        # asset id 구하기
        asset_filter = [["code", "is", asset_name]] # 가운데 위젯에서 내가 선택한 asset name
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}
        selected_asset_id = asset_info["id"]

        # task id 구하기 (mod, lkd, rig)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])              ####### 이것두 가져와야댐
        step_id = step["id"]                                                            # 14 (mod의 step id)

        filter =[
            ["entity", "is", {"type": "Asset", "id": selected_asset_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                    ] 
        field = ["id"]
        task_ids = self.sg.find("Task", filters=filter, fields=field)                   # task, asset id 조건에 맞는 status 필드 찾기

        for task in task_ids:
            task_id = task["id"]
            self.sg.update("Task", task_id, {"sg_status_list": "wip"})
            print(f"Task ID {task_id}의 status를 wip으로 바꿉니다")                      # Task ID 7033의 status를 wip으로 바꿉니다


    # shot loader
    def get_shot_task_data(self, user_id): # Shot 작업자에게 할당된 데이터 정보 가져오기 
        """
        shot 작업자의 user data 가져오기
        """

        user_data = self.get_datas_by_id(user_id)  

        shot_user_id = user_data["id"]
        user_name = user_data["name"]

        filters = [["task_assignees", "is", {'id': shot_user_id, 'name': user_name, 'type': 'HumanUser'}]]
        fields = ["projects", "entity", "task_assignees", "step", "sg_status_list", "start_date", "due_date", "project"]
        datas_list = self.sg.find("Task", filters=filters, fields=fields) # 리스트에 싸여진 딕셔너리들 데이터

        return datas_list

        # [{'due_date': '2024-09-29',
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
        # 'type': 'Task'}]


    # log-in
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
