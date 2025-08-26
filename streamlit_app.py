
# -*- coding: utf-8 -*-
# BloodMap - 암종류별 자동 피수치 패널 + 항암 프리셋 통합 (확장 항암제 + 문의 경로)
# 제작: Hoya / 자문: GPT
from datetime import datetime
import streamlit as st

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

st.set_page_config(page_title="피수치 자동 해석기 by Hoya", layout="centered")
st.title("🩸 피수치 자동 해석기")
st.markdown("👤 **제작: Hoya / 자문: GPT**")
st.caption("※ 교육·보조용. 치료 결정은 반드시 주치의와 상의하세요. 목록에 없는 약물은 마지막에 '기타 약물(문의)'에 적어주세요.")

# -------------------- 피수치 정의 --------------------
CORE_ORDER = [
    "WBC (백혈구)","Hb (혈색소)","PLT (혈소판)","ANC (절대 호중구 수)",
    "Ca (칼슘)","P (인)","Na (소디움)","K (포타슘)",
    "Albumin (알부민)","Glucose (혈당)","Total Protein (총단백)",
    "AST","ALT","LDH","CRP","Creatinine (Cr)",
    "Uric Acid (UA)","Total Bilirubin (TB)","BUN","BNP"
]
CBC_EXT = ["Reticulocyte (망상적혈구)","Hct (헤마토크릿)","MCV","MCH","MCHC","RDW"]
ALL_FIELDS = CORE_ORDER + CBC_EXT

CANCERS = ["AML","APL","ALL","CML","CLL","기타(직접 선택)"]

# 암종별 기본 패널 (요청: 기본은 CORE_ORDER, 필요 시 추가 가능)
CANCER_LAB_DEFAULTS = {c: CORE_ORDER for c in CANCERS}

