
import json
from datetime import datetime
import streamlit as st

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기 (Android 튜닝판)")
st.markdown("👤 **제작자: Hoya / 자문: GPT**")

# --- ANDROID-FOCUSED CSS ---
# 1) 강제 단일 컬럼
# 2) 버튼/라디오/체크박스 1열 + 100% 폭
# 3) 입력 폰트 16px 이상 -> 모바일 브라우저 자동 줌/줄이동 방지
# 4) 삼성 인터넷/크롬 flex 깨짐 방지
# 5) 넘버 인풋 스피너 숨김 -> 레이아웃 흔들림 방지
st.markdown("""
<style>
html, body { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
.block-container { padding-top: 8px !important; }
@media (max-width: 480px) {
  .block-container { max-width: 430px !important; margin: 0 auto !important; }
  label, .stMarkdown p, .stRadio label, .stCheckbox label { 
    font-size: 16px !important; line-height: 1.25rem !important; 
    overflow-wrap: anywhere; word-break: keep-all;
  }
}
/* 강제 단일 컬럼 */
[data-testid="stHorizontalBlock"] { display: block !important; }
div.row-widget.stRadio > div { flex-direction: column !important; gap: .3rem !important; }
.stButton button { width: 100% !important; }
/* 입력 폭 고정 + 폰트 16px (모바일 자동 확대 방지) */
.stNumberInput input, .stTextInput input, .stDateInput input, 
.stSelectbox div[data-baseweb="select"] *,
.stMultiSelect div[data-baseweb="select"] * { 
  width: 100% !important; font-size: 16px !important; 
}
/* 넘버 인풋 스피너 제거로 레이아웃 안정화 */
input[type=number]::-webkit-outer-spin-button,
input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
/* select 메뉴가 좁게 렌더링되는 이슈 방지 */
[data-baseweb="select"] { width: 100% !important; }
/* 버튼 주변 여백 통일 */
.stButton { margin-top: .25rem; margin-bottom: .25rem; }
/* 카드 느낌 구분선 */
hr { opacity: .4; }
</style>
""", unsafe_allow_html=True)

ORDER = ["WBC","Hb","PLT","ANC","Ca","P","Na","K","Albumin","Glucose","Total Protein",
         "AST","ALT","LDH","CRP","Cr","Uric Acid","Total Bilirubin","BUN","BNP"]

LABELS = {
    "WBC":"WBC", "Hb":"Hb", "PLT":"PLT", "ANC":"ANC",
    "Ca":"Ca", "P":"P", "Na":"Na", "K":"K",
    "Albumin":"Albumin", "Glucose":"Glucose", "Total Protein":"TP",
    "AST":"AST", "ALT":"ALT", "LDH":"LDH", "CRP":"CRP",
    "Cr":"Cr", "Uric Acid":"UA", "Total Bilirubin":"TB", "BUN":"BUN", "BNP":"BNP"
}

ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염","광과민"]},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부/점막 건조","두통"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응","드물게 비장비대"]},
}
ABX_GUIDE = {"페니실린계":["발진/설사"],"세팔로스포린계":["설사"],
             "마크롤라이드":["QT 연장","CYP 상호작용"],"플루오로퀴놀론":["힘줄염/파열","광과민"],
             "카바페넴":["경련 위험(고용량/신부전)"],"TMP-SMX":["고칼륨혈증","골수억제"],
             "메트로니다졸":["금주"],"반코마이신":["Red man(주입속도)","신독성"]}
FOODS = {"Albumin_low":["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
         "K_low":["바나나","감자","호박죽","고구마","오렌지"],
         "Hb_low":["소고기","시금치","두부","달걀 노른자","렌틸콩"],
         "Na_low":["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
         "Ca_low":["연어 통조림","두부","케일","브로콜리","(참깨 제외)"]}
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"

def entered(v):
    try:
        return v is not None and str(v) != "" and float(v) is not None
    except Exception:
        return False

def interp(l):
    out=[]
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")): add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")): add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")): add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")): add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")): add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")): add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")): add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

if "records" not in st.session_state: st.session_state.records = {}

st.divider()
st.header("1️⃣ 환자 정보 입력")
nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동", key="nick")
exam_date = st.date_input("검사 날짜", value=datetime.today(), key="date")

st.divider()
st.header("2️⃣ 혈액 검사 수치 입력 (입력한 항목만 결과에 표시)")
vals = {}
for key in ORDER:
    step = 0.1 if key not in ("PLT","ANC","Glucose","AST","ALT","LDH","BNP") else 1.0
    fmt = "%.1f" if step == 0.1 else "%.0f"
    vals[key] = st.number_input(LABELS[key], step=step, format=fmt, key=f"lab_{key}")

st.divider()
st.header("3️⃣ 카테고리 및 추가 정보")
category = st.radio("카테고리", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], index=0, key="cat")

extras, meds = {}, {}
if category == "항암치료":
    if st.checkbox("ARA-C 사용", key="use_arac"):
        meds["ARA-C"] = {
            "form": st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key="arac_form"),
            "dose": st.number_input("ARA-C 용량/일(임의 입력)", min_value=0.0, step=0.1, key="arac_dose"),
        }
    for key in ["6-MP","MTX","ATRA","G-CSF"]:
        if st.checkbox(f"{key} 사용", key=f"use_{key}"):
            meds[key] = {"dose_or_tabs": st.number_input(f"{key} 투여량/알약 개수(소수 허용)", min_value=0.0, step=0.1, key=f"dose_{key}")}
elif category == "항생제":
    extras["abx"] = st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()), key="abx_multi")
elif category == "투석 환자":
    extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0, key="urine_ml")
    extras["hd_today"] = st.checkbox("오늘 투석 시행", key="hd_today")
    extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1, key="post_hd_delta")
elif category == "당뇨 환자":
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0, key="fpg")
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="pp1")
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0, key="pp2")
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f", key="a1c")

st.divider()
run = st.button("🔎 해석하기", use_container_width=True)

if run:
    st.subheader("📋 해석 결과")
    for line in interp(vals): st.write(line)

    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서(.md)
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 별명: {nickname or '미기재'}\n",
           f"- 검사일: {exam_date}\n",
           f"- 카테고리: {category}\n\n"]
    for k in ORDER:
        v = vals.get(k)
        if entered(v): buf.append(f"- {k}: {v}\n")
    st.download_button("📥 보고서(.md) 다운로드",
                       data="".join(buf).encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")

    # 저장
    if nickname.strip():
        rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "date": str(exam_date),
               "category": category,
               "labs": {k:v for k,v in vals.items() if entered(v)},
               "meds": meds, "extras": extras}
        st.session_state.records.setdefault(nickname, []).append(rec)
        st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")

st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.records:
        sel = st.selectbox("별명 선택", sorted(st.session_state.records.keys()))
        rows = st.session_state.records.get(sel, [])
        if rows:
            data = [{"ts": r["ts"], **{k: r["labs"].get(k) for k in ["WBC","Hb","PLT","CRP","ANC"]}} for r in rows]
            import pandas as pd
            df = pd.DataFrame(data).set_index("ts")
            st.line_chart(df.dropna(how="all"))
    else:
        st.info("아직 저장된 기록이 없습니다.")

