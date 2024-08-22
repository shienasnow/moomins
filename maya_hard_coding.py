import maya.cmds as cmds

def create_pub_panel():
    # 기존에 같은 이름의 workspaceControl이 있는지 확인하고 삭제
    if cmds.workspaceControl('pubWorkspaceControl', exists=True):
        cmds.deleteUI('pubWorkspaceControl')

    # 새 workspaceControl 생성
    pub_panel = cmds.workspaceControl(
        'pubWorkspaceControl', 
        label='Pub Panel', 
        tabToControl=["AttributeEditor", -1], 
        widthProperty="preferred",
        height=200
    )
    
    # workspaceControl 내에 formLayout을 생성
    form = cmds.formLayout(parent=pub_panel)
    
    # 버튼 생성
    button = cmds.button(parent=form, label='Click Me', width=100, height=40)  # 버튼 크기 설정
    
    # 패널의 중앙에 버튼을 배치
    cmds.formLayout(form, edit=True,
                    attachForm=[(button, 'top', 0), (button, 'bottom', 0), (button, 'left', 0), (button, 'right', 0)],
                    attachNone=[(button, 'center')],
                    attachControl=[(button, 'top', 0, form),
                                   (button, 'left', 0, form),
                                   (button, 'bottom', 0, form),
                                   (button, 'right', 0, form)],
                    )

# create_pub_panel 함수를 호출하여 패널과 버튼을 생성
create_pub_panel()