# -------------------- 항암제 사전 (확장) --------------------
# 간결한 교육용 요약. 실제 처방/용량/상호작용은 반드시 주치의와 상의.
ANTICANCER = {
    # 기존
    "6-MP":{"alias":"6-머캅토퓨린","aes":["골수억제","간수치↑","구내염"],"note":"TPMT/NUDT15 변이 시 독성↑ 가능"},
    "MTX":{"alias":"메토트렉세이트","aes":["골수억제","간/신독성","구내염"],"note":"고용량 후 류코보린; NSAIDs/TMP-SMX 주의"},
    "ATRA":{"alias":"트레티노인","aes":["분화증후군","발열","피부건조"],"note":"분화증후군 의심 시 즉시 병원"},
    "ARA-C":{"alias":"시타라빈","aes":["골수억제","발열","구내염","(HDAC) 신경독성"],"note":"HDAC 시 신경증상 즉시 보고"},
    "G-CSF":{"alias":"그라신","aes":["골통/근육통","주사부위 반응"],"note":"좌상복부 통증=비장평가 고려"},
    "Hydroxyurea":{"alias":"하이드록시우레아","aes":["골수억제","피부색소","궤양"],"note":"임신 회피"},
    "Daunorubicin":{"alias":"도우노루비신","aes":["골수억제","심독성","점막염"],"note":"누적용량·심기능 추적"},
    "Idarubicin":{"alias":"이달루비신","aes":["골수억제","심독성","점막염"],"note":"심기능 모니터"},
    "Mitoxantrone":{"alias":"미토잔트론","aes":["골수억제","심독성","청록색 소변"],"note":"심기능 모니터"},
    "Cyclophosphamide":{"alias":"사이클로포스파미드","aes":["골수억제","출혈성 방광염","탈모"],"note":"수분섭취·메스나 고려"},
    "Etoposide":{"alias":"에토포사이드","aes":["골수억제","저혈압(주입)"],"note":""},
    "Topotecan":{"alias":"토포테칸","aes":["골수억제","설사"],"note":""},
    "Fludarabine":{"alias":"플루다라빈","aes":["면역억제","감염↑","혈구감소"],"note":"PCP 예방 고려"},
    "Vincristine":{"alias":"빈크리스틴","aes":["말초신경병증","변비/장폐색"],"note":"IT 금지"},

    # 새로 추가 (일반 항암/유도/구제/저강도)
    "Doxorubicin":{"alias":"독소루비신","aes":["골수억제","심독성","탈모"],"note":"누적용량 관리·심기능"},
    "Epirubicin":{"alias":"에피루비신","aes":["골수억제","심독성"],"note":"심기능"},
    "Azacitidine":{"alias":"아자시티딘","aes":["골수억제","오심","피로"],"note":"저강도 치료(AML/MDS)"},
    "Decitabine":{"alias":"데시타빈","aes":["골수억제","감염","피로"],"note":"저강도 치료(AML/MDS)"},
    "Venetoclax":{"alias":"베네토클락스","aes":["종양용해증후군","호중구감소"],"note":"강력한 상호작용 약물 확인"},

    # APL 특이 추가
    "Arsenic trioxide (ATO)":{"alias":"삼산화비소","aes":["QT 연장","분화증후군"],"note":"전해질·심전도 모니터"},

    # ALL 관련
    "Asparaginase/Pegaspargase":{"alias":"아스파라가네이스/페그","aes":["췌장염","혈전","간독성"],"note":"지질/혈당/췌장 모니터"},
    "Prednisone/Dexamethasone":{"alias":"프레드니손/덱사","aes":["혈당↑","감염↑","불면"],"note":"스테로이드(보조요법)"},

    # 표적/항체/기타 (요약·문의 권장)
    "Imatinib (TKI)":{"alias":"이매티닙","aes":["부종","근육통","오심"],"note":"CML/Ph+ ALL; 상호작용 문의"},
    "Dasatinib (TKI)":{"alias":"다사티닙","aes":["흉막/심낭삼출","혈소판감소"],"note":"CML/Ph+ ALL; 문의"},
    "Nilotinib (TKI)":{"alias":"닐로티닙","aes":["QT 연장","고혈당"],"note":"CML; 공복 복용 등 주의"},
    "Ponatinib (TKI)":{"alias":"포나티닙","aes":["혈전/동맥이상","고혈압"],"note":"CML/Ph+ ALL; 고위험 약물"},
    "Midostaurin":{"alias":"미도스타우린","aes":["오심","QT 연장"],"note":"FLT3 변이 AML; 문의"},
    "Gilteritinib":{"alias":"길터리티닙","aes":["간수치↑","QT 연장"],"note":"FLT3 변이 재발/불응 AML; 문의"},
    "Ivosidenib":{"alias":"이보시데닙","aes":["분화증후군","QT 연장"],"note":"IDH1 변이 AML; 문의"},
    "Enasidenib":{"alias":"에나시데닙","aes":["분화증후군","고빌리루빈혈증"],"note":"IDH2 변이 AML; 문의"},
    "Rituximab":{"alias":"리툭시맙","aes":["주입반응","HBV 재활성"],"note":"CD20 양성(예: CLL/림프구성); HBV 스크리닝"},
    "Obinutuzumab":{"alias":"오비누투주맙","aes":["주입반응","감염"],"note":"CD20 표적; 문의"},
    "Blinatumomab":{"alias":"블리나투모맙","aes":["CRES(신경독성)","사이토킨방출증후군"],"note":"Ph- B-ALL; 입원 모니터 필요"},
    "Inotuzumab ozogamicin":{"alias":"이노투주맙","aes":["간정맥폐쇄병","감염"],"note":"B-ALL; 전처치/간 모니터"},
    "Ibrutinib/Acalabrutinib":{"alias":"이브루티닙/아칼라브루티닙","aes":["출혈경향","AFib"],"note":"BTK 억제제(CLL); 상호작용 문의"},
    "Venetoclax+Obinutuzumab":{"alias":"베네토클락스+오비누투주맙","aes":["종양용해","감염"],"note":"CLL 1차 옵션 중 하나"},
    "CAR-T (tisagenlecleucel 등)":{"alias":"CAR-T","aes":["CRS","신경독성"],"note":"전문센터 치료"},
}

# 암종별 권장 프리셋(확장)
CANCER_REGIMENS = {
    "AML": ["ARA-C","Daunorubicin","Idarubicin","Mitoxantrone","Fludarabine","Etoposide","G-CSF","Hydroxyurea",
            "Azacitidine","Decitabine","Venetoclax","Midostaurin","Gilteritinib","Ivosidenib","Enasidenib","Doxorubicin","Epirubicin"],
    "APL": ["ATRA","Arsenic trioxide (ATO)","Daunorubicin","Idarubicin","ARA-C"],
    "ALL": ["Vincristine","Cyclophosphamide","Daunorubicin","ARA-C","MTX","6-MP","Etoposide","Topotecan",
            "Asparaginase/Pegaspargase","Prednisone/Dexamethasone","Imatinib (TKI)","Dasatinib (TKI)","Nilotinib (TKI)","Blinatumomab","Inotuzumab ozogamicin"],
    "CML": ["Hydroxyurea","Imatinib (TKI)","Dasatinib (TKI)","Nilotinib (TKI)","Ponatinib (TKI)","G-CSF"],
    "CLL": ["Fludarabine","Cyclophosphamide","Mitoxantrone","Rituximab","Obinutuzumab","Ibrutinib/Acalabrutinib",
            "Venetoclax","Venetoclax+Obinutuzumab"],
    "기타(직접 선택)": sorted(list(ANTICANCER.keys())),
}

