
import io
import datetime
import streamlit as st

# ============== Page Config ==============
st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🔬 피수치 자동 해석기 by Hoya (통합본)")

# ============== Inputs: User meta ==============
nickname = st.text_input("별명 (결과 저장용, 선택)", placeholder="예: hoya")

# ============== Helper: header for report ==============
def write_header(report_lines):
    today = datetime.date.today().isoformat()
    report_lines.append(f"# 피수치 자동 해석 결과")
    report_lines.append(f"- 생성일: {today}")
    if nickname:
        report_lines.append(f"- 별명: {nickname}")
    report_lines.append("")

# ============== Inputs: Labs ==============
st.subheader("🩸 혈액 수치 입력")

col1, col2 = st.columns(2)
with col1:
    wbc = st.number_input("WBC 백혈구 (x10³/μL)", min_value=0.0, step=0.1, format="%.2f")
    hb = st.number_input("Hb 헤모글로빈 (g/dL)", min_value=0.0, step=0.1, format="%.2f")
    plt = st.number_input("PLT 혈소판 (x10³/μL)", min_value=0.0, step=1.0, format="%.0f")
    anc = st.number_input("ANC 호중구 (면역력, /μL)", min_value=0.0, step=10.0, format="%.0f")
with col2:
    crp = st.number_input("CRP 염증수치 (mg/dL)", min_value=0.0, step=0.1, format="%.2f")
    alt = st.number_input("ALT (간 수치, IU/L)", min_value=0.0, step=1.0, format="%.0f")
    ast = st.number_input("AST (간 수치, IU/L)", min_value=0.0, step=1.0, format="%.0f")
    tb  = st.number_input("T.B (총빌리루빈, mg/dL)", min_value=0.0, step=0.1, format="%.2f")

temp = st.number_input("🌡️ 체온 (°C)", min_value=0.0, step=0.1, format="%.1f")

# ============== Dialysis / Urine Output ==============
st.markdown("---")
st.subheader("🚰 투석/소변량")
is_dialysis = st.checkbox("투석(hemodialysis/peritoneal) 치료 중이에요", key="dialysis_ck")
urine_ml = st.number_input("하루 소변량 (mL/일)", min_value=0, step=10, format="%d", help="투석 환자도 소변이 조금 나오는 경우가 있어요. 모르면 0으로 둘 수 있어요.")

st.markdown("---")

# ============== Drugs: selection UI (Stabilized) ==============
st.subheader("💊 항암제 복용/투여 입력 (선택)")

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

selected_names = st.multiselect(
    "현재 복용/투여 중인 항암제를 선택하세요",
    options=option_names,
    key="ms_drugs"
)

NAME2SPEC = {d["name"]: d for d in DRUG_SPECS}

# Doses input with stable keys and consistent order
doses = {}
for nm in sorted(selected_names, key=lambda x: option_names.index(x)):
    spec = NAME2SPEC[nm]
    if spec["input"] == "pill":
        doses[spec["slug"]] = st.number_input(
            spec["dose_label"], min_value=0.0, step=0.1, key=f"dose_{spec['slug']}"
        )
    elif spec["input"] == "cycle":
        doses[spec["slug"]] = st.selectbox(
            spec["dose_label"], spec["choices"], key=f"dose_{spec['slug']}"
        )

# Warnings on screen
st.subheader("📋 항암제 관련 요약 주의사항")
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
if not selected_names:
    st.caption("선택된 항암제가 없습니다.")
else:
    for nm in sorted(selected_names, key=lambda x: option_names.index(x)):
        spec = NAME2SPEC[nm]
        slug = spec["slug"]
        tail = ""
        if slug in doses:
            if spec["input"] == "pill":
                tail = f" (복용량: {doses[slug]}정)"
            elif spec["input"] == "cycle":
                tail = f" (주기: {doses[slug]})"
        st.write(f"• **{nm}**{tail} → {drug_warnings.get(nm, '주의사항을 확인하세요.')}")

st.markdown("---")

