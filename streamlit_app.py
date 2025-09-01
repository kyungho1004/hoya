
import sys
import os

# bloodmap_app 경로를 강제로 인식시켜줌
sys.path.append(os.path.join(os.path.dirname(__file__), "bloodmap_app"))

# streamlit_main.py 안의 main() 호출
from streamlit_main import main

if __name__ == "__main__":
    main()
