# Asset Publish - Shotgrid 연동
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget
from shotgun_api3 import shotgun

class AssetPublish(QWidget):

    def __init__(self):
        super().__init__()
        print("*******")
        self.sg = self.connect_sg()
        self.temp_info()

    def connect_sg(self):
        URL = "https://4thacademy.shotgrid.autodesk.com"
        SCRIPT_NAME = "moomins_key"
        API_KEY = "gbug$apfmqxuorfqaoa3tbeQn"
    
        sg = shotgun.Shotgun(URL,
                                SCRIPT_NAME,
                                API_KEY)
        return sg

# 임시로 문자 넣어놨는데, 나중에 UI에서 입력한 comment, file path로 변경 필요
    def temp_info(self):
        comment = "에셋 퍼블리셔 샷그리드 링크 테스트입니다!" # asset 엔티티의 description 필드에 update
        png_path = "/home/rapa/wip/Marvelous/asset/Character/dami/modeling/wip/image/test.png" # asset 엔티티의 image 필드에 업로드
        mov_path = "/home/rapa/wip/Marvelous/asset/Character/dami/modeling/wip/image/test.mov" # add version할 때 쓰이게
        self.test(comment, png_path, mov_path)

# 임시로 그냥 실행되게 했는데, upload 버튼 누르면 실행되도록 해야 함
    def test(self, comment, png_path, mov_path):
        project_id = 188 # Moomins 프로젝트
        user_id = 121
        version_code = "v022"
        asset_id = 1547 # 업데이트 할 asset id

        # Version Entity
        version_data = {
            "project":{"type" : "Project", "id" : project_id},
            "code" : version_code,
        }
        new_version = self.sg.create("Version", version_data) # Add Version 생성
        version_id = new_version["id"]

        self.sg.update("Version", version_id, {"user" : {"type" : "HumanUser", "id" : user_id}}) # artist 변경
        self.sg.update("Version", version_id, {"description": comment}) # 코멘트 올리기
        self.sg.update("Version", version_id, {"sg_uploaded_movie_frame_rate": float(24)}) # fps 올리기
        self.sg.upload("Version", version_id, mov_path, "sg_uploaded_movie") # mov 업로드

        # filter = [[]]
        # field = ["id", "content", "entity"]
        # task_data = self.sg.find_one("Task", filters=filter, fields=field)
        task_data = "" ################################ publisher에서 받아 와야 함

        self.sg.update("Version", version_id, {"sg_task": {"type": "Task", "id": task_data["id"]}})
        self.sg.update("Version", version_id, {"sg_task": {"type": "Task", "id": task_data["content"]}})


        # Asset Entity (task 말고 asset..?)
        self.sg.upload("Asset", asset_id, png_path, "image") # thumbnail png 넣기  (이미 이미지가 있을 경우에는 업로드 안됨)
        self.sg.update("Asset", asset_id, {"description": comment}) # asset description 변경
        self.sg.update("Asset", asset_id, {"sg_status_list":"wip"}) # asset status 변경



if __name__ == "__main__":
    app = QApplication()
    win = AssetPublish()
    # win.show()
    app.exec()