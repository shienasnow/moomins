import sys
from shotgun_api3 import shotgun
import os
from pprint import pprint


class ShotgunApi:
    def __init__(self):
        self.connect_sg()

    def connect_sg(self):

        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"

        self.sg = shotgun.Shotgun(URL,
                                SCRIPT_NAME,
                                API_KEY)
        return URL



    def get_project_by_id(self, user_id):
        """
        Function to import data from logged-in users
        """
        filters = [["id", "is", user_id]]
        fields = ["projects"] 
        project = self.sg.find_one("HumanUser", filters=filters, fields=fields)
        #[{'id': 188, 'name': 'Moomins', 'type': 'Project'}]

        return project["projects"]

    def get_name_by_id(self,user_id):
        filters = [["id", "is", user_id]]
        fields = ["name"]
        name = self.sg.find_one("HumanUser", filters=filters, fields=fields)

        return name["name"]

    def get_task_data(self, user_id):
        """
        Get tasks assigned to artists with user_id.
        """
        user_name = self.get_name_by_id(user_id)

        filters = [["task_assignees", "is", {'id': user_id, 'name': user_name, 'type': 'HumanUser'}]]
        fields = ["projects", "entity", "task_assignees", "step", "sg_status_list", "start_date", "due_date", "project"]
        datas_list = self.sg.find("Task", filters=filters, fields=fields)

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

        return datas_list

    def get_assets_data(self, asset_id):
        """
        Function to find assets data with asset_id
        """
        filters = [["id", "is", asset_id]]
        fields = ["code","sg_asset_type"] 
        if asset_id:
            assets_datas = self.sg.find_one("Asset",filters=filters,fields=fields)
        return assets_datas

    def get_assigned_Shot_num_lgt_task(self, seq_num):
        """
        A function that finds the assigned tasks of the lgt step for the task of the comp step
        """
        filter = [["code", "is", seq_num]]
        content_field = ["content"]
        frame_field = ["sg_cut_in", "sg_cut_out"]
        lgt_content = self.sg.find("Shot", filters=filter, fields=content_field)
        seq_frame_list = self.sg.find("Shot", filters=filter, fields=frame_field)

        # lgt_shot = [{'type': 'Shot', 'id': 1343}]
        filter = [["entity","is",lgt_content],["step","is",{'id': 7, 'name': 'lgt', 'type': 'Step'}]]
        field = ["task_assignees","updated_at","sg_status_list"]
        datas_list = self.sg.find("Task", filters=filter, fields=field)

        return seq_frame_list,datas_list

    def get_project_id_by_name(self, project_name):
        project = self.sg.find_one("Project", [["name", "is", project_name]], ["id"])
        project_id = project[id]
        return project_id

    def sg_status_update(self, asset_name, task):
        # Get project id
        project_id = self.get_project_id_by_name()

        # Get asset id
        asset_filter = [["code", "is", asset_name], ["project", "is", project_id]]
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}
        asset_id = asset_info["id"]

        # Get task id
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"]

        # find status filed that meets task, asset id condition.
        filter =[
            ["entity", "is", {"type": "Asset", "id": asset_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                    ]
        field = ["id"]
        task_ids = self.sg.find("Task", filters=filter, fields=field)

        for task in task_ids:
            task_id = task["id"]
            self.sg.update("Task", task_id, {"sg_status_list": "wip"})
            print(f"Change status of task id '{task_id}' to 'wip'")


# login
    def get_dept_by_id(self, user_id):
        """
        Get user name, Department information with user_id.
        """
        filter_dept = [["id", "is", user_id]]
        field_dept = ["name", "department"]
        datas = self.sg.find_one("HumanUser", filters=filter_dept, fields=field_dept)
        # {'type': 'HumanUser', 'id': 121, 'name': 'hyoeun seol', 'department': {'id': 41, 'name': 'Shot', 'type': 'Department'}}

        return datas["department"]
    
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

        return camera_info["description"]
    
    def get_project_res_to_project_name(self,project_name):
        shot_filter = [["name", "is", project_name]]
        shot_fields = ["sg_resolutin_width","sg_resolution_height"]
        project_res_list = self.sg.find("Project", filters=shot_filter, fields=shot_fields)
        
        
        return project_res_list[0]
    
    def get_shot_undistortion_size_to_seq_num(self,seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["sg_undistortion_height","sg_undistortion_width"]
        undistortion_size_list = self.sg.find("Shot", filters=shot_filter, fields=shot_fields)

        return undistortion_size_list[0]
        
    def get_shot_frame_range_to_seq_num(self,seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["sg_cut_in","sg_cut_out"]
        frame_range_list = self.sg.find("Shot", filters=shot_filter, fields=shot_fields)

        return frame_range_list[0]
    
    def get_shot_due_date_to_seq_num(self, user_id, seq_num):
        user_data = self.get_datas_by_id(user_id)  

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

    def get_shot_id_by_seq_num(self, seq_num):
        shot_filter = [["code", "is", seq_num]]
        shot_fields = ["id"]
        shot_entity = self.sg.find_one("Shot", filters=shot_filter, fields=shot_fields)
        shot_id = shot_entity['id']

        return shot_id

    def get_assets_by_seq_num(self, seq_num):
        filter = [["code", "is", seq_num]]
        field = ["assets"]
        assets_by_seq = self.sg.find_one("Shot", filters=filter, fields=field)

        return assets_by_seq

    def get_asset_info_by_asset_id(self, asset_id): ##### 비슷한 함수
        """
        Find asset information with asset id.
        """
        filter = [["id", "is", asset_id]] # [1546, 1479, 1547]
        field = ["code", "sg_status_list", "tasks"]
        asset_info = self.sg.find("Asset", filters=filter, fields=field)

        return asset_info

    def get_asset_datas_by_asset_id(self, asset_id): ##### 비슷한 함수
        """
        Find artist, status, pub date, asset name, step with asset id.
        """
        filter = [["id", "is", asset_id]]
        field = ["task_assignees", "sg_status_list", "updated_at", "content", "step"]
        asset_datas = self.sg.find("Task", filters=filter, fields=field)
        return asset_datas


    def get_link_camera_directory(self, shot_id):
        """
        Return rendercam path based on shot id.
        """
        filter = [["id", "is", shot_id]]
        field = ["description"]
        camera_info = self.sg.find_one("Shot", filters=filter, fields=field)

        return camera_info["description"]

    def get_undistortion_size(self, shot_id):
        """
        Find the undistortion size relative to the shot id, published in the shot grid in mm step.
        """
        filter = [["id", "is", shot_id]]
        field =["sg_undistortion_height", "sg_undistortion_width"]
        undistortion_info = self.sg.find_one("Shot", filters=filter, fields=field)
        undistortion_height = undistortion_info["sg_undistortion_height"] # 1220
        undistortion_width = undistortion_info["sg_undistortion_width"] # 2040

        return undistortion_height, undistortion_width

    def get_frame_range_by_shot_id(self, shot_id):
        """
        Get the frame range in the shot grid based on shot_id.
        """
        filter = [["id", "is", shot_id]]
        field = ["sg_cut_in", "sg_cut_out"]
        frame_info = self.sg.find_one("Shot", filters=filter, fields=field)
        start_frame = frame_info["sg_cut_in"] # 1
        end_frame = frame_info["sg_cut_out"] # 25

        return start_frame, end_frame
    
    def get_tasks_info_by_task_id(self, task_id):
        tasks_info = self.sg.find("Task", [["id", "is", task_id]], ["task_assignees", "step", "sg_status_list"])
        return tasks_info

    def get_path_info_by_task_id(self, task_id):
        """
        Get the path and pub date that the asset is published in task entity.
        """
        filter = [["id", "is", task_id]]
        field = ["sg_description"]
        path_info = self.sg.find_one("Task", filters=filter, fields=field)

        field2 = ["updated_at"]
        date_info = self.sg.find_one("Task", filters=filter, fields=field2)

        return path_info, date_info
    
    def get_lgt_assgined_assets_by_shot_id(self, shot_id):
         
        filter_ly = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 277}]] # shot_id + ly's step id
        filter_ani = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 106}]] # shot_id + ani's step id
        filter_fx = [["entity", "is", {"type" : "Shot", "id" : shot_id}], ["step", "is", {"type": "Step", "id": 276}]] # shot_id + fx's step id
        field = ["id", "sg_description"] # publised abc file directory, task id

        ly_asset_info = self.sg.find("Task", filters=filter_ly, fields=field)
        ani_asset_info = self.sg.find("Task", filters=filter_ani, fields=field)
        fx_asset_info = self.sg.find("Task", filters=filter_fx, fields=field)
        
        ly_asset_info = ly_asset_info[0]
        ani_asset_info = ani_asset_info[0]
        fx_asset_info = fx_asset_info[0]

        return ly_asset_info, ani_asset_info, fx_asset_info



    # Backend
    def sg_asset_task_status_update(self,asset_name,task):
        """
        Update status to 'wip' when new scene is made in 'wtg', 're' state.
        """
        # Get asset id
        asset_filter = [["code", "is", asset_name]]
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}
        asset_id = asset_info["id"]
        print(f"asset_id : {asset_id}")

        # Get task id (mod, lkd, rig)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"]

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
            print(f"Change status of task id '{task_id}' to 'wip'")

    def sg_shot_task_status_update(self, seq_num, task):
        """
        Update status to 'wip' when new scene is made in 'wtg', 're' state.
        """
        # Get shot id
        seq_filter = [["code", "is", seq_num]]
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        shot_id = seq_info["id"]

        # Get task id (mm, ly, ani, fx, lgt, prc, cmp)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"]
        print(f"step_id : {step_id}")

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
            print(f"Change status of task id '{task_id}' to 'wip'")


    # Status Automation Method (Run on all code in maya and nuke)
    def sg_asset_status_update_automation1(self, asset_name):
        """
        Check the status of mod, lkd, rig task corresponding to asset_id
        When all of them are 'fin', the asset status is 'fin'
        """
        # Get asset id
        asset_filter = [["code", "is", asset_name]]
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
            if not status == "fin": # False if even one of the statuses is not 'fin'
                all_fin = False
                break

        # Change the asset status to fin only if it is all 'fin'.
        if all_fin == True:
            self.sg.update("Asset", asset_id, {"sg_status_list": "fin"})


        """
        If any of the tasks corresponding to asset_id is 're'
        Asset Status is 're'.
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
        Check the status of tasks in mm, ly, ani, fx, lgt, cmp step corresponding to shot_id
        When it's all fin, the shot status is fin
        """
        # Get shot id
        seq_filter = [["code", "is", seq_num]]
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        shot_id = seq_info["id"]
        print(f"shot_id 찾기 : {shot_id}")


        # Get all the status of tasks corresponding to shot id.
        filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
        fields = ["sg_status_list", "content"]
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
            if not status == "fin": # False if even one of the statuses is not 'fin'
                all_fin = False
                break

        # Change the asset status to fin only if it is all 'fin'.
        if all_fin == True:
            self.sg.update("Asset", shot_id, {"sg_status_list": "fin"}) 

        """
        If any of the tasks corresponding to shot_id is 're'
        Shot Status is 're'.
        """
        all_re = False
        for status in status_list:
            if status == "re":
                all_re = True
                break
        if all_re == True:
            self.sg.update("Asset", shot_id, {"sg_status_list": "re"})







