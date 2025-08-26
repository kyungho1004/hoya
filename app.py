
import os, shutil

KEEP = {"streamlit_app_plus_debug.py", "README.md", "README.txt"}

for name in os.listdir("."):
    if name in KEEP:
        continue
    try:
        if os.path.isdir(name):
            shutil.rmtree(name)
        else:
            os.remove(name)
        print("삭제:", name)
    except Exception as e:
        print("건너뜀:", name, e)

print("완료. 남긴 파일:", ", ".join(sorted(KEEP)))