# ============== Action: Interpret ==============
if st.button("🔎 해석하기"):
    today = datetime.date.today().isoformat()
    screen_lines = []
    report_lines = []
    write_header(report_lines)

    # ---- Lab interpretations (simple rules) ----
    if wbc > 0:
        if wbc < 4:
            screen_lines.append(f"WBC {wbc:.2f} → 낮음 (감염 위험)")
            report_lines.append(f"- **WBC 낮음**: 감염 위험. 발열/오한 시 즉시 병원.")
        elif wbc > 11:
            screen_lines.append(f"WBC {wbc:.2f} → 높음")
            report_lines.append(f"- **WBC 높음**: 감염/염증 가능. 임상 증상과 함께 해석.")
    if hb > 0:
        if hb < 8:
            screen_lines.append(f"Hb {hb:.2f} g/dL → 심한 빈혈")
            report_lines.append(f"- **빈혈 심함(Hb < 8)**: 어지럼/호흡곤란 시 보고.")
        elif hb < 10:
            screen_lines.append(f"Hb {hb:.2f} g/dL → 빈혈")
            report_lines.append(f"- **빈혈**: 피로감/창백 시 관찰.")
    if plt > 0:
        if plt < 50:
            screen_lines.append(f"PLT {plt:.0f} → 매우 낮음 (출혈 위험↑)")
            report_lines.append(f"- **혈소판 낮음(PLT < 50)**: 멍/코피/잇몸출혈 주의.")
        elif plt < 150:
            screen_lines.append(f"PLT {plt:.0f} → 낮음")
            report_lines.append(f"- **혈소판 낮음**: 출혈 증상 관찰.")
    if anc > 0:
        if anc < 500:
            screen_lines.append(f"ANC {anc:.0f} → 심한 중성구 감소 (면역저하)")
            report_lines.append(f"- **ANC < 500**: 외출/생식식품 금지, 발열 시 즉시 병원.")
        elif anc < 1000:
            screen_lines.append(f"ANC {anc:.0f} → 중성구 감소")
            report_lines.append(f"- **ANC < 1000**: 감염주의, 익힌 음식 권장.")
    if crp > 0:
        if crp >= 1.0:
            screen_lines.append(f"CRP {crp:.2f} mg/dL → 염증 상승")
            report_lines.append(f"- **CRP 상승**: 감염/염증 의심. 발열·오한 시 보고.")
    if alt > 0 or ast > 0 or tb > 0:
        if alt >= 80 or ast >= 80 or tb >= 2.0:
            screen_lines.append(f"간 관련 수치 상승 (ALT/AST/T.B)")
            report_lines.append(f"- **간 수치 상승**: 약물성 간손상 가능. 복통·구토/황달 시 병원.")
    if temp > 0:
        if temp >= 38.0:
            screen_lines.append(f"🌡️ 체온 {temp:.1f}°C → 발열")
            report_lines.append(f"- **발열(≥38.0°C)**: 즉시 병원 연락/내원.")
        elif temp >= 37.5:
            screen_lines.append(f"🌡️ 체온 {temp:.1f}°C → 미열")
            report_lines.append(f"- **미열**: 증상 변화 시 보고")

    # ---- Dialysis & Urine output interpretation ----
    report_lines.append("\n### 🚰 투석/소변")
    if is_dialysis:
        report_lines.append("- **투석 중**")
        if urine_ml == 0:
            screen_lines.append("투석 중 + 소변량 0 mL → 무뇨 가능, 체액 관리 주의")
            report_lines.append("- 소변량: **0 mL/일** (무뇨 가능) → 체액·체중 변화 관찰")
        elif urine_ml < 200:
            screen_lines.append(f"투석 중 + 소변량 {urine_ml} mL/일 → 거의 소변 없음(▶ 체액 관리 주의)")
            report_lines.append(f"- 소변량: **{urine_ml} mL/일** (적음) → 체액·부종 관찰")
        else:
            report_lines.append(f"- 소변량: **{urine_ml} mL/일**")
    else:
        report_lines.append("- **비투석**")
        report_lines.append(f"- 소변량: **{urine_ml} mL/일**")

    # ---- Drugs report helper ----
    def append_drug_report(report_lines, selected_names, doses):
        NAME2SPEC = {d["name"]: d for d in DRUG_SPECS}
        report_detail = {
            "6-MP (Mercaptopurine)": "- 간독성/골수억제/췌장염 가능. AST/ALT, WBC/PLT 추적 필요.",
            "MTX (Methotrexate)": "- 구내염/간수치 상승/골수억제. 탈수 시 독성↑. 약물상호작용 주의.",
            "베사노이드 (ATRA)": "- 피부 발진/구내염/설사. RA증후군(발열·호흡곤란·체중증가) 가능.",
            "Cytarabine (ARA-C) - 정맥(IV)": "- 발열/골수억제. 복시·시야 흐림 등 신경학 증상 주의.",
            "Cytarabine (ARA-C) - 피하(SC)": "- 주사부위 반응. 발열·출혈 시 즉시 병원.",
            "Cytarabine (ARA-C) - 고용량(HDAC)": "- 신경독성·시야 이상 가능. 신경계 모니터링 필수.",
            "Vincristine (비크라빈)": "- 말초신경병증/변비. 장폐색 의심 증상 교육.",
            "Daunorubicin (도우노루비신)": "- 심독성(누적용량). 흉통·호흡곤란 시 즉시.",
            "Idarubicin (이달루시빈)": "- 심독성/골수억제. 고열 시 패혈증 의심.",
            "Mitoxantrone (미토잔트론)": "- 심독성. 체액·피부 청록색 변색 가능.",
            "Cyclophosphamide (사이클로포스파마이드)": "- 출혈성 방광염 예방 위해 수분섭취/배뇨 모니터.",
            "Etoposide (에토포사이드)": "- 저혈압/과민반응 드묾. 투여 중 모니터링.",
            "Topotecan (토포테칸)": "- 강한 골수억제. 발열·출혈 위험.",
            "Fludarabine (플루다라빈)": "- 면역억제 강함. 기회감염 주의.",
            "Hydroxyurea (하이드록시우레아)": "- 골수억제/피부변화. 상처치유 지연.",
            "G-CSF (그라신)": "- 뼈통증 흔함. 고열·호흡곤란 등 이상 시 보고."
        }

        if selected_names:
            report_lines.append("\n### 💊 항암제 요약 및 주의사항")
            simple = ", ".join([n.split(" (")[0] for n in selected_names])
            report_lines.append(f"- **복용/투여 항목**: {simple}")
            bits = []
            for nm in selected_names:
                spec = NAME2SPEC[nm]
                slug = spec["slug"]
                if slug in doses:
                    if spec["input"] == "pill":
                        bits.append(f"{nm.split(' (')[0]} {doses[slug]}정")
                    elif spec["input"] == "cycle":
                        bits.append(f"{nm.split(' (')[0]} {doses[slug]}")
            if bits:
                report_lines.append(f"- **용량/주기**: {', '.join(bits)}")
            for nm in selected_names:
                if nm in report_detail:
                    report_lines.append(f"- **{nm}**: {report_detail[nm]}")

    # Add drug section to report
    append_drug_report(report_lines, selected_names, doses)

    # ---- Cross rule example ----
    if ("6-MP (Mercaptopurine)" in selected_names) and (alt >= 80 or ast >= 80 or tb >= 2.0):
        screen_lines.append("6-MP 복용 + 간 수치 상승 → 간독성 주의 (주치의 상담)")
        report_lines.append("- **교차 경고**: 6-MP 복용 + 간 수치 상승 → 간독성 의심, 주치의와 상의.")

    # ============= Output summary =============
    st.subheader("📌 요약 결과")
    if screen_lines:
        for line in screen_lines:
            st.write("• " + line)
    else:
        st.info("표시할 요약이 없습니다.")

    # ============= Save & Download =============
    md_text = "\n".join(report_lines)
    if nickname:
        with open(f"{nickname}_results.md", "a", encoding="utf-8") as f:
            f.write(md_text)
            f.write("\n\n---\n\n")
        st.success(f"'{nickname}_results.md'에 결과가 저장되었습니다.")

    st.download_button(
        "📥 이번 결과 .md 다운로드",
        data=io.BytesIO(md_text.encode("utf-8")),
        file_name=f"{nickname or 'result'}_{datetime.date.today().isoformat()}.md",
        mime="text/markdown"
    )
