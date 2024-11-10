import maya.cmds as cmds
import maya.mel as mel
import sys
import os
from importlib import reload

my_path = os.path.dirname(__file__)
sys.path.append(my_path)


def asset_upload_func():
    global asset_upload_win
    import moomins.core.asset_maya.scripts.upload.asset_upload as asset_upload
    reload(asset_upload)
    asset_upload_win = asset_upload.AssetUpload()
    asset_upload_win.show()

def asset_publish_func():
    global asset_publish_win
    import moomins.core.asset_maya.scripts.publish.asset_publish as asset_publish
    reload(asset_publish)
    asset_publish_win = asset_publish.AssetPublish()
    asset_publish_win.show()

def add_menu():
    gMainWindow = mel.eval('$window=$gMainWindow') # 마야의 메인 윈도우
    custom_menu = cmds.menu(parent=gMainWindow, tearOff = True, label = 'Pipeline') # 메인 윈도우에 새 메뉴 추가 
    cmds.menuItem("asset_upload", label="Asset Upload", parent=custom_menu, command=lambda *args: asset_upload_func())
    cmds.menuItem("asset_publish", label="Asset Publish",parent=custom_menu, command=lambda *args: asset_publish_func())