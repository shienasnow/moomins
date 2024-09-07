# coding=utf-8
# @Time    : 2020/07/05 15:46
# @Author  : é¡¶å¤©ç«å°æºæ§å¤§å°å
# @File    : vaccine.py
# ä»ä½ä¸ºå¬å¸åé¨ä½¿ç¨ä¿æ¤ ä¸æ¦æ³é²åºå»é æçå½±å æ¬äººæ¦ä¸è´è´£
import maya.cmds as cmds
import os
import shutil


class phage:
    @staticmethod
    def backup(path):
        folder_path = path.rsplit('/', 1)[0]
        file_name = path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        backup_folder = folder_path + '/history'
        new_file = backup_folder + '/' + file_name + '_backup.ma '
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
        shutil.copyfile(path, new_file)

    def antivirus(self):
        health = True
        self.clone_gene()
        self.antivirus_virus_base()
        virus_gene = ['sysytenasdasdfsadfsdaf_dsfsdfaasd', 'PuTianTongQing', 'daxunhuan']
        all_script_jobs = cmds.scriptJob(listJobs=True)
        for each_job in all_script_jobs:
            for each_gene in virus_gene:
                if each_gene in each_job:
                    health = False
                    job_num = int(each_job.split(':', 1)[0])
                    cmds.scriptJob(kill=job_num, force=True)
        all_script = cmds.ls(type='script')
        if all_script:
            for each_script in all_script:
                commecnt = cmds.getAttr(each_script + '.before')
                for each_gene in virus_gene:
                    if commecnt:
                        if each_gene in commecnt:
                            try:
                                cmds.delete(each_script)
                            except:
                                name_space = each_script.rsplit(':',1)[0]
                                cmds.error(u'{}è¢«ææäºï¼ä½æ¯ææ²¡æ³å é¤'.format(name_space))
        if not health:
            file_path = cmds.file(query=True, sceneName=True)
            self.backup(file_path)
            cmds.file(save=True)
            cmds.error(u'ä½ çæä»¶è¢«ææäºï¼ä½æ¯æè´´å¿çä¸ºæ¨ææ¯å¹¶ä¸å¤ä»½äº~ä¸ç¨è°¢~')
        else:
            cmds.warning(u'ä½ çæä»¶è´¼å¥åº·~æå°±è¯´ä¸å£°æ²¡æå«çææ')

    @staticmethod
    def antivirus_virus_base():
        virus_base = cmds.internalVar(userAppDir=True) + '/scripts/userSetup.mel'
        if os.path.exists(virus_base):
            try:
                os.remove(virus_base)
            except:
                cmds.error(u'ææ¯å¤±è´¥')

    def clone_gene(self):
        vaccine_path = cmds.internalVar(userAppDir=True) + '/scripts/vaccine.py'
        if not cmds.objExists('vaccine_gene'):
            if os.path.exists(vaccine_path):
                gene = list()
                with open(vaccine_path, "r") as f:
                    for line in f.readlines():
                        gene.append(line)
                    cmds.scriptNode(st=1,
                                    bs="petri_dish_path = cmds.internalVar(userAppDir=True) + 'scripts/userSetup.py'\npetri_dish_gene = ['import sys\\r\\n', 'import maya.cmds as cmds\\r\\n', \"maya_path = cmds.internalVar(userAppDir=True) + '/scripts'\\r\\n\", 'if maya_path not in sys.path:\\r\\n', '    sys.path.append(maya_path)\\r\\n', 'import vaccine\\r\\n', \"cmds.evalDeferred('leukocyte = vaccine.phage()')\\r\\n\", \"cmds.evalDeferred('leukocyte.occupation()')\"]\nwith open(petri_dish_path, \"w\") as f:\n\tf.writelines(petri_dish_gene)",
                                    n='vaccine_gene', stp='python')
                    cmds.addAttr('vaccine_gene', ln="notes", sn="nts", dt="string")
                    cmds.setAttr('vaccine_gene.notes', gene, type='string')
        if not cmds.objExists('breed_gene'):
            cmds.scriptNode(st=1,
                            bs="import os\nvaccine_path = cmds.internalVar(userAppDir=True) + '/scripts/vaccine.py'\nif not os.path.exists(vaccine_path):\n\tif cmds.objExists('vaccine_gene'):\n\t\tgene = eval(cmds.getAttr('vaccine_gene.notes'))\n\t\twith open(vaccine_path, \"w\") as f:\n\t\t\tf.writelines(gene)",
                            n='breed_gene', stp='python')

    def occupation(self):
        cmds.scriptJob(event=["SceneSaved", "leukocyte.antivirus()"], protected=True)
