
import nuke

class NukeApi:
    def __init__(self):
        pass
    
    @staticmethod
    def check_read_node_connection(node_name):
        
        """
        주어진 노드에 Read 노드가 연결됐는지 확인합니다.
        
        input type = str
        
        output = Bool
        
        Read노드가 있으면 True 없으면 False 반환
        
        """
        
        current_node = nuke.toNode(node_name)
    
        if current_node is None:
            raise nuke.message(f"ReadNode is None")
        
        while current_node is not None:
            # 현재 노드의 클래스가 Read인지 확인합니다
            if current_node.Class() == "Read":
                return True
            # 다음 노드로 이동합니다 (상위 노드로)
            current_node = current_node.input(0)
        
        return False
