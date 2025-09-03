# BloodMap Full Package (with alias fix)

## 포함된 파일
- main.py                  → 호스트 진입점
- main/app/run.py          → 일부 호스트가 찾는 경로
- streamlit_app.py         → Streamlit 실행 파일
- bloodmap/                → alias (bloodmap → bloodmap_app)
- bloodmap_app/            → 실제 앱 코드 위치
- fonts/                   → PDF 폰트 위치
- config.py, __init__.py   → 루트 기본 파일

## 사용법
1. bloodmap_app/ 안에 실제 app.py, utils/, data/, style.css 등을 넣으세요.
2. streamlit 로컬 실행: 
   ```bash
   streamlit run streamlit_app.py
   ```
3. 배포 환경은 main.py 또는 main/app/run.py 자동 인식.
4. 일부 호스트가 bloodmap 모듈만 찾을 경우 alias bloodmap/ 폴더가 자동 연결.

## 고지문
- ⚠️ 문제가 생길 경우 데이터는 삭제될 수 있습니다.
- 🔒 개인정보는 절대 수집하지 않습니다.
