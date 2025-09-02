# Korean Font Pack for BloodMap (Nanum Gothic)

이 패키지는 **한글 깨짐 방지**를 위해 프로젝트 루트에 `fonts/` 폴더를 만들고
`NanumGothic-Regular.ttf` / `NanumGothic-Bold.ttf`를 자동으로 내려받아 넣어주는 스크립트를 포함합니다.

## 사용 방법
1) 압축을 BloodMap 프로젝트 루트에 풀기 (또는 폴더를 복사해 넣기)
2) 아래 스크립트를 실행
   ```bash
   python install_fonts.py
   ```
3) 완료 후 생성되는 경로:
   ```
   project_root/fonts/NanumGothic.ttf            (Regular로 심볼릭/복사본 제공)
   project_root/fonts/NanumGothic-Regular.ttf
   project_root/fonts/NanumGothic-Bold.ttf
   ```
4) 앱 실행
   ```bash
   streamlit run streamlit_app.py
   ```

## 참고
- `config.py`의 경로는 `FONT_PATH_REG = "fonts/NanumGothic.ttf"`로 맞춰져 있으므로
  위 스크립트가 만든 파일 구조면 그대로 동작합니다.
- 인터넷 연결이 필요합니다(구글 폰트 GitHub에서 받음).
- 회사/병원 네트워크 차단 시, 수동으로 ttf 파일을 구해 `project_root/fonts/`에 넣어도 됩니다.