# Shot Publish
    def get_task_id(self, seq_num):
        seq_filter = [["code", "is", seq_num]]
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        seq_num_id = seq_info["id"]
        print(f"seq_num_id : {seq_num_id}")

    def get_step_id(self, step_name, seq_num_id):
        step_info = self.sg.find_one("Step",[["code", "is", step_name]], ["id"])
        step_id = step_info["id"]
        print(f"step id : {step_id}")

        # find task id that meets seq_num_id, step_id condition.
        task_filter = [
            ["entity", "is", {"type": "Shot", "id": seq_num_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
        ]
        task_field = ["id"]
        task_info = self.sg.find_one("Task", filters=task_filter, fields=task_field)
        task_id = task_info["id"]
        print(f"task id : {task_id}")

        return task_id


    def update_status_to_pub(self, task_id):
        self.sg.update("Task", task_id, {"sg_status_list" : "pub"})

    def update_camera_path(self, task_id, camera_path):
        self.sg.update("Task", task_id, {"sg_description" : camera_path})

    def update_camera_path(self, task_id, exr_path):
        self.sg.update("Task", task_id, {"sg_description" : exr_path})

    def update_undistortion_size(self, shot_id, undistortion_width, undistortion_height):
        self.sg.update("Shot", shot_id, {"sg_undistortion_width" : undistortion_width,
                                         "sg_undistortion_height" : undistortion_height})


# Asset & Shot Upload
    def get_artist_name(self, user_id):

        filter = [["id", "is", user_id]]
        field = ["name"]
        artist_info = self.sg.find_one("HumanUser", filters=filter, fields=field)
        artist_name = artist_info["id"]
        print(artist_name)

        return artist_name

    def get_project_id_by_name(self, project):
        # Get project id by project name
        filter = [["name", "is", project]]
        field = ["id"]
        project_info = self.sg.find_one("Project", filters=filter, fields=field)
        project_id = project_info["id"]

        return project_id


    def sg_upload_image(self, png_path):
        self.sg.upload("Task", self.task_id, png_path, "image")


    def sg_asset_upload_mov(self, project_id, version, comment, selected_asset_id, user_id, mov_path):

        # Version Entity
        version_data = {
            "project":{"type" : "Project", "id" : project_id},
            "code" : version,
            "description" : comment,
            "entity" : {"type": "Asset", "id": selected_asset_id}, # Connects to Asset Entity.
            "sg_task" : {"type": "Task", "id": self.task_id}, # Connects to Task Entity.
            "sg_status_list" : "pub"
        }

        new_version = self.sg.create("Version", version_data) # Create Add Version
        version_id = new_version["id"]

        self.sg.update("Version", version_id, {"user" : {"type" : "HumanUser", "id" : user_id}}) # Upload Artist field
        self.sg.upload("Version", version_id, mov_path, "sg_uploaded_movie") # Upload mov file

    def sg_shot_upload_mov(self, project_id, version, comment, selected_seq_id, user_id, mov_path):

        # Version Entity
        version_data = {
            "project":{"type" : "Project", "id" : project_id},
            "code" : version,
            "description" : comment,
            "entity" : {"type": "Shot", "id": selected_seq_id}, # Connects to Shot Entity.
            "sg_task" : {"type": "Task", "id": self.task_id}, # Connects to Task Entity.
            "sg_status_list" : "pub"
        }

        new_version = self.sg.create("Version", version_data) # Create Add Version
        version_id = new_version["id"]

        self.sg.update("Version", version_id, {"user" : {"type" : "HumanUser", "id" : user_id}}) # Upload Artist field
        self.sg.upload("Version", version_id, mov_path, "sg_uploaded_movie") # Upload mov file


    def sg_asset_status_update_pub(self, selected_asset_name, task):
        # Get asset id
        asset_filter = [["code", "is", selected_asset_name]]
        asset_field = ["id"]
        asset_info = self.sg.find_one("Asset", filters=asset_filter, fields=asset_field) # {'type': 'Asset', 'id': 1789}

        self.selected_asset_id = asset_info["id"]

        # Get task id (mod, lkd, rig)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"] # 14 (mod step id)
        filter =[
            ["entity", "is", {"type": "Asset", "id": self.selected_asset_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                 ] 
        field = ["id"]
        task_info = self.sg.find_one("Task", filters=filter, fields=field) # find status fields that meet asset id, task id conditions
        self.task_id = task_info["id"]

        self.sg.update("Task", self.task_id, {"sg_status_list" : "pub"})
        print(f"Update the status of {self.task_id} to 'pub' on the asset entity.")

    def sg_shot_status_update_pub(self, selected_seq_num, task):
        # Get seq id
        seq_filter = [["code", "is", selected_seq_num]] # OPN_0010
        seq_field = ["id"]
        seq_info = self.sg.find_one("Shot", filters=seq_filter, fields=seq_field) # {'type': 'Asset', 'id': 1789}
        selected_seq_num_id = seq_info["id"]

        # Get task id (ly, ani, lgt)
        step = self.sg.find_one("Step",[["code", "is", task]], ["id"])
        step_id = step["id"] # 277 (ly step id)

        # # find status fields that meet seq id, task id conditions
        filter =[
            ["entity", "is", {"type": "Shot", "id": selected_seq_num_id}],
            ["step", "is", {"type": "Step", "id": step_id}]
                 ] 
        field = ["id"]
        task_info = self.sg.find_one("Task", filters=filter, fields=field)
        print(task_info)
        task_id = task_info["id"]

        self.sg.update("Task", task_id, {"sg_status_list": "pub"})
        print(f"Update the status of {task_id} to 'pub' on the Sequence entity.")
