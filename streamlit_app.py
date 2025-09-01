import sys
import os

# 현재 파일 기준으로 bloodmap_app 폴더 경로를 시스템 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "bloodmap_app"))

from streamlit_main import main

if __name__ == "__main__":
    main()