FEVER_GUIDE = "🌡️ 38.0~38.5℃ 해열제/경과, 38.5℃↑ 병원 연락, 39.0℃↑ 즉시 병원. (ANC<500 동반 발열=응급)"
NEUTROPENIA_RULE = "🧼 호중구 감소 시: 생채소 금지, 익혀 섭취(전자레인지 30초+), 남은 음식 2시간 이후 섭취 금지, 껍질 과일은 주치의와 상의."
FOODS = {
    "Albumin_low": ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"],
    "K_low": ["바나나","감자","호박죽","고구마","오렌지"],
    "Hb_low": ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
    "Na_low": ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"],
    "Ca_low": ["연어 통조림","두부","케일","브로콜리","(참깨 제외)"],
}

def norm_key(label: str) -> str:
    if "(" in label: head = label.split("(")[0].strip()
    else: head = label.split()[0].strip()
    mapping = {"Creatinine":"Cr","Uric":"Uric Acid","Total":"Total"}  # Total Protein/Bilirubin 그대로 라벨 유지
    for k,v in mapping.items():
        if head.startswith(k): return v if v!="Total" else label
    return head

def entered(v):
    try:
        return v is not None and float(v) > 0
    except Exception:
        return False

def interpret_labs(l):
    out = []
    def add(s): out.append("- " + s)
    if entered(l.get("WBC")): add(f"WBC {l['WBC']}: " + ("낮음 → 감염 위험↑" if l["WBC"]<4 else "높음 → 감염/염증 가능" if l["WBC"]>10 else "정상"))
    if entered(l.get("Hb")): add(f"Hb {l['Hb']}: " + ("낮음 → 빈혈" if l["Hb"]<12 else "정상"))
    if entered(l.get("PLT")): add(f"혈소판 {l['PLT']}: " + ("낮음 → 출혈 위험" if l["PLT"]<150 else "정상"))
    if entered(l.get("ANC")): add(f"ANC {l['ANC']}: " + ("중증 감소(<500)" if l["ANC"]<500 else "감소(<1500)" if l["ANC"]<1500 else "정상"))
    if entered(l.get("Albumin")): add(f"Albumin {l['Albumin']}: " + ("낮음 → 영양/염증/간질환 가능" if l["Albumin"]<3.5 else "정상"))
    if entered(l.get("Glucose")): add(f"Glucose {l['Glucose']}: " + ("고혈당(≥200)" if l["Glucose"]>=200 else "저혈당(<70)" if l["Glucose"]<70 else "정상"))
    if entered(l.get("CRP")): add(f"CRP {l['CRP']}: " + ("상승 → 염증/감염 의심" if l["CRP"]>0.5 else "정상"))
    if entered(l.get("BUN")) and entered(l.get("Cr")) and l["Cr"]>0:
        ratio = l["BUN"]/l["Cr"]
        if ratio>20: add(f"BUN/Cr {ratio:.1f}: 탈수 의심")
        elif ratio<10: add(f"BUN/Cr {ratio:.1f}: 간질환/영양 고려")
    return out

def food_suggestions(l: dict):
    foods=[]
    if entered(l.get("Albumin")) and l["Albumin"]<3.5: foods.append("알부민 낮음 → " + ", ".join(FOODS["Albumin_low"]))
    if entered(l.get("K")) and l["K"]<3.5: foods.append("칼륨 낮음 → " + ", ".join(FOODS["K_low"]))
    if entered(l.get("Hb")) and l["Hb"]<12: foods.append("Hb 낮음 → " + ", ".join(FOODS["Hb_low"]))
    if entered(l.get("Na")) and l["Na"]<135: foods.append("나트륨 낮음 → " + ", ".join(FOODS["Na_low"]))
    if entered(l.get("Ca")) and l["Ca"]<8.5: foods.append("칼슘 낮음 → " + ", ".join(FOODS["Ca_low"]))
    if entered(l.get("ANC")) and l["ANC"]<500: foods.append(NEUTROPENIA_RULE)
    foods.append("⚠️ 항암/백혈병 환자는 철분제는 반드시 주치의와 상의(비타민C 병용 시 흡수↑).")
    return foods

