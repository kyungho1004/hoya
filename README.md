# BloodMap v3.14 (클린 설치본)
- 모바일 줄꼬임 방지
- 별명 + PIN(4자리) 저장키 → 중복 방지
- 육종 카테고리 **진단명** 분리
- 항암제/항생제 **한글 병기**
- 특수검사(암별) + **일반 특수검사(보체/단백뇨/요당/혈뇨/ACR/UPCR)** 토글
- `bloodmap.app_user` **shim 포함** (런처 호환)

## 설치
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 구조
```
project_root/
├── streamlit_app.py
├── config.py
├── requirements.txt
├── README.md
├── data/            # 세션/내보내기 등 로컬 데이터 (선택)
├── fonts/           # PDF용 폰트 넣을 곳 (선택)
├── bloodmap_app/
│   ├── __init__.py
│   ├── app.py
│   ├── drug_data.py
│   ├── utils.py
│   ├── style.css
│   └── config.py    # import 안전용 복사본
└── bloodmap/
    ├── __init__.py
    └── app_user.py
```
