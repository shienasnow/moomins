import nuke
import sys
sys.path.append("/home/rapa/git/pipeline/api_scripts")

from python.nuke_import import NukeImport
from python.nuke_upload import NukeUpload
from python.nuke_publish import NukePublish
menu_bar = nuke.menu("Nuke")

def open_asset_importer():
    global importer
    importer = NukeImport()
    importer.show()
    
def open_asset_uploader():
    global uploader
    uploader = NukeUpload()
    uploader.show()
   
def open_nuke_publish():
    global uploader
    uploader = NukePublish()
    uploader.show()
    
    
menu_moomins = menu_bar.addMenu("Pipeline")

menu_moomins.addCommand("Asset Importer",open_asset_importer,"F10")
menu_moomins.addCommand("Asset Uploader",open_asset_uploader,"F11")
menu_moomins.addCommand("Nuke publish",open_nuke_publish,"F12")

