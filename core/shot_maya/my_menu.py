import maya.cmds as cmds
import maya.mel as mel
import sys
import os
from importlib import reload

my_path = os.path.dirname(__file__)
sys.path.append(my_path)


def asset_import_func():
    global win
    import scripts.asset_loader as asset_loader
    reload(asset_loader)
    win = asset_loader.AssetLoader()
    win.show()

def shot_upload_func():
    global shot_upload_win
    import scripts.upload.shot_upload as shot_upload
    reload(shot_upload)
    shot_upload_win = shot_upload.ShotUpload()
    shot_upload_win.show()

def shot_publish_func():
    global shot_publish_win
    import scripts.publish.shot_publish as shot_publish
    reload(shot_publish)
    shot_publish_win = shot_publish.ShotPublish()
    shot_publish_win.show()


def add_menu():
    gMainWindow = mel.eval('$window=$gMainWindow') # Maya's main window
    custom_menu = cmds.menu(parent=gMainWindow, tearOff = True, label = 'Pipeline') # Add a new menu to the main window
    cmds.menuItem("import_assets", label="Import Assets", parent=custom_menu, command=lambda *args: asset_import_func()) # Adding items from menus, Commands to be executed when clicked
    cmds.menuItem("shot_upload", label="Shot Upload", parent=custom_menu, command=lambda *args: shot_upload_func())
    cmds.menuItem("shot_publish", label="Shot Publish",parent=custom_menu, command=lambda *args: shot_publish_func())