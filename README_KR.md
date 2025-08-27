# 피수치 해석기 실행 가이드 (KR)

## 1) 설치
```bash
# (권장) 새 가상환경 만들기
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 패키지 설치
pip install -U pip
pip install -r requirements.txt
```

## 2) 실행
```bash
streamlit run streamlit_app.py
```

실행 후 브라우저가 자동으로 열리며, 모바일에서도 줄꼬임 없이 사용 가능합니다.

## 3) 필수/선택 기능
- PDF 내보내기 사용 시: `reportlab` 이미 포함(requirements.txt)
- 그래프 기능 사용 시: `pandas` 이미 포함
- 프리셋/임계값/위험 배지/3줄요약/파일명 개선: **이미 코드에 반영 완료**

## 4) 자주 묻는 질문
- 포트 변경하고 싶어요? → `streamlit run streamlit_app.py --server.port 8080`
- 외부 접속 허용하고 싶어요? → `streamlit run streamlit_app.py --server.address 0.0.0.0`
- PDF 폰트가 한글이 깨져요? → 시스템에 `NanumGothic.ttf`가 없으면 기본 Helvetica로 대체됩니다. 
  한글 폰트를 강제 사용하려면 같은 폴더에 `NanumGothic.ttf`를 넣어주세요.

## 5) 배포(선택)
- **Streamlit Community Cloud**: 리포지토리에 `streamlit_app.py`와 `requirements.txt`만 있어도 바로 동작
- **Docker(선택)**:
  ```Dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8501
  CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  ```
