
# 피수치 자동 해석기 (v9.1.1 hotfix)

환자/보호자를 위한 **혈액/전해질 자동 해석 + 식단 가이드** 앱.  
- 카테고리: **항암 치료(19종 입력)** · **투석 환자** · **당뇨 환자** · **일반 해석(WBC/Hb/PLT/ANC/CRP/체온)**  
- 결과는 **.md / .pdf** 로 바로 다운로드 가능 (모바일 지원).  
- **홈 화면 추가 가이드** 버튼 내장(iOS/Android).

---

## 1) 설치 / 실행 (로컬)
```bash
# 1) 가상환경(선택)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) 의존성
pip install -r requirements.txt

# 3) 실행
streamlit run app.py
```
- 브라우저 자동 오픈. 안 열리면 `http://localhost:8501` 접속.

---

## 2) 배포 (Streamlit Cloud)
1. GitHub에 다음 파일 업로드
   - `app.py`
   - `requirements.txt` (아래 예시 확인)
2. https://streamlit.io/cloud 접속 → 새 앱 배포 → GitHub repo 선택
3. 배포 완료되면 `*.streamlit.app` 주소 발급 → 공유

### `requirements.txt` 예시
```
streamlit>=1.36
reportlab>=3.6   # PDF 내보내기 사용
```

> **PDF 버튼이 안 보이면** Cloud 환경에 `reportlab` 설치가 안 된 경우입니다.  
> 위 requirements를 커밋/배포한 뒤 다시 시도하세요.

---

## 3) 파일 구조
```
app.py                # 메인 앱
requirements.txt      # 의존성
README.md             # (선택) 배포/사용 가이드
```
- 실행/배포 시 `app.py`만 있어도 동작. (PDF 출력은 reportlab 필요)

---

## 4) 사용법 (요약)
1. 상단 **카테고리** 선택
   - 항암 치료: 19종 혈액검사 값 입력 + 체온
   - 투석 환자: K/Na/Ca/Phos/BUN/Cr/Alb/Hb + 체중증가
   - 당뇨 환자: FPG/PP2/HbA1c + Hb/Alb
   - 일반 해석: **WBC/Hb/PLT/ANC/CRP/체온**
2. **별명** 입력 (결과 저장/다운로드에 필요)
3. **🔎 해석하기** → 요약/가이드 표시
4. 결과 하단에서 **.md / .pdf** 다운로드

---

## 5) 홈 화면에 추가 (모바일)
- **iPhone**: Safari → 공유(⬆️) → *홈 화면에 추가*  
- **Android**: Chrome → 메뉴(⋮) → *홈 화면에 추가* 또는 *앱 설치*  
- 카톡/네이버 **인앱 브라우저에서는 비권장** (다운로드/설치 제한 있음)

---

## 6) 자주 묻는 오류 (Troubleshooting)
- **PDF 버튼이 없음**: `reportlab` 미설치 → `requirements.txt`에 추가 후 재배포
- **다운로드가 안 됨**: 인앱 브라우저에서 열었는지 확인 → Chrome/Safari로 다시 열기
- **저장/다운로드 버튼이 없음**: 별명 미입력
- **앱이 멈춤/오류**: v9.1.1은 오류가 나도 죽지 않음. 사이드바의 **🐞 디버그 모드** 켜고 메시지 확인

---

## 7) 개인정보 / 주의
- 이 앱은 의료진의 진단/처방을 **대체하지 않습니다.**  
- 입력 값은 **로컬 세션/다운로드 파일**에만 저장됩니다. (서버 DB 저장 없음)  
- 결과 공유 시 개인정보가 포함되지 않도록 주의하세요.

---

## 8) 릴리스 노트 (요약)
- v9.1: **PDF 다운로드** 추가, **병원에서 가능한 식단**(항암) 추가
- v9.1.1 hotfix: reportlab 방어 처리, 오류 시 앱 비정지, 디버그 모드

---

## 9) 바로 사용 (배포 링크 예시)
- 예: https://your-app-name.streamlit.app (배포 후 실제 주소로 교체)

---

### Maintainer
- Hoya/GPT
- Feedback: (구글 폼/이메일 등 삽입)
