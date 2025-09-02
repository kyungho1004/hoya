
# -*- coding: utf-8 -*-
"""
Nanum Gothic 설치 스크립트
- Google Fonts GitHub에서 Regular/Bold TTF를 내려받아 project_root/fonts/ 에 배치
- config.py의 FONT_PATH_REG = "fonts/NanumGothic.ttf"와 호환되도록 NanumGothic.ttf 사본도 생성
"""
import os, sys

URLS = {
    "NanumGothic-Regular.ttf": "https://github.com/googlefonts/nanumgothic/raw/main/fonts/ttf/NanumGothic-Regular.ttf",
    "NanumGothic-Bold.ttf":    "https://github.com/googlefonts/nanumgothic/raw/main/fonts/ttf/NanumGothic-Bold.ttf",
}

def download(url, path):
    import urllib.request
    print(f"Downloading: {url}")
    with urllib.request.urlopen(url) as r, open(path, "wb") as f:
        f.write(r.read())
    print(f" -> saved: {path} ({os.path.getsize(path)} bytes)")

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(root, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)

    reg_path = os.path.join(fonts_dir, "NanumGothic-Regular.ttf")
    bold_path = os.path.join(fonts_dir, "NanumGothic-Bold.ttf")
    alias_path = os.path.join(fonts_dir, "NanumGothic.ttf")  # 앱 기본 경로 호환용

    # Download if missing
    if not os.path.exists(reg_path):
        download(URLS["NanumGothic-Regular.ttf"], reg_path)
    else:
        print("Exists:", reg_path)

    if not os.path.exists(bold_path):
        download(URLS["NanumGothic-Bold.ttf"], bold_path)
    else:
        print("Exists:", bold_path)

    # Create alias copy for FONT_PATH_REG
    if not os.path.exists(alias_path):
        try:
            import shutil
            shutil.copyfile(reg_path, alias_path)
            print("Alias created:", alias_path)
        except Exception as e:
            print("Alias create failed:", e)
    else:
        print("Exists:", alias_path)

    print("\n완료 ✅  이제 다음을 실행하세요:\n  streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()
