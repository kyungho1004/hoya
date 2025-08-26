
import streamlit as st
import datetime as dt

st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작자: Hoya / 자문: GPT**")

st.divider()
st.header("1️⃣ 환자 정보 입력")
nickname = st.text_input("별명 또는 환자 이름", placeholder="예: 홍길동")
date = st.date_input("검사 날짜", value=dt.date.today())

st.divider()
st.header("2️⃣ 혈액 검사 수치 입력")
st.caption("입력하지 않은 항목은 자동으로 제외됩니다. 숫자만 입력하세요.")

def to_float(x):
    try:
        return float(x)
    except:
        return None

ORDER = [
    ("WBC","WBC (백혈구)","예: 5.2"),
    ("Hb","Hb (혈색소)","예: 11.8"),
    ("PLT","PLT (혈소판)","예: 180"),
    ("ANC","ANC (호중구)","예: 1200"),
    ("Ca","Ca (칼슘)","예: 8.6"),
    ("P","P (인)","예: 3.5"),
    ("Na","Na (소디움)","예: 140"),
    ("K","K (포타슘)","예: 3.6"),
    ("Albumin","Albumin (알부민)","예: 3.2"),
    ("Glucose","Glucose (혈당)","예: 110"),
    ("Total Protein","Total Protein (총단백)","예: 6.6"),
    ("AST","AST","예: 35"),
    ("ALT","ALT","예: 40"),
    ("LDH","LDH","예: 300"),
    ("CRP","CRP","예: 0.2"),
    ("Cr","Creatinine (Cr)","예: 0.9"),
    ("UA","Uric Acid (요산)","예: 4.5"),
    ("TB","Total Bilirubin (TB)","예: 0.8"),
    ("BUN","BUN","예: 18"),
    ("BNP","BNP (선택)","예: 120"),
]

values = {}
for i in range(0, len(ORDER), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(ORDER):
            key, label, ph = ORDER[idx]
            with col:
                val = st.text_input(label, placeholder=ph, key=f"field_{key}")
                values[key] = to_float(val)

st.divider()
st.header("2️⃣-1 카테고리 선택")
category = st.radio("분류", ["일반 해석","항암치료","항생제","투석 환자","당뇨 환자"], horizontal=True)

# ==================== 데이터 ====================
ANTICANCER = {
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치 상승","구내염","오심"],"warn":["황달/진한 소변 시 진료"],"ix":["알로푸리놀 병용 감량"]},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간독성","신독성","구내염"],"warn":["탈수 시 독성↑"],"ix":["NSAIDs/TMP-SMX 병용 주의"]},
    "ATRA":{"alias":"베사노이드 (트레티노인, ATRA)","aes":["분화증후군","발열","피부/점막 건조","두통","설사"],"warn":["분화증후군 주요 증상: 호흡곤란, 기침, 흉통, 부종(체중 증가), 발열, 저혈압","이 증상 동반 시 즉시 병원 연락 필요"],"ix":["테트라사이클린계 병용 시 가성뇌종양 위험"]},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","신경독성(HDAC)"],"warn":["HDAC시 신경증상 보고"],"ix":[]},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통"],"warn":["좌상복부 통증시 평가"],"ix":[]},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소침착"],"warn":[],"ix":[]},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성"],"warn":["누적용량 관리"],"ix":[]},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성"],"warn":[],"ix":[]},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성"],"warn":[],"ix":[]},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염"],"warn":["수분섭취"],"ix":[]},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제"],"warn":[],"ix":[]},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"warn":[],"ix":[]},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염 위험"],"warn":[],"ix":[]},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비"],"warn":["IT투여 금지"],"ix":[]},
}
ABX_GUIDE = {
    "페니실린계":["발진/설사","와파린 효과↑ 가능"],
    "세팔로스포린계":["설사","일부 알코올 병용시 플러싱"],
    "마크롤라이드":["QT 연장","CYP 상호작용"],
    "플루오로퀴놀론":["힘줄염/파열","광과민"],
    "카바페넴":["경련 위험","광범위 커버"],
    "TMP-SMX":["고칼륨혈증","골수억제","MTX 병용 주의"],
    "메트로니다졸":["금주","금속맛"],
    "반코마이신":["Red man 증후군","신독성"],
}
FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}
FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 발열=응급)"

# ==================== 해석 함수 ====================
def entered(v):
    try:
        return v is not None and float(v)==float(v)
    except:
        return False