def summarize_meds(meds: dict):
    out=[]
    for k, v in meds.items():
        info = ANTICANCER.get(k)
        if not info: 
            out.append(f"• {k}: 목록에 없는 항목입니다. **전문의와 상의해 주세요.**")
            continue
        line = f"• {k} ({info['alias']}): AE {', '.join(info['aes'])}"
        if info.get("note"): line += f" | 주의: {info['note']}"
        if k == "ARA-C" and isinstance(v, dict) and v.get("form"): line += f" | 제형: {v['form']}"
        if isinstance(v, dict) and v.get("dose_or_tabs") is not None: line += f" | 입력량: {v['dose_or_tabs']}"
        out.append(line)
    return out

# -------------------- UI --------------------
st.divider()
st.header("1️⃣ 환자 정보")
nickname = st.text_input("별명(저장/그래프용)", placeholder="예: 홍길동")
date_str = st.date_input("검사 날짜").strftime("%Y-%m-%d")

st.divider()
st.header("2️⃣ 카테고리 선택")
category = st.radio("분류", ["일반 해석","항암치료(암종류별)","항생제","투석 환자","당뇨 환자"])

meds, extras = {}, {}
selected_lab_labels = CORE_ORDER  # 기본

# -------- 암종류별: 자동 패널 + 확장 항암제 --------
if category == "항암치료(암종류별)":
    st.markdown("### 🧬 암 종류")
    cancer_type = st.selectbox("암 종류를 선택하세요", CANCERS, index=0, key="cancer_type")

    default_panel = CANCER_LAB_DEFAULTS.get(cancer_type, CORE_ORDER)
    st.markdown("### 🧪 표시할 피수치 (암종 선택 시 자동 기본값 로드)")
    selected_lab_labels = st.multiselect(
        "필요한 피수치를 선택하세요",
        options=ALL_FIELDS,
        default=default_panel,
        key=f"lab_panel_{cancer_type}",
        help="CBC 확장 항목(망상적혈구/Hct/MCV/MCH/MCHC/RDW)은 필요한 환자에서만 선택하세요."
    )

    st.markdown("### 💊 항암제 프리셋 (없으면 '기타 약물(문의)' 사용)")
    rec = CANCER_REGIMENS.get(cancer_type, CANCER_REGIMENS["기타(직접 선택)"])
    options = sorted(set(rec + list(ANTICANCER.keys())))
    picked = st.multiselect("항암제 선택", options=options, default=rec, key=f"rx_{cancer_type}")
    for key in picked:
        if key == "ARA-C":
            c1, c2 = st.columns(2)
            with c1:
                form = st.selectbox("ARA-C 제형", ["정맥(IV)","피하(SC)","고용량(HDAC)"], key=f"arac_form_{cancer_type}")
            with c2:
                dose = st.number_input("ARA-C 용량/일(선택)", min_value=0.0, step=0.1, key=f"arac_dose_{cancer_type}")
            meds[key] = {"form": form, "dose_or_tabs": dose}
        else:
            dose = st.number_input(f"{key} 투여량/알약 개수(선택)", min_value=0.0, step=0.1, key=f"dose_{key}_{cancer_type}")
            meds[key] = {"dose_or_tabs": dose}

    st.info("목록에 없다면 아래 '기타 약물(문의)'에 입력해 주세요. 약물명만 적어도 됩니다.")
    extras["other_meds"] = st.text_input("기타 약물(문의)", placeholder="예: gilteritinib 120mg qd, imatinib 400mg, ...")

    st.info("증상 가이드: " + FEVER_GUIDE)
    if st.checkbox("이뇨제 복용 중", key=f"diuret_{cancer_type}"):
        extras["diuretic"] = True

elif category == "항생제":
    extras["abx"] = st.multiselect("사용 중인 항생제 계열", ["페니실린계","세팔로스포린계","마크롤라이드","플루오로퀴놀론","카바페넴","TMP-SMX","메트로니다졸","반코마이신"])

