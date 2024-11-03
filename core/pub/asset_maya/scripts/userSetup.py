# Maya가 시작될 때 자동으로 실행되는 Python 스크립트

import maya.utils as mu # Maya 유틸리티 모듈을 가져옴
import my_menu        # test_menu.py 모듈을 가져옴

mu.executeDeferred('my_menu.add_menu()') # Maya가 완전히 초기화된 후에 test_menu.add_menu() 함수를 호출하도록