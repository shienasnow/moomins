import maya.cmds as cmds
import maya.mel as mel
import sys
import os
from importlib import reload

my_path = os.path.dirname(__file__)
sys.path.append(my_path)


def asset_import_func():
    global win
    import asset_import
    reload(asset_import)
    win = asset_import.Import()
    win.show()

def shot_upload_func():
    global shot_upload_win
    import shot_uploader
    reload(shot_uploader)
    shot_upload_win = shot_uploader.ShotUpload()
    shot_upload_win.show()

def shot_publish_func():
    global shot_publish_win
    import shot_publish
    reload(shot_publish)
    shot_publish_win = shot_publish.ShotPublish()
    shot_publish_win.show()


def add_menu():
    gMainWindow = mel.eval('$window=$gMainWindow') # 마야의 메인 윈도우
    custom_menu = cmds.menu(parent=gMainWindow, tearOff = True, label = 'Pipeline') # 메인 윈도우에 새 메뉴 추가 
    cmds.menuItem("import_assets", label="Import Assets", parent=custom_menu, command=lambda *args: asset_import_func())# 메뉴의 항목 추가, 클릭시 실행될 명령어 설정
    cmds.menuItem("shot_upload", label="Shot Upload", parent=custom_menu, command=lambda *args: shot_upload_func())
    cmds.menuItem("shot_publish", label="Shot Publish",parent=custom_menu, command=lambda *args: shot_publish_func())
