
import io
import datetime
import streamlit as st

# ================= Page Config =================
st.set_page_config(page_title="피수치 자동 해석기 by Hoya (v5 통합)", layout="wide")
st.title("🔬 피수치 자동 해석기 by Hoya (v5 통합)")
st.caption("항암/투석/당뇨 모드 + 음식 가이드 + 항암제 안정화 + 보고서 다운로드")

# -------------- helpers --------------
def ss_default(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

def add_header(report_lines, nickname):
    today = datetime.date.today().isoformat()
    report_lines.append("# 피수치 자동 해석 결과")
    report_lines.append(f"- 생성일: {today}")
    if nickname:
        report_lines.append(f"- 별명: {nickname}")
    report_lines.append("")

# Defaults
ss_default("nickname", "")
ss_default("mode", "🧬 항암 환자")
MODES = ["🧬 항암 환자", "💧 투석 환자", "🍚 당뇨 환자"]

# ------------------- NAV -------------------
left, right = st.columns([1,3])
with left:
    st.markdown("### 🧭 모드 선택")
    st.session_state.mode = st.radio(
        "모드",
        options=MODES,
        index=0,
        label_visibility="collapsed",
        key="mode_radio_v5"
    )
with right:
    st.subheader("👤 기본정보")
    st.session_state.nickname = st.text_input("별명 (결과 저장용, 선택)", value=st.session_state.nickname, key="nickname_v5")

# ------------------- MODE: Oncology -------------------
if st.session_state.mode == "🧬 항암 환자":
    st.markdown("---")
    st.subheader("🩸 항암 환자 수치 입력 (20개)")

    # Define fields: (key, label, unit, step, format)
    ONCO_FIELDS_LEFT = [
        ("wbc","WBC 백혈구 (x10³/μL)",0.1,"%.2f"),
        ("hb","Hb 헤모글로빈 (g/dL)",0.1,"%.2f"),
        ("plt","PLT 혈소판 (x10³/μL)",1.0,"%.0f"),
        ("anc","ANC 호중구 (/μL)",10.0,"%.0f"),
        ("ca","Ca 칼슘 (mg/dL)",0.1,"%.2f"),
        ("p","P 인 (mg/dL)",0.1,"%.2f"),
        ("na","Na 나트륨 (mmol/L)",0.5,"%.1f"),
        ("k","K 칼륨 (mmol/L)",0.1,"%.2f"),
        ("alb","Alb 알부민 (g/dL)",0.1,"%.2f"),
        ("glu","Glu 혈당 (mg/dL)",1.0,"%.0f"),
    ]
    ONCO_FIELDS_RIGHT = [
        ("tp","TP 총단백 (g/dL)",0.1,"%.2f"),
        ("ast","AST (IU/L)",1.0,"%.0f"),
        ("alt","ALT (IU/L)",1.0,"%.0f"),
        ("ld","LDH (U/L)",1.0,"%.0f"),
        ("crp","CRP (mg/dL)",0.1,"%.2f"),
        ("cr","Cr 크레아티닌 (mg/dL)",0.1,"%.2f"),
        ("ua","UA 요산 (mg/dL)",0.1,"%.2f"),
        ("tb","T.B 총빌리루빈 (mg/dL)",0.1,"%.2f"),
        ("bun","BUN (mg/dL)",0.1,"%.2f"),
        ("bnp","BNP (pg/mL)",1.0,"%.0f"),
    ]
    c1, c2 = st.columns(2)
    for key,label,step,fmt in ONCO_FIELDS_LEFT:
        ss_default(key, 0.0)
        st.session_state[key] = st.number_input(label, min_value=0.0, step=step, format=fmt, key=f"{key}_v5")
    for key,label,step,fmt in ONCO_FIELDS_RIGHT:
        ss_default(key, 0.0)
        st.session_state[key] = st.number_input(label, min_value=0.0, step=step, format=fmt, key=f"{key}_v5")
    st.session_state.temp = st.number_input("🌡️ 체온 (°C)", min_value=0.0, step=0.1, format="%.1f", key="temp_v5")

    # -------- Drugs (stable) --------
    st.markdown("### 💊 항암제 선택/용량 (선택)")
    DRUG_SPECS = [
        {"name": "6-MP (Mercaptopurine)", "slug": "6mp", "input": "pill",   "dose_label": "6-MP 복용량 (정)"},
        {"name": "MTX (Methotrexate)",     "slug": "mtx", "input": "pill",   "dose_label": "MTX 복용량 (정)"},
        {"name": "베사노이드 (ATRA)",         "slug": "atra","input": "pill",   "dose_label": "베사노이드 복용량 (정)"},
        {"name": "Cytarabine (ARA-C) - 정맥(IV)", "slug": "arac_iv",   "input": None},
        {"name": "Cytarabine (ARA-C) - 피하(SC)", "slug": "arac_sc",   "input": None},
        {"name": "Cytarabine (ARA-C) - 고용량(HDAC)", "slug": "arac_hdac","input": None},
        {"name": "Vincristine (비크라빈)",   "slug": "vcr", "input": None},
        {"name": "Daunorubicin (도우노루비신)", "slug": "dau", "input": None},
        {"name": "Idarubicin (이달루시빈)",     "slug": "ida", "input": None},
        {"name": "Mitoxantrone (미토잔트론)",  "slug": "mtox","input": None},
        {"name": "Cyclophosphamide (사이클로포스파마이드)", "slug": "ctx", "input": None},
        {"name": "Etoposide (에토포사이드)", "slug": "etop","input": None},
        {"name": "Topotecan (토포테칸)",     "slug": "tpt", "input": None},
        {"name": "Fludarabine (플루다라빈)", "slug": "fld", "input": None},
        {"name": "Hydroxyurea (하이드록시우레아)", "slug": "hyd", "input": None},
        {"name": "G-CSF (그라신)",         "slug": "gcsf","input": "cycle", "dose_label": "G-CSF 투여 주기", "choices": ["미투여", "1회", "연속 2일", "연속 3일 이상"]},
    ]
    option_names = [d["name"] for d in DRUG_SPECS]
    NAME2SPEC = {d["name"]: d for d in DRUG_SPECS}

    ss_default("drug_selected_v5", [])
    st.session_state.drug_selected_v5 = st.multiselect(
        "현재 복용/투여 중인 항암제를 선택하세요",
        options=option_names,
        default=st.session_state.drug_selected_v5,
        key="ms_drugs_v5"
    )

    for d in DRUG_SPECS:
        if d["input"] == "pill":
            ss_default(f"dose_{d['slug']}_v5", 0.0)
        elif d["input"] == "cycle":
            ss_default(f"dose_{d['slug']}_v5", d["choices"][0])

    # Dose inputs
    for nm in sorted(st.session_state.drug_selected_v5, key=lambda x: option_names.index(x)):
        spec = NAME2SPEC[nm]; slug = spec["slug"]
        if spec["input"] == "pill":
            st.session_state[f"dose_{slug}_v5"] = st.number_input(
                spec["dose_label"], min_value=0.0, step=0.1, key=f"dose_{slug}_v5"
            )
        elif spec["input"] == "cycle":
            st.session_state[f"dose_{slug}_v5"] = st.selectbox(
                spec["dose_label"], spec["choices"], key=f"dose_{slug}_v5"
            )

    st.markdown("#### 📋 항암제 관련 요약 주의사항")
    drug_warnings = {
        "6-MP (Mercaptopurine)": "간 수치(AST/ALT) 상승 시 주의. 복통·구토 시 즉시 병원.",
        "MTX (Methotrexate)": "구내염·간수치 상승·골수억제 주의. 탈수 시 독성↑ 가능.",
        "베사노이드 (ATRA)": "피부 발진·구내염·설사 가능. 발열·호흡곤란 시 RA증후군 의심.",
        "Cytarabine (ARA-C) - 정맥(IV)": "발열·골수억제 주의. 신경학적 증상 시 병원.",
        "Cytarabine (ARA-C) - 피하(SC)": "주사부위 통증·발적 가능. 발열·출혈 시 즉시 병원.",
        "Cytarabine (ARA-C) - 고용량(HDAC)": "신경독성·시야 흐림 가능. 고열·의식저하 시 즉시 병원.",
        "Vincristine (비크라빈)": "저림·통증·변비 가능. 장폐색 의심 시 응급.",
        "Daunorubicin (도우노루비신)": "심장독성 가능. 흉통·부종 시 즉시 병원.",
        "Idarubicin (이달루시빈)": "심장독성/골수억제 주의. 고열·호흡곤란 시 즉시.",
        "Mitoxantrone (미토잔트론)": "심장독성 가능. 피부·소변 청록색 변색 흔함.",
        "Cyclophosphamide (사이클로포스파마이드)": "출혈성 방광염 주의. 수분섭취 중요.",
        "Etoposide (에토포사이드)": "저혈압/과민반응 드묾. 어지럼·호흡곤란 시 즉시.",
        "Topotecan (토포테칸)": "골수억제 심함. 발열·출혈 경향 주의.",
        "Fludarabine (플루다라빈)": "면역억제 강함. 발열·호흡기 증상 시 즉시 병원.",
        "Hydroxyurea (하이드록시우레아)": "골수억제/피부변화 가능. 상처치유 지연.",
        "G-CSF (그라신)": "뼈통증 흔함. 발열반응 드물게. 백혈구 상승 시 주치의 상의."
    }
    if not st.session_state.drug_selected_v5:
        st.caption("선택된 항암제가 없습니다.")
    else:
        for nm in sorted(st.session_state.drug_selected_v5, key=lambda x: option_names.index(x)):
            spec = NAME2SPEC[nm]; slug = spec["slug"]
            v = st.session_state.get(f"dose_{slug}_v5")
            tail = ""
            if spec["input"] == "pill" and isinstance(v, (int, float)):
                tail = f" (복용량: {v}정)"
            elif spec["input"] == "cycle" and isinstance(v, str):
                tail = f" (주기: {v})"
            st.write(f"• **{nm}**{tail} → {drug_warnings.get(nm, '주의사항을 확인하세요.')}")

# ------------------- MODE: Dialysis -------------------
elif st.session_state.mode == "💧 투석 환자":
    st.markdown("---")
    st.subheader("🩸 투석 환자 수치 입력")
    # Typical dialysis set
    D_FIELDS_LEFT = [
        ("na","Na (mmol/L)",0.5,"%.1f"),
        ("k","K (mmol/L)",0.1,"%.2f"),
        ("ca","Ca (mg/dL)",0.1,"%.2f"),
        ("p","P (mg/dL)",0.1,"%.2f"),
        ("cl","Cl (mmol/L)",0.5,"%.1f"),
        ("bun","BUN (mg/dL)",0.1,"%.2f"),
    ]
    D_FIELDS_RIGHT = [
        ("cr","Cr (mg/dL)",0.1,"%.2f"),
        ("ua","UA (mg/dL)",0.1,"%.2f"),
        ("hb","Hb (g/dL)",0.1,"%.2f"),
        ("hct","Hct 헤마토크릿 (%)",0.1,"%.1f"),
        ("alb","Alb (g/dL)",0.1,"%.2f"),
        ("tp","TP (g/dL)",0.1,"%.2f"),
    ]
    c1, c2 = st.columns(2)
    for key,label,step,fmt in D_FIELDS_LEFT:
        ss_default(key, 0.0)
        st.session_state[key] = st.number_input(label, min_value=0.0, step=step, format=fmt, key=f"{key}_dial_v5")
    for key,label,step,fmt in D_FIELDS_RIGHT:
        ss_default(key, 0.0)
        st.session_state[key] = st.number_input(label, min_value=0.0, step=step, format=fmt, key=f"{key}_dial_v5")
    ss_default("urine_ml", 0)
    ss_default("is_dialysis", True)
    st.session_state.is_dialysis = st.checkbox("투석(hemo/peritoneal) 치료 중", value=True, key="dial_ck_v5")
    st.session_state.urine_ml = st.number_input("하루 소변량 (mL/일)", min_value=0, step=10, format="%d", key="urine_ml_v5")

    st.markdown("### 🍽️ 투석 환자 음식 가이드")
    st.write("- ❌ **고칼륨**: 바나나, 오렌지, 감자, 고구마 등")
    st.write("- ❌ **고인/가공식품**: 햄, 소시지, 가공치즈, 라면스프")
    st.write("- ❌ **고염분**: 김치, 젓갈, 인스턴트")
    st.write("- ✅ **대안**: 사과·배·포도(저칼륨 과일), 흰살생선·계란흰자(단백질), 저염 조리")

# ------------------- MODE: Diabetes -------------------
elif st.session_state.mode == "🍚 당뇨 환자":
    st.markdown("---")
    st.subheader("🩸 당뇨 환자 수치 입력")
    ss_default("fbs", 0.0); ss_default("pp2", 0.0); ss_default("hba1c", 0.0)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.fbs = st.number_input("FBS 공복혈당 (mg/dL)", min_value=0.0, step=1.0, format="%.0f", key="fbs_v5")
        st.session_state.pp2 = st.number_input("PP2BS 식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0, format="%.0f", key="pp2_v5")
    with c2:
        st.session_state.hba1c = st.number_input("HbA1c 당화혈색소 (%)", min_value=0.0, step=0.1, format="%.1f", key="hba1c_v5")

    st.markdown("### 🍽️ 당뇨 환자 추천 음식")
    st.write("- 🥗 채소(시금치/브로콜리/오이), 🥜 견과류, 🐟 연어/고등어")
    st.write("- 🍠 복합탄수화물(귀리/현미/고구마) → 혈당지수 낮음")
    st.write("- 🥛 저지방 단백질: 두부, 닭가슴살")

# ------------------- INTERPRET -------------------
st.markdown("---")
st.subheader("🧾 해석 및 보고서")

if st.button("🔎 해석하기 (현재 모드 기준)", key="btn_interpret_all_v5"):
    nickname = st.session_state.nickname_v5.strip() if "nickname_v5" in st.session_state else st.session_state.nickname
    screen_lines = []; report_lines = []
    add_header(report_lines, nickname)

    mode = st.session_state.mode

    # ----- Rules per mode (simple demos) -----
    if mode == "🧬 항암 환자":
        # grab needed values
        wbc=st.session_state.wbc_v5; hb=st.session_state.hb_v5; plt=st.session_state.plt_v5; anc=st.session_state.anc_v5
        crp=st.session_state.crp_v5; alt=st.session_state.alt_v5; ast=st.session_state.ast_v5; tb=st.session_state.tb_v5
        temp=st.session_state.temp_v5
        # a few sample rules
        if wbc>0 and wbc<4: screen_lines.append(f"WBC {wbc:.2f} → 낮음 (감염 위험)"); report_lines.append("- **WBC 낮음**: 발열/오한 시 즉시 병원.")
        if hb>0 and hb<10: screen_lines.append(f"Hb {hb:.2f} g/dL → 빈혈"); report_lines.append("- **빈혈**: 피로감/창백 시 관찰.")
        if plt>0 and plt<150: screen_lines.append(f"PLT {plt:.0f} → 낮음"); report_lines.append("- **혈소판 낮음**: 멍/코피/잇몸출혈 주의.")
        if anc>0 and anc<1000: screen_lines.append(f"ANC {anc:.0f} → 중성구 감소"); report_lines.append("- **ANC < 1000**: 감염주의, 익힌 음식 권장.")
        if crp>=1.0: screen_lines.append(f"CRP {crp:.2f} mg/dL → 염증 상승"); report_lines.append("- **CRP 상승**: 감염/염증 의심.")
        if alt>=80 or ast>=80 or tb>=2.0:
            screen_lines.append("간 관련 수치 상승 (ALT/AST/T.B)")
            report_lines.append("- **간 수치 상승**: 약물성 간손상 가능.")
        if temp>=38.0: screen_lines.append(f"🌡️ 체온 {temp:.1f}°C → 발열"); report_lines.append("- **발열(≥38.0°C)**: 즉시 병원 연락/내원.")
        elif temp>=37.5: screen_lines.append(f"🌡️ 체온 {temp:.1f}°C → 미열"); report_lines.append("- **미열**: 증상 변화 시 보고")

        # drugs to report
        selected = st.session_state.drug_selected_v5
        if selected:
            option_names = [d["name"] for d in DRUG_SPECS]
            NAME2SPEC = {d["name"]: d for d in DRUG_SPECS}
            report_lines.append("\n### 💊 항암제 요약 및 주의사항")
            simple = ", ".join([n.split(" (")[0] for n in selected])
            report_lines.append(f"- **복용/투여 항목**: {simple}")
            bits = []
            for nm in selected:
                spec = NAME2SPEC[nm]; slug = spec["slug"]; v = st.session_state.get(f"dose_{slug}_v5")
                if spec["input"] == "pill" and isinstance(v, (int,float)): bits.append(f"{nm.split(' (')[0]} {v}정")
                elif spec["input"] == "cycle" and isinstance(v, str): bits.append(f"{nm.split(' (')[0]} {v}")
            if bits: report_lines.append(f"- **용량/주기**: {', '.join(bits)}")

    elif mode == "💧 투석 환자":
        na=st.session_state.na_dial_v5; k=st.session_state.k_dial_v5; p=st.session_state.p_dial_v5
        bun=st.session_state.bun_dial_v5; cr=st.session_state.cr_dial_v5; alb=st.session_state.alb_dial_v5
        urine=st.session_state.urine_ml_v5
        if k>5.5: screen_lines.append(f"K {k:.2f} mmol/L → 고칼륨혈증 주의"); report_lines.append("- **칼륨 높음**: 심전도 이상 위험, 고칼륨 음식 제한.")
        if p>5.5: report_lines.append("- **인 높음**: 인결합제/식이 조절 고려.")
        if bun>80 or cr>8: report_lines.append("- **요독증 지표 상승 가능**: 증상 확인 필요.")
        if alb<3.5: report_lines.append("- **저알부민혈증**: 영양 상태 점검.")
        report_lines.append("\n### 🚰 투석/소변")
        if st.session_state.dial_ck_v5:
            if urine==0: screen_lines.append("투석 중 + 소변량 0 mL → 무뇨 가능"); report_lines.append("- 소변량: **0 mL/일** (무뇨 가능)")
            elif urine<200: report_lines.append(f"- 소변량: **{urine} mL/일** (적음)")
            else: report_lines.append(f"- 소변량: **{urine} mL/일**")
        else:
            report_lines.append("- 비투석")

        # Add food guide to report
        report_lines.append("\n### 🍽️ 투석 환자 음식 가이드")
        report_lines.append("- ❌ 고칼륨: 바나나/오렌지/감자/고구마")
        report_lines.append("- ❌ 고인·가공품: 햄/소시지/가공치즈/라면스프")
        report_lines.append("- ❌ 고염분: 김치/젓갈/인스턴트")
        report_lines.append("- ✅ 대안: 사과·배·포도, 흰살생선·계란흰자, 저염 조리")

    elif mode == "🍚 당뇨 환자":
        fbs=st.session_state.fbs_v5; pp2=st.session_state.pp2_v5; a1c=st.session_state.hba1c_v5
        if fbs>0 and fbs>=126: screen_lines.append(f"FBS {fbs:.0f} mg/dL → 공복 고혈당"); report_lines.append("- **공복 고혈당**: 내분비 상담 고려.")
        if pp2>0 and pp2>=200: screen_lines.append(f"PP2BS {pp2:.0f} mg/dL → 식후 고혈당"); report_lines.append("- **식후 고혈당**: 식사·운동·약물 조정 필요.")
        if a1c>0 and a1c>=6.5: report_lines.append("- **HbA1c ≥ 6.5%**: 당뇨 진단 기준 이상.")
        report_lines.append("\n### 🍽️ 당뇨 환자 추천 음식")
        report_lines.append("- 채소, 견과류, 연어/고등어, 귀리/현미/고구마, 두부/닭가슴살")

    # -------- Output --------
    st.markdown("#### 📌 요약 결과")
    if screen_lines:
        for line in screen_lines:
            st.write("• " + line)
    else:
        st.info("표시할 요약이 없습니다.")

    md_text = "\n".join(report_lines)
    if nickname:
        with open(f"{nickname}_results.md", "a", encoding="utf-8") as f:
            f.write(md_text); f.write("\n\n---\n\n")
        st.success(f"'{nickname}_results.md'에 결과가 저장되었습니다.")
    st.download_button(
        "📥 이번 결과 .md 다운로드",
        data=io.BytesIO(md_text.encode("utf-8")),
        file_name=f"{nickname or 'result'}_{datetime.date.today().isoformat()}.md",
        mime="text/markdown",
        key="dl_btn_md_v5"
    )