elif category == "투석 환자":
    extras["urine_ml"] = st.number_input("하루 소변량 (mL)", min_value=0.0, step=10.0)
    extras["hd_today"] = st.checkbox("오늘 투석 시행")
    extras["post_hd_weight_delta"] = st.number_input("투석 후 체중 변화 (kg)", min_value=-10.0, max_value=10.0, step=0.1)
    if st.checkbox("이뇨제 복용 중"):
        extras["diuretic"] = True

elif category == "당뇨 환자":
    extras["FPG"] = st.number_input("식전 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP1h"] = st.number_input("식후 1시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["PP2h"] = st.number_input("식후 2시간 혈당 (mg/dL)", min_value=0.0, step=1.0)
    extras["HbA1c"] = st.number_input("HbA1c (%)", min_value=0.0, step=0.1, format="%.1f")

# -------- 선택된 피수치만 입력창 노출 --------
st.divider()
st.header("3️⃣ 혈액 검사 수치 입력 (선택 항목만 표시)")
def step_for(key): return 1.0 if key in ["ANC","Glucose","AST","ALT","LDH","BNP"] else 0.1
labs = {norm_key(label): st.number_input(label, min_value=0.0, step=step_for(norm_key(label)), key=f"lab_{norm_key(label)}") for label in selected_lab_labels}

# -------- 실행 --------
run = st.button("🔎 해석하기", use_container_width=True)
if run:
    st.subheader("📋 해석 결과")
    for line in interpret_labs(labs):
        st.write(line)

    if category == "항암치료(암종류별)":
        st.markdown("### 💊 항암제 요약")
        for line in summarize_meds(meds):
            st.write(line)
        if extras.get("other_meds"):
            st.write(f"• 기타 약물(문의): {extras['other_meds']}  → **전문의와 상의 필요**")

    if extras.get("abx"):
        st.markdown("### 🧪 항생제 주의 요약")
        for a in extras["abx"]:
            st.write(f"• {a} 계열: 일반적 주의 필요")

    fs = food_suggestions(labs)
    if fs:
        st.markdown("### 🥗 음식 가이드")
        for f in fs: st.write("- " + f)

    st.markdown("### 🌡️ 발열 가이드")
    st.write(FEVER_GUIDE)

    # 보고서
    buf = [f"# BloodMap 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n",
           f"- 날짜: {date_str}\n",
           f"- 카테고리: {category}\n\n"]
    for label in selected_lab_labels:
        key = norm_key(label); v = labs.get(key)
        if entered(v): buf.append(f"- {label}: {v}\n")
    if meds:
        buf.append("\n## 약물\n")
        for line in summarize_meds(meds): buf.append(line + "\n")
    if extras.get("other_meds"):
        buf.append(f"• 기타 약물(문의): {extras['other_meds']}\n")
    report_md = "".join(buf)
    st.download_button("📥 보고서(.md) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                       mime="text/markdown")
    st.download_button("📥 보고서(.txt) 다운로드", data=report_md.encode("utf-8"),
                       file_name=f"bloodmap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                       mime="text/plain")

    # 저장
    if nickname.strip():
        if st.checkbox("📝 이 별명으로 저장", value=True):
            rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "date": date_str,
                   "category": category,
                   "labs": {k:v for k,v in labs.items() if entered(v)},
                   "meds": meds, "extras": extras, "panel": selected_lab_labels}
            st.session_state.setdefault("records", {}).setdefault(nickname, []).append(rec)
            st.success("저장되었습니다. 아래 그래프에서 추이를 확인하세요.")
    else:
        st.info("별명을 입력하면 추이 그래프를 사용할 수 있어요.")

# -------- 그래프 --------
st.markdown("---")
st.subheader("📈 별명별 추이 그래프 (WBC, Hb, PLT, CRP, ANC)")
if not HAS_PD:
    st.info("그래프는 pandas 설치 시 활성화됩니다. (pip install pandas)")
else:
    if st.session_state.get("records"):
        sel = st.selectbox("별명 선택", sorted(st.session_state["records"].keys()))
        rows = st.session_state["records"].get(sel, [])
        if rows:
            data = []
            for r in rows:
                row = {"ts": r["ts"]}
                for k in ["WBC","Hb","PLT","CRP","ANC"]:
                    row[k] = r["labs"].get(k)
                data.append(row)
            if data:
                import pandas as pd
                df = pd.DataFrame(data).set_index("ts")
                st.line_chart(df.dropna(how="all"))
            else:
                st.info("그래프화 가능한 항목이 없습니다.")
    else:
        st.info("아직 저장된 기록이 없습니다.")

st.caption("© BloodMap | 제작: Hoya / 자문: GPT")


