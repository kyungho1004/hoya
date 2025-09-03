BloodMap Bootstrap Full
-----------------------
이 패키지는 `bloodmap_app`을 삭제한 뒤, 실제 메인 앱 폴더를 `bloodmap/`로 통일해
바로 실행할 수 있도록 구성된 완전체 뼈대입니다.

✔ 포함
- bloodmap/app.py (업로드본 + 안전 main())
- bloodmap/style.css (업로드본)
- bloodmap/utils.py, bloodmap/drug_data.py, bloodmap/config.py (빈 스텁)
- main.py, main/app/run.py, streamlit_app.py (진입점)
- fonts/ (빈 폴더), bloodmap/data/ (빈 폴더)

▶ 사용
1) 프로젝트 루트에 압축을 풀어주세요.
2) 기존에 쓰던 utils.py, drug_data.py 실제 내용을 `bloodmap/`에 덮어쓰세요.
3) 실행:
   - 로컬:     streamlit run streamlit_app.py
   - 배포:     main.py 또는 main/app/run.py 자동 인식

푸터 정책 문구는 app.py 내부에서 st.caption(...)으로 추가하세요.
