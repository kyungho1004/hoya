
# BloodMap App v3.14 (완전체)

## 실행 방법
```bash
pip install streamlit pandas reportlab
streamlit run app.py
```
- PDF 한글 폰트 고정 기능을 쓰려면 `fonts/` 폴더에 아래 파일을 넣어주세요:
  - `fonts/NanumGothic-Regular.ttf` (필수)
  - `fonts/NanumGothic-Bold.ttf` (선택)
  - `fonts/NanumGothic-ExtraBold.ttf` (선택)
- 폰트가 없으면 PDF 버튼 클릭 시 경고 메시지가 나오고, MD/TXT는 정상 다운로드됩니다.

## 폴더 구조
```
bloodmap_app_v3_14/
├── app.py
├── config.py
├── data/
│   ├── __init__.py
│   ├── drugs.py
│   ├── foods.py
│   └── ped.py
├── utils/
│   ├── __init__.py
│   ├── inputs.py
│   ├── interpret.py
│   ├── reports.py
│   ├── graphs.py
│   └── schedule.py
└── fonts/
    └── .keep
```

## 비고
- 모바일 줄꼬임 방지, 별명 저장/그래프, 항암 스케줄표, 계절 식재료/레시피, ANC 가정/병원 구분, 항암제/항생제 사전 뷰어 포함.
- Streamlit Cloud 배포 시에도 동일 구조 그대로 업로드하면 동작합니다.