def interpret_labs(l):
    out=[]
    if entered(l.get("WBC")):
        if l["WBC"]<4: out.append(f"WBC {l['WBC']}: 낮음 → 감염 위험↑")
        elif l["WBC"]>10: out.append(f"WBC {l['WBC']}: 높음 → 감염/염증 가능")
        else: out.append(f"WBC {l['WBC']}: 정상")
    if entered(l.get("Hb")):
        out.append(f"Hb {l['Hb']}: {'낮음 → 빈혈' if l['Hb']<12 else '정상'}")
    if entered(l.get("PLT")):
        out.append(f"혈소판 {l['PLT']}: {'낮음 → 출혈 위험' if l['PLT']<150 else '정상'}")
    if entered(l.get("ANC")):
        anc=l["ANC"]
        if anc<500: out.append(f"ANC {anc}: 중증 감소(<500)")
        elif anc<1500: out.append(f"ANC {anc}: 감소(<1500)")
        else: out.append(f"ANC {anc}: 정상")
    if entered(l.get("Albumin")):
        out.append(f"Albumin {l['Albumin']}: {'낮음 → 영양/간질환' if l['Albumin']<3.5 else '정상'}")
    if entered(l.get("Glucose")):
        g=l["Glucose"]
        if g>=200: out.append(f"Glucose {g}: 고혈당")
        elif g<70: out.append(f"Glucose {g}: 저혈당")
        else: out.append(f"Glucose {g}: 정상")
    if entered(l.get("CRP")):
        out.append(f"CRP {l['CRP']}: {'상승 → 염증/감염' if l['CRP']>0.5 else '정상'}")
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio=l["BUN"]/l["Cr"]
        if ratio>20: out.append(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: out.append(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

def food_suggestions(l):
    out=[]
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: out.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: out.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: out.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: out.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: out.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500:
        out.append("🧼 호중구 감소: 생채소 금지, 익힌 음식만, 남은 음식 2시간 후 폐기, 껍질 과일은 주치의 상담.")
    out.append("⚠️ 철분제 복용 금지 (비타민C 병용 시 흡수↑, 반드시 주치의 상담).")
    return out

def dialysis_guides(l):
    out=[]
    if entered(l.get("K")):
        if l["K"]>5.5: out.append(f"칼륨 {l['K']}: 고칼륨혈증 위험 → 저칼륨 식이 필요")
        elif l["K"]<3.5: out.append(f"칼륨 {l['K']}: 저칼륨혈증 위험")
    if entered(l.get("P")) and l["P"]>4.5:
        out.append(f"인 {l['P']}: 고인혈증 → 인 제한 식이 필요")
    if entered(l.get("Ca")) and l["Ca"]<8.5:
        out.append(f"칼슘 {l['Ca']}: 저칼슘혈증 → 뼈대사 장애 가능성")
    if entered(l.get("Albumin")) and l["Albumin"]<3.5:
        out.append(f"알부민 {l['Albumin']}: 저알부민혈증 → 영양 부족")
    return out

def diabetes_guides(extras):
    out=[]
    fpg=to_float(extras.get("FPG"))
    if fpg:
        if fpg>=126: out.append(f"식전혈당 {fpg}: 당뇨 범위")
        elif fpg<70: out.append(f"식전혈당 {fpg}: 저혈당")
    a1c=to_float(extras.get("HbA1c"))
    if a1c and a1c>=6.5: out.append(f"HbA1c {a1c}: 당뇨 기준")
    return out

# ==================== UI 추가 입력 ====================
meds, extras = {}, {}

if category=="항암치료":
    st.markdown("### 💊 항암제 선택")
    if st.checkbox("ARA-C 사용"):
        meds["ARA-C"]={"form":st.selectbox("ARA-C 제형",["정맥(IV)","피하(SC)","고용량(HDAC)"]),
                       "dose":st.text_input("ARA-C 용량/일")}
    for k in ["6-MP","MTX","ATRA","G-CSF","Hydroxyurea","Daunorubicin","Idarubicin",
              "Mitoxantrone","Cyclophosphamide","Etoposide","Topotecan","Fludarabine","Vincristine"]:
        if st.checkbox(f"{k} 사용"): meds[k]={"dose":st.text_input(f"{k} 투여량/알약 수")}
    if st.checkbox("이뇨제 복용 중"): extras["diuretic"]=True

elif category=="항생제":
    extras["abx"]=st.multiselect("사용 중인 항생제", list(ABX_GUIDE.keys()))

elif category=="투석 환자":
    extras["urine_ml"]=st.text_input("하루 소변량 (mL)")
    extras["hd_today"]=st.checkbox("오늘 투석 시행")
    extras["delta_wt"]=st.text_input("투석 후 체중 변화 (kg)")
    if st.checkbox("이뇨제 복용 중"): extras["diuretic"]=True

elif category=="당뇨 환자":
    extras["FPG"]=st.text_input("식전 혈당 (mg/dL)")
    extras["PP1h"]=st.text_input("식후 1시간 혈당 (mg/dL)")
    extras["PP2h"]=st.text_input("식후 2시간 혈당 (mg/dL)")
    extras["HbA1c"]=st.text_input("HbA1c (%)")

# ==================== 실행 ====================
st.divider()
if st.button("🔎 해석하기", use_container_width=True):
    labs=values
    st.subheader("📋 해석 결과")
    for line in interpret_labs(labs): st.write(line)
    st.markdown("### 🥗 식이 가이드")
    for f in food_suggestions(labs): st.write("- "+f)
    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    if category=="항암치료" and meds:
        st.markdown("### 💊 항암제 요약")
        for k,v in meds.items():
            info=ANTICANCER.get(k)
            if info: st.write(f"{k}({info['alias']}): AE {', '.join(info['aes'])}, 주의 {', '.join(info['warn'])}")

    if category=="항생제" and extras.get("abx"):
        st.markdown("### 🧪 항생제 주의")
        for a in extras["abx"]: st.write(f"{a}: {', '.join(ABX_GUIDE[a])}")

    if category=="투석 환자":
        st.warning("투석 환자: 칼륨/인/수분 관리 주의. 의료진과 상의 필요.")
        for line in dialysis_guides(labs): st.write("- "+line)

    if category=="당뇨 환자":
        st.markdown("### 🍚 당뇨 해석/가이드")
        for line in diabetes_guides(extras): st.write("- "+line)
        st.write("🥗 당뇨 식이: 현미, 채소, 두부, 생선, 견과류 권장 / 단 음식·과일 주스 제한")

    ts=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    buf=[f"# BloodMap 보고서 ({ts})\n", f"- 카테고리: {category}\n"]
    for k,v in labs.items():
        if entered(v): buf.append(f"- {k}: {v}\n")
    report_md="".join(buf)
    st.download_button("📥 보고서 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